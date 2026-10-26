import hashlib
import json
import secrets
from datetime import date, datetime, timedelta, timezone
from functools import wraps

import bcrypt
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from jose import jwt, JWTError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed

from .models import User, RefreshToken, Supplement, Source
from logic import doses_per_day_from_frequency, days_remaining, restock_date, status_for

ACCESS_MINUTES = 15
REFRESH_DAYS = 30
UNITS = {"day", "week", "month", "year"}

def limited(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        key = "auth-rate:" + (request.META.get("REMOTE_ADDR") or "unknown")
        count = cache.get(key, 0)
        if count >= 5:
            return JsonResponse({"detail": "Request was throttled. Expected available in 1 minute."}, status=429)
        cache.set(key, count + 1, 60)
        return view(request, *args, **kwargs)
    return wrapped

def body(request):
    try:
        return json.loads(request.body or b"{}")
    except (ValueError, UnicodeDecodeError):
        raise ValueError("Invalid JSON")

def error(message, status=400):
    return JsonResponse({"detail": message}, status=status)

def user_out(user):
    return {"id": user.id, "email": user.email, "notifications_enabled": user.notifications_enabled,
            "created_at": user.created_at.isoformat()}

def issue_tokens(user):
    access = jwt.encode({"sub": user.email, "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_MINUTES)}, settings.SECRET_KEY, algorithm="HS256")
    raw = secrets.token_urlsafe(48)
    RefreshToken.objects.create(user=user, token_hash=hashlib.sha256(raw.encode()).hexdigest(),
                                expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_DAYS))
    return {"access_token": access, "refresh_token": raw, "token_type": "bearer"}

def valid_refresh(raw):
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return RefreshToken.objects.filter(token_hash=digest, revoked=False, expires_at__gt=datetime.now(timezone.utc)).first()

def supplement_out(s):
    d = doses_per_day_from_frequency(s.dose_amount, s.frequency_count, s.frequency_unit)
    left = days_remaining(s.start_date, s.total_doses, d)
    return {"id": s.id, "name": s.name, "start_date": s.start_date.isoformat(), "total_doses": s.total_doses,
        "dose_amount": s.dose_amount, "frequency_count": s.frequency_count, "frequency_unit": s.frequency_unit,
        "notes": s.notes, "days_remaining": left, "restock_date": restock_date(s.start_date, s.total_doses, d).isoformat(),
        "status": status_for(left), "sources": [{"id": x.id, "name": x.name, "url": x.url} for x in s.sources.order_by("id")]}

def get_owned(supplement_id, user):
    return Supplement.objects.filter(id=supplement_id, user=user).first()

def validate_supplement(data, partial=False):
    fields = {"name", "start_date", "total_doses", "dose_amount", "frequency_count", "frequency_unit", "notes"}
    if not isinstance(data, dict):
        raise ValueError("Expected an object")
    result = {}
    for key, value in data.items():
        if key not in fields:
            continue
        if key == "name":
            if not isinstance(value, str) or not value.strip() or len(value) > 100: raise ValueError("name must be 1–100 characters")
            value = value.strip()
        elif key == "start_date":
            try: value = date.fromisoformat(value)
            except (TypeError, ValueError): raise ValueError("start_date must be YYYY-MM-DD")
        elif key in ("total_doses", "dose_amount", "frequency_count"):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0: raise ValueError(f"{key} must be greater than 0")
            if key == "total_doses" and int(value) != value: raise ValueError("total_doses must be an integer")
        elif key == "frequency_unit" and value not in UNITS: raise ValueError("Invalid frequency_unit")
        elif key == "notes" and value is not None and not isinstance(value, str): raise ValueError("notes must be a string or null")
        result[key] = int(value) if key == "total_doses" else value
    if not partial:
        required = {"name", "start_date", "total_doses"}
        missing = required - result.keys()
        if missing: raise ValueError(f"Missing required fields: {', '.join(sorted(missing))}")
        result.setdefault("dose_amount", 1.0); result.setdefault("frequency_count", 1.0); result.setdefault("frequency_unit", "day"); result.setdefault("notes", None)
    if "start_date" in result and isinstance(result["start_date"], date): result["start_date"] = result["start_date"]
    return result

def csrf_exempt_api(fn):
    return csrf_exempt(api_view(["GET", "POST", "PUT", "PATCH", "DELETE"])(fn))

@csrf_exempt_api
@permission_classes([AllowAny])
@limited
def register(request):
    if request.method != "POST": return error("Method not allowed", 405)
    try:
        data = body(request); email = data.get("email", "").strip().lower(); password = data.get("password", "")
        if "@" not in email or len(email) > 254: raise ValueError("A valid email is required")
        if not isinstance(password, str) or not 8 <= len(password) <= 72: raise ValueError("Password must be 8–72 characters")
    except (ValueError, AttributeError) as exc: return error(str(exc))
    if User.objects.filter(email=email).exists(): return error("Email is already registered")
    user = User.objects.create(email=email, hashed_password=bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode())
    return JsonResponse(user_out(user), status=201)

@csrf_exempt_api
@permission_classes([AllowAny])
@limited
def login(request):
    if request.method != "POST": return error("Method not allowed", 405)
    try: data = body(request)
    except ValueError: data = {}
    if request.content_type == "application/x-www-form-urlencoded": data = request.POST
    email = data.get("username", data.get("email", "")).strip().lower(); password = data.get("password", "")
    user = User.objects.filter(email=email).first()
    if not user or not bcrypt.checkpw(password.encode()[:72], user.hashed_password.encode()): return error("Incorrect email or password", 401)
    return JsonResponse(issue_tokens(user))

@csrf_exempt_api
@permission_classes([AllowAny])
def refresh(request):
    try: token = valid_refresh(body(request).get("refresh_token", ""))
    except (ValueError, AttributeError): token = None
    if not token: return error("Invalid or expired refresh token", 401)
    token.revoked = True; token.save(update_fields=["revoked"])
    return JsonResponse(issue_tokens(token.user))

@csrf_exempt_api
@permission_classes([AllowAny])
def logout(request):
    try: token = valid_refresh(body(request).get("refresh_token", ""))
    except (ValueError, AttributeError): token = None
    if token: token.revoked = True; token.save(update_fields=["revoked"])
    return HttpResponse(status=204)

@csrf_exempt_api
@permission_classes([IsAuthenticated])
def me(request): return JsonResponse(user_out(request.user))

@csrf_exempt_api
@permission_classes([IsAuthenticated])
def notification_settings(request):
    try: value = body(request).get("notifications_enabled")
    except ValueError: return error("Invalid JSON")
    if not isinstance(value, bool): return error("notifications_enabled must be a boolean")
    request.user.notifications_enabled = value; request.user.save(update_fields=["notifications_enabled"])
    return JsonResponse(user_out(request.user))

@csrf_exempt_api
@permission_classes([AllowAny])
def notifications_run(request):
    if not settings.NOTIFICATIONS_SECRET or request.headers.get("X-Notifications-Secret") != settings.NOTIFICATIONS_SECRET: return error("Invalid or missing notifications secret", 401)
    sent = 0
    for user in User.objects.filter(notifications_enabled=True).prefetch_related("supplements"):
        low = []
        for s in user.supplements.all():
            left = days_remaining(s.start_date, s.total_doses, doses_per_day_from_frequency(s.dose_amount, s.frequency_count, s.frequency_unit))
            if status_for(left) != "ok": low.append((s.name, left))
        if low:
            lines = ["Here's what's running low:\n"] + [
                f"- {name} ({abs(days)} days overdue)" if days < 0 else f"- {name} ({days} days left)"
                for name, days in sorted(low, key=lambda i: i[1])
            ]
            lines.append("\n— Supplement Restock Tracker")
            if settings.EMAIL_HOST: send_mail(f"Supplement Tracker: {len(low)} item(s) need restocking", "\n".join(lines), settings.DEFAULT_FROM_EMAIL, [user.email])
            else: print(f"[email:console-fallback] To: {user.email}\n" + "\n".join(lines))
            sent += 1
    return JsonResponse({"emails_sent": sent})

@csrf_exempt_api
@permission_classes([IsAuthenticated])
def supplements(request):
    if request.method == "GET": return JsonResponse([supplement_out(s) for s in Supplement.objects.filter(user=request.user).prefetch_related("sources")], safe=False)
    if request.method != "POST": return error("Method not allowed", 405)
    try:
        data = body(request); sources = data.pop("sources", []); values = validate_supplement(data)
        if not isinstance(sources, list): raise ValueError("sources must be a list")
        s = Supplement.objects.create(user=request.user, **values)
        for item in sources:
            if not isinstance(item, dict) or not item.get("name"): raise ValueError("Each source requires a name")
            Source.objects.create(supplement=s, name=item["name"], url=item.get("url") or None)
    except (ValueError, TypeError) as exc: return error(str(exc))
    return JsonResponse(supplement_out(s), status=201)

@csrf_exempt_api
@permission_classes([IsAuthenticated])
def supplement_detail(request, supplement_id):
    s = get_owned(supplement_id, request.user)
    if not s: return error(f"Supplement {supplement_id} not found", 404)
    if request.method == "GET": return JsonResponse(supplement_out(s))
    if request.method == "DELETE": s.delete(); return HttpResponse(status=204)
    if request.method not in ("PUT", "PATCH"): return error("Method not allowed", 405)
    try: values = validate_supplement(body(request), partial=True)
    except ValueError as exc: return error(str(exc))
    for key, value in values.items(): setattr(s, key, value)
    s.save(); return JsonResponse(supplement_out(s))

@csrf_exempt_api
@permission_classes([IsAuthenticated])
def restock(request, supplement_id):
    s = get_owned(supplement_id, request.user)
    if not s: return error(f"Supplement {supplement_id} not found", 404)
    s.start_date = date.today()
    total = request.GET.get("new_total_doses")
    if total:
        try: s.total_doses = int(total); assert s.total_doses > 0
        except (ValueError, AssertionError): return error("new_total_doses must be greater than 0")
    s.save(); return JsonResponse(supplement_out(s))

@csrf_exempt_api
@permission_classes([IsAuthenticated])
def add_source(request, supplement_id):
    s = get_owned(supplement_id, request.user)
    if not s: return error(f"Supplement {supplement_id} not found", 404)
    try: data = body(request); name = data.get("name", "").strip(); url = data.get("url") or None
    except (ValueError, AttributeError): return error("Invalid source")
    if not name or len(name) > 100: return error("name must be 1–100 characters")
    Source.objects.create(supplement=s, name=name, url=url)
    return JsonResponse(supplement_out(s), status=201)

@csrf_exempt_api
@permission_classes([IsAuthenticated])
def delete_source(request, source_id):
    source = Source.objects.filter(id=source_id, supplement__user=request.user).first()
    if not source: return error(f"Source {source_id} not found", 404)
    source.delete(); return HttpResponse(status=204)
