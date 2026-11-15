"""
Authentication and roles.

Two ways to authenticate:

1. User accounts (the web UI): POST /auth/login with username and
   password returns a signed token; the browser sends it as
   `Authorization: Bearer <token>`. Accounts have the role
   `admin` or `employee` and are managed by admins.

2. API keys (scripts, integrations): `X-API-Key` header.
       ADMIN_API_KEY -> admin
       AGENT_API_KEY -> agent (same permissions as an employee)

Permission levels (each includes the ones below):

    admin              everything: documents, users, settings, scheduler
    employee / agent   ask questions, review queue, test messages, analytics
    viewer             ask questions and browse the knowledge base

If no API keys are set and no user accounts exist, authentication is
disabled and every request is treated as admin (first-run / local
development). A warning is printed at startup in that case.
"""

import hmac
import os
from typing import Optional

from fastapi import Depends, Header, HTTPException


ROLE_LEVELS = {
    "viewer": 0,
    "agent": 1,
    "employee": 1,
    "admin": 2
}

_user_store = None
_token_signer = None


def configure(user_store=None, token_signer=None):

    global _user_store, _token_signer

    _user_store = user_store
    _token_signer = token_signer


def _configured_keys():

    return {
        "admin": (os.getenv("ADMIN_API_KEY") or "").strip(),
        "agent": (os.getenv("AGENT_API_KEY") or "").strip()
    }


def users_exist():

    try:
        return bool(_user_store and _user_store.count() > 0)
    except Exception:
        return False


def auth_enabled():

    return any(_configured_keys().values()) or users_exist()


def role_for_key(api_key):

    keys = _configured_keys()

    if not auth_enabled():
        return "admin"

    api_key = (api_key or "").strip()

    if api_key:

        # Constant-time comparison; admin checked first.
        for role in ("admin", "agent"):

            expected = keys[role]

            if expected and hmac.compare_digest(api_key, expected):
                return role

    return "viewer"


def resolve_principal(authorization=None, api_key=None):
    """
    Work out who is calling. Returns a dict:
        {"role", "username", "user_id", "full_name", "method"}
    """

    # 1. Signed user token.
    if authorization and authorization.lower().startswith("bearer ") and _token_signer:

        payload = _token_signer.verify(authorization[7:].strip())

        if payload and _user_store:

            user = _user_store.get(payload.get("uid"))

            # Role and active flag come from the database, so changes
            # by an admin take effect immediately.
            if user and user["active"]:
                return {
                    "role": user["role"],
                    "username": user["username"],
                    "user_id": user["id"],
                    "full_name": user["full_name"],
                    "method": "account"
                }

    # 2. API key (or auth disabled).
    role = role_for_key(api_key)

    if role == "viewer":
        return {"role": "viewer", "username": "anonymous", "user_id": None, "full_name": "", "method": "none"}

    if not auth_enabled():
        return {"role": "admin", "username": "local-admin", "user_id": None, "full_name": "", "method": "disabled"}

    return {
        "role": role,
        "username": f"{role}-api-key",
        "user_id": None,
        "full_name": "",
        "method": "api_key"
    }


def get_principal(
    authorization: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None)
):

    return resolve_principal(authorization, x_api_key)


def get_role(principal: dict = Depends(get_principal)):

    return principal["role"]


def require_role(minimum_role):
    """
    FastAPI dependency: reject the request unless the caller's role
    is at least `minimum_role`. Returns the principal.
    """

    required_level = ROLE_LEVELS[minimum_role]

    def dependency(principal: dict = Depends(get_principal)):

        if ROLE_LEVELS[principal["role"]] < required_level:

            raise HTTPException(
                status_code=401 if principal["role"] == "viewer" else 403,
                detail=(
                    "Please sign in to continue."
                    if principal["role"] == "viewer"
                    else f"This action requires the '{minimum_role}' role."
                )
            )

        return principal

    return dependency
