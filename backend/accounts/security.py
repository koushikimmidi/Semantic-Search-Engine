"""
Password hashing and signed session tokens (standard library only).

Passwords: PBKDF2-HMAC-SHA256, 260,000 iterations, random salt.
Tokens:    base64url(JSON payload) + "." + base64url(HMAC-SHA256),
           with an expiry time. The signing secret comes from
           AUTH_SECRET, or is generated once and stored on disk.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time


PBKDF2_ITERATIONS = 260_000
DEFAULT_TOKEN_TTL_SECONDS = 12 * 60 * 60


# ============================================================
# PASSWORDS
# ============================================================

def hash_password(password):

    salt = secrets.token_bytes(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )

    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password, stored_hash):

    try:
        algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$")
    except (ValueError, AttributeError):
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        (password or "").encode("utf-8"),
        bytes.fromhex(salt_hex),
        int(iterations)
    )

    return hmac.compare_digest(digest.hex(), digest_hex)


# ============================================================
# TOKENS
# ============================================================

def _b64encode(data):

    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(text):

    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


class TokenSigner:

    def __init__(self, secret=None, secret_file=None, ttl_seconds=None):

        self.ttl_seconds = ttl_seconds or int(
            os.getenv("AUTH_TOKEN_TTL_SECONDS", DEFAULT_TOKEN_TTL_SECONDS)
        )

        self.secret = (secret or os.getenv("AUTH_SECRET") or "").encode("utf-8")

        if not self.secret:
            self.secret = self._load_or_create_secret(
                secret_file or os.path.join(
                    os.getenv("AUTOMATION_DATA_DIR", "data/automation"),
                    "auth_secret.key"
                )
            )

    @staticmethod
    def _load_or_create_secret(path):

        if os.path.exists(path):
            with open(path, "rb") as file:
                value = file.read().strip()
            if value:
                return value

        directory = os.path.dirname(path)

        if directory:
            os.makedirs(directory, exist_ok=True)

        value = secrets.token_urlsafe(48).encode("ascii")

        with open(path, "wb") as file:
            file.write(value)

        try:
            os.chmod(path, 0o600)
        except OSError:
            pass

        return value

    def _sign(self, body):

        return _b64encode(hmac.new(self.secret, body.encode("ascii"), hashlib.sha256).digest())

    def create(self, user_id, username, role):

        payload = {
            "uid": user_id,
            "sub": username,
            "role": role,
            "exp": int(time.time()) + self.ttl_seconds
        }

        body = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))

        return f"{body}.{self._sign(body)}"

    def verify(self, token):
        """
        Return the payload for a valid, unexpired token, else None.
        """

        try:
            body, signature = (token or "").split(".", 1)
        except ValueError:
            return None

        if not hmac.compare_digest(signature, self._sign(body)):
            return None

        try:
            payload = json.loads(_b64decode(body))
        except (ValueError, json.JSONDecodeError):
            return None

        if int(payload.get("exp", 0)) < time.time():
            return None

        return payload
