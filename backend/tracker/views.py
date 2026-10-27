import hashlib
import secrets
from datetime import date, datetime, timedelta, timezone

import bcrypt
from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView
from jose import jwt

from .models import RefreshToken, SkippedDay, Source, Supplement, User
from .serializers import RegisterSerializer, SkippedDaySerializer, SourceSerializer, SupplementSerializer, UserSerializer
from .services import run_low_stock_check


class AuthThrottle(SimpleRateThrottle):
    scope = "auth"

    def get_cache_key(self, request, view):
        return self.get_rate() and self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


def issue_tokens(user):
    access = jwt.encode(
        {"sub": user.email, "exp": datetime.now(timezone.utc) + timedelta(minutes=15)},
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    refresh = secrets.token_urlsafe(48)
    RefreshToken.objects.create(
        user=user,
        token_hash=hashlib.sha256(refresh.encode()).hexdigest(),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


def valid_refresh(raw):
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return RefreshToken.objects.filter(token_hash=digest, revoked=False, expires_at__gt=datetime.now(timezone.utc)).first()


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AuthThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()
        if User.objects.filter(email=email).exists():
            return Response({"detail": "Email is already registered"}, status=status.HTTP_400_BAD_REQUEST)
        password = serializer.validated_data["password"]
        user = User.objects.create(email=email, hashed_password=bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt()).decode())
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AuthThrottle]

    def post(self, request):
        email = request.data.get("username", request.data.get("email", ""))
        password = request.data.get("password", "")
        if not isinstance(email, str) or not isinstance(password, str):
            return Response({"detail": "Incorrect email or password"}, status=status.HTTP_401_UNAUTHORIZED)
        user = User.objects.filter(email=email.strip().lower()).first()
        if not user or not bcrypt.checkpw(password.encode()[:72], user.hashed_password.encode()):
            return Response({"detail": "Incorrect email or password"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(issue_tokens(user))


class RefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        raw = request.data.get("refresh_token", "")
        token = valid_refresh(raw) if isinstance(raw, str) else None
        if token is None:
            return Response({"detail": "Invalid or expired refresh token"}, status=status.HTTP_401_UNAUTHORIZED)
        token.revoked = True
        token.save(update_fields=["revoked"])
        return Response(issue_tokens(token.user))


class LogoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        raw = request.data.get("refresh_token", "")
        token = valid_refresh(raw) if isinstance(raw, str) else None
        if token:
            token.revoked = True
            token.save(update_fields=["revoked"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class NotificationSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        value = request.data.get("notifications_enabled")
        if not isinstance(value, bool):
            return Response({"detail": "notifications_enabled must be a boolean"}, status=status.HTTP_400_BAD_REQUEST)
        request.user.notifications_enabled = value
        request.user.save(update_fields=["notifications_enabled"])
        return Response(UserSerializer(request.user).data)


class NotificationsRunView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        if not settings.NOTIFICATIONS_SECRET or request.headers.get("X-Notifications-Secret") != settings.NOTIFICATIONS_SECRET:
            return Response({"detail": "Invalid or missing notifications secret"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({"emails_sent": run_low_stock_check()})


class SupplementListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        supplements = Supplement.objects.filter(user=request.user).prefetch_related("sources", "skipped_days")
        return Response(SupplementSerializer(supplements, many=True, context={"request": request}).data)

    def post(self, request):
        serializer = SupplementSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        supplement = serializer.save()
        return Response(SupplementSerializer(supplement, context={"request": request}).data, status=status.HTTP_201_CREATED)


def owned_supplement_or_404(supplement_id, user):
    try:
        return Supplement.objects.prefetch_related("sources", "skipped_days").get(id=supplement_id, user=user)
    except Supplement.DoesNotExist:
        raise NotFound(f"Supplement {supplement_id} not found")


class SupplementDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, supplement_id):
        supplement = owned_supplement_or_404(supplement_id, request.user)
        return Response(SupplementSerializer(supplement, context={"request": request}).data)

    def put(self, request, supplement_id):
        return self._update(request, supplement_id)

    def patch(self, request, supplement_id):
        return self._update(request, supplement_id, partial=True)

    def _update(self, request, supplement_id, partial=False):
        supplement = owned_supplement_or_404(supplement_id, request.user)
        serializer = SupplementSerializer(supplement, data=request.data, partial=partial, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(SupplementSerializer(supplement, context={"request": request}).data)

    def delete(self, request, supplement_id):
        owned_supplement_or_404(supplement_id, request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RestockView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, supplement_id):
        supplement = owned_supplement_or_404(supplement_id, request.user)
        raw_total = request.query_params.get("new_total_doses")
        if raw_total is not None:
            try:
                total = int(raw_total)
                if total <= 0: raise ValueError
            except ValueError:
                return Response({"detail": "new_total_doses must be greater than 0"}, status=status.HTTP_400_BAD_REQUEST)
            supplement.total_doses = total
        supplement.start_date = date.today()
        supplement.skipped_days.all().delete()
        supplement.save()
        return Response(SupplementSerializer(supplement, context={"request": request}).data)


class SourceListView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, supplement_id):
        supplement = owned_supplement_or_404(supplement_id, request.user)
        serializer = SourceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(supplement=supplement)
        supplement = owned_supplement_or_404(supplement_id, request.user)
        return Response(SupplementSerializer(supplement, context={"request": request}).data, status=status.HTTP_201_CREATED)


class SourceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, source_id):
        source = Source.objects.filter(id=source_id, supplement__user=request.user).first()
        if source is None:
            raise NotFound(f"Source {source_id} not found")
        source.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SkippedDayListView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, supplement_id):
        supplement = owned_supplement_or_404(supplement_id, request.user)
        serializer = SkippedDaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        skipped_date = serializer.validated_data["date"]
        if skipped_date < supplement.start_date or skipped_date > date.today():
            raise ValidationError({"date": "Skipped date must be between the supplement start date and today"})
        try:
            with transaction.atomic():
                serializer.save(supplement=supplement)
        except IntegrityError:
            return Response({"detail": "A skipped day is already recorded for this date"}, status=status.HTTP_409_CONFLICT)
        supplement = owned_supplement_or_404(supplement_id, request.user)
        return Response(SupplementSerializer(supplement, context={"request": request}).data, status=status.HTTP_201_CREATED)


class SkippedDayDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, supplement_id, skipped_day_id):
        supplement = owned_supplement_or_404(supplement_id, request.user)
        skipped = supplement.skipped_days.filter(id=skipped_day_id).first()
        if skipped is None:
            raise NotFound(f"Skipped day {skipped_day_id} not found")
        skipped.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
