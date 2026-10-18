"""
Auth utilities: password hashing (bcrypt), JWT creation/verification, and
the get_current_user dependency that protected routes use to identify
"who is making this request".
"""
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

import models
from database import get_db

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is not set. Add it to your .env file — this signs auth "
        "tokens, so it must be a long random value kept out of source control."
    )

ALGORITHM = "HS256"
# Short-lived on purpose: this is the token sent on every request, so a
# stolen one is only useful for a brief window. Staying logged in beyond
# this relies on the refresh token below, not a long-lived access token.
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Tells FastAPI (and the /docs UI) where clients should send credentials to
# get a token. tokenUrl is relative to the API root.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def hash_password(password: str) -> str:
    # bcrypt has a hard 72-byte input limit; truncate defensively so unusually
    # long passwords fail loudly elsewhere rather than silently misbehaving here.
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def generate_refresh_token() -> str:
    """A long random opaque string — not a JWT. Nothing about it is
    decodable; it's just a lookup key into the refresh_tokens table."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(raw_token: str) -> str:
    """
    SHA-256 rather than bcrypt here: bcrypt is deliberately slow (that's
    the point for passwords, to resist brute-forcing a short, guessable
    secret). A refresh token is already a 48-byte random value no one is
    going to brute-force, so a fast cryptographic hash is the right tool —
    using bcrypt here would just add needless latency to every request
    that presents a refresh token.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def refresh_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    """
    Decodes the JWT from the Authorization header, looks up the user it
    refers to, and returns it. Any protected route can depend on this to
    get "the currently authenticated user" and reject the request early
    (401) if the token is missing, invalid, or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user