from __future__ import annotations

import uuid

from app.db.repo import SQLiteRepository

from app.core.security import ServiceError, hash_password, make_token, verify_password, verify_token


class AuthService:
    """User accounts persisted through the repository. Passwords are PBKDF2-hashed."""

    def __init__(self, secret: str, repo: SQLiteRepository | None = None) -> None:
        if len(secret) < 16:
            raise ValueError("auth secret must be at least 16 characters")
        self._secret = secret
        self.repo = repo or SQLiteRepository(":memory:")

    def register(self, email: str, password: str) -> str:
        email = email.strip().lower()
        if "@" not in email or len(password) < 10:
            raise ServiceError("invalid_input", "Provide a valid email and a password of at least 10 characters.")
        uid = uuid.uuid4().hex[:12]
        try:
            self.repo.add_user(uid, email, hash_password(password))
        except ValueError:
            raise ServiceError("invalid_input", "That email is already registered.") from None
        return uid

    def login(self, email: str, password: str) -> str:
        rec = self.repo.get_user(email.strip().lower())
        if not rec or not verify_password(password, rec[1]):
            raise ServiceError("unauthorized", "Invalid email or password.")
        return make_token(rec[0], self._secret)

    def authenticate(self, token: str) -> str:
        return verify_token(token, self._secret)
