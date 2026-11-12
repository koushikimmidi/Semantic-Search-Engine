"""
API key authentication with roles.

Roles (each includes the ones below it):

    admin   upload/delete documents, start/stop the scheduler,
            plus everything an agent can do
    agent   email automation: run inbox checks, test messages,
            review queue (resolve / reply), dashboard and history
    viewer  ask questions and browse the knowledge base (no key)

Keys are read from the environment:

    ADMIN_API_KEY=...
    AGENT_API_KEY=...

Clients send the key in the `X-API-Key` header.

If neither key is set, authentication is disabled and every
request is treated as admin (local development). A warning is
printed at startup in that case.
"""

import hmac
import os
from typing import Optional

from fastapi import Depends, Header, HTTPException


ROLE_LEVELS = {
    "viewer": 0,
    "agent": 1,
    "admin": 2
}


def _configured_keys():

    return {
        "admin": (os.getenv("ADMIN_API_KEY") or "").strip(),
        "agent": (os.getenv("AGENT_API_KEY") or "").strip()
    }


def auth_enabled():

    return any(_configured_keys().values())


def role_for_key(api_key):

    keys = _configured_keys()

    if not any(keys.values()):
        return "admin"

    api_key = (api_key or "").strip()

    if api_key:

        # Constant-time comparison; admin checked first.
        for role in ("admin", "agent"):

            expected = keys[role]

            if expected and hmac.compare_digest(api_key, expected):
                return role

    return "viewer"


def get_role(x_api_key: Optional[str] = Header(default=None)):

    return role_for_key(x_api_key)


def require_role(minimum_role):
    """
    FastAPI dependency: reject the request unless the caller's role
    is at least `minimum_role`.
    """

    required_level = ROLE_LEVELS[minimum_role]

    def dependency(role: str = Depends(get_role)):

        if ROLE_LEVELS[role] < required_level:

            raise HTTPException(
                status_code=401 if role == "viewer" else 403,
                detail=(
                    f"This action requires the '{minimum_role}' role. "
                    "Provide a valid X-API-Key."
                )
            )

        return role

    return dependency
