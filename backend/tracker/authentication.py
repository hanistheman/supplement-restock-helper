from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from jose import JWTError, jwt
from .models import User

class BearerAuthentication(BaseAuthentication):
    def authenticate_header(self, request):
        return "Bearer"

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts:
            return None
        if len(parts) != 2 or parts[0].lower() != b"bearer":
            raise AuthenticationFailed("Invalid authorization header")
        try:
            email = jwt.decode(parts[1].decode(), settings.SECRET_KEY, algorithms=["HS256"]).get("sub")
            user = User.objects.get(email=email)
        except (JWTError, User.DoesNotExist, AttributeError):
            raise AuthenticationFailed("Could not validate credentials")
        return (user, None)
