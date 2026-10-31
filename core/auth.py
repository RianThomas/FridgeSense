"""Accounts: registration and login.

Passwords are never stored. Each one is salted and run through scrypt (a
deliberately slow hash), and compared in constant time. This is appropriate
for a local or small deployment; it does not add rate limiting, password
reset, or email verification.
"""
import hashlib
import hmac
import os
import re
import time

from core import db

USERNAME_RE = re.compile(r"^[a-z0-9_.-]{3,30}$")
MIN_PASSWORD = 8

_SCRYPT = dict(n=2 ** 14, r=8, p=1, dklen=32)


def _hash(password, salt):
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, **_SCRYPT)


def hash_password(password):
    salt = os.urandom(16)
    return salt.hex(), _hash(password, salt).hex()


def verify_password(password, salt_hex, hash_hex):
    candidate = _hash(password, bytes.fromhex(salt_hex))
    return hmac.compare_digest(candidate, bytes.fromhex(hash_hex))


def register(username, password, confirm):
    """-> (user dict, None) on success or (None, message) on failure."""
    username = (username or "").strip().lower()
    if not USERNAME_RE.match(username):
        return None, "Use 3 to 30 letters, numbers, dots, dashes or underscores for the username."
    if len(password or "") < MIN_PASSWORD:
        return None, f"Choose a password with at least {MIN_PASSWORD} characters."
    if password != confirm:
        return None, "The two passwords don't match."
    salt, pw_hash = hash_password(password)
    user = db.create_user(username, pw_hash, salt)
    if user is None:
        return None, "That username is already taken. Try another one."
    return user, None


def login(username, password):
    """-> (user dict, None) on success or (None, message) on failure."""
    username = (username or "").strip().lower()
    row = db.get_user(username)
    if row is None:
        # Spend the same time as a real check so timing doesn't reveal which
        # usernames exist.
        _hash(password or "", b"\x00" * 16)
        ok = False
    else:
        ok = verify_password(password or "", row["salt"], row["password_hash"])
    if not ok:
        time.sleep(0.4)
        return None, "Username or password is incorrect."
    return {"id": row["id"], "username": row["username"]}, None
