import re
import threading
import time
from datetime import datetime

from backend.accounts.security import hash_password, verify_password


ROLES = ("admin", "employee")

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]{3,32}$")
MIN_PASSWORD_LENGTH = 8

# Brute-force protection: lock a username after repeated failures.
MAX_FAILED_LOGINS = 5
LOCKOUT_SECONDS = 300


class AccountError(ValueError):
    """A user-facing validation error (bad input, last admin, ...)."""


def _now():

    return datetime.now().isoformat(timespec="seconds")


def _public(user):

    if user is None:
        return None

    return {
        "id": user["id"],
        "username": user["username"],
        "full_name": user["full_name"],
        "role": user["role"],
        "active": bool(user["active"]),
        "created_at": user["created_at"],
        "last_login": user["last_login"]
    }


class UserStore:

    def __init__(self, db):

        self.db = db
        self._failures = {}
        self._lock = threading.Lock()

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_username(username):

        username = (username or "").strip()

        if not USERNAME_PATTERN.match(username):
            raise AccountError(
                "Username must be 3-32 characters: letters, numbers, dot, dash or underscore."
            )

        return username

    @staticmethod
    def _validate_password(password):

        if len(password or "") < MIN_PASSWORD_LENGTH:
            raise AccountError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
            )

        return password

    @staticmethod
    def _validate_role(role):

        if role not in ROLES:
            raise AccountError("Role must be 'admin' or 'employee'.")

        return role

    # ========================================================
    # QUERIES
    # ========================================================

    def count(self):

        return self.db.query("SELECT COUNT(*) AS n FROM users")[0]["n"]

    def _active_admin_count(self):

        return self.db.query(
            "SELECT COUNT(*) AS n FROM users WHERE role = 'admin' AND active = 1"
        )[0]["n"]

    def _get_row(self, user_id):

        rows = self.db.query("SELECT * FROM users WHERE id = ?", (user_id,))

        return rows[0] if rows else None

    def get(self, user_id):

        return _public(self._get_row(user_id))

    def list(self):

        return [
            _public(row)
            for row in self.db.query("SELECT * FROM users ORDER BY role, username")
        ]

    # ========================================================
    # CREATE / UPDATE / DELETE
    # ========================================================

    def create(self, username, password, role="employee", full_name=""):

        username = self._validate_username(username)
        self._validate_password(password)
        self._validate_role(role)

        if self.db.query("SELECT id FROM users WHERE username = ?", (username,)):
            raise AccountError(f"The username '{username}' is already taken.")

        user_id = self.db.execute(
            "INSERT INTO users (username, full_name, role, password_hash, active, created_at) "
            "VALUES (?, ?, ?, ?, 1, ?)",
            (username, (full_name or "").strip()[:80], role, hash_password(password), _now())
        )

        return self.get(user_id)

    def update(self, user_id, role=None, active=None, full_name=None, password=None):

        user = self._get_row(user_id)

        if user is None:
            raise AccountError("User not found.")

        # Never leave the system without an active admin.
        loses_admin = user["role"] == "admin" and user["active"] and (
            (role is not None and role != "admin") or active is False
        )

        if loses_admin and self._active_admin_count() <= 1:
            raise AccountError("You cannot demote or disable the last active admin.")

        if role is not None:
            self.db.execute("UPDATE users SET role = ? WHERE id = ?", (self._validate_role(role), user_id))

        if active is not None:
            self.db.execute("UPDATE users SET active = ? WHERE id = ?", (1 if active else 0, user_id))

        if full_name is not None:
            self.db.execute("UPDATE users SET full_name = ? WHERE id = ?", (full_name.strip()[:80], user_id))

        if password is not None:
            self._validate_password(password)
            self.db.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (hash_password(password), user_id)
            )

        return self.get(user_id)

    def delete(self, user_id):

        user = self._get_row(user_id)

        if user is None:
            raise AccountError("User not found.")

        if user["role"] == "admin" and user["active"] and self._active_admin_count() <= 1:
            raise AccountError("You cannot delete the last active admin.")

        self.db.execute("DELETE FROM users WHERE id = ?", (user_id,))

        return _public(user)

    # ========================================================
    # AUTHENTICATION
    # ========================================================

    def is_locked(self, username):

        with self._lock:
            failures, last = self._failures.get((username or "").lower(), (0, 0))

        return failures >= MAX_FAILED_LOGINS and time.time() - last < LOCKOUT_SECONDS

    def authenticate(self, username, password):
        """
        Return the public user on success. Raise AccountError with a
        generic message on failure (does not reveal which part was
        wrong).
        """

        key = (username or "").strip().lower()

        if self.is_locked(key):
            raise AccountError(
                "Too many failed attempts. Try again in a few minutes."
            )

        rows = self.db.query("SELECT * FROM users WHERE username = ?", (key,))
        user = rows[0] if rows else None

        if (
            user is None
            or not user["active"]
            or not verify_password(password, user["password_hash"])
        ):
            with self._lock:
                failures, _ = self._failures.get(key, (0, 0))
                self._failures[key] = (failures + 1, time.time())

            raise AccountError("Incorrect username or password.")

        with self._lock:
            self._failures.pop(key, None)

        self.db.execute("UPDATE users SET last_login = ? WHERE id = ?", (_now(), user["id"]))

        return self.get(user["id"])

    def record_login(self, user_id):

        self.db.execute("UPDATE users SET last_login = ? WHERE id = ?", (_now(), user_id))

        return self.get(user_id)

    def change_password(self, user_id, current_password, new_password):

        user = self._get_row(user_id)

        if user is None or not verify_password(current_password, user["password_hash"]):
            raise AccountError("Your current password is incorrect.")

        return self.update(user_id, password=new_password)
