"""Stdlib-only security primitives: password hashing, signed tokens, rate limiting, upload validation."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import time
from collections import defaultdict, deque
from typing import Callable


class ServiceError(Exception):
    """User-safe error: `message` is shown to users; internals are never included."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code, self.message = code, message


def hash_password(password: str, salt: bytes | None = None, iterations: int = 200_000) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2${iterations}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, it, salt, dk = stored.split("$")
        cand = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(it))
        return hmac.compare_digest(cand.hex(), dk)
    except (ValueError, TypeError):
        return False


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def make_token(user_id: str, secret: str, ttl: int = 3600, now: Callable[[], float] = time.time) -> str:
    body = _b64(json.dumps({"sub": user_id, "exp": int(now()) + ttl}).encode())
    sig = _b64(hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{sig}"


def verify_token(token: str, secret: str, now: Callable[[], float] = time.time) -> str:
    try:
        body, sig = token.split(".")
        good = _b64(hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, good):
            raise ValueError
        data = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        if data["exp"] < now():
            raise ValueError
        return str(data["sub"])
    except (ValueError, KeyError, TypeError):
        raise ServiceError("unauthorized", "Invalid or expired credentials.") from None


class RateLimiter:
    def __init__(self, limit: int, window: float = 60.0, now: Callable[[], float] = time.monotonic) -> None:
        self.limit, self.window, self.now = limit, window, now
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        t, q = self.now(), self._hits[key]
        while q and q[0] <= t - self.window:
            q.popleft()
        if len(q) >= self.limit:
            raise ServiceError("rate_limited", "Too many requests. Please wait a moment and retry.")
        q.append(t)


ALLOWED_EXT = {"pdf", "txt"}


def validate_upload(filename: str, data: bytes, max_bytes: int) -> tuple[str, str]:
    """Returns (extension, safe_filename). Content is checked, not just the extension."""
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", os.path.basename(filename or "").strip())[:120]
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in ALLOWED_EXT:
        raise ServiceError("invalid_upload", "Only PDF and plain-text files are supported.")
    if not data:
        raise ServiceError("invalid_upload", "The file is empty.")
    if len(data) > max_bytes:
        raise ServiceError("invalid_upload", f"File exceeds the {max_bytes // (1024 * 1024)} MB limit.")
    if ext == "pdf" and not data.startswith(b"%PDF-"):
        raise ServiceError("invalid_upload", "The file is not a valid PDF.")
    if ext == "txt":
        if b"\x00" in data:
            raise ServiceError("invalid_upload", "The file is not valid text.")
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            raise ServiceError("invalid_upload", "Text files must be UTF-8 encoded.") from None
    return ext, name
