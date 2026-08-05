"""Auth middleware for DataForge's internal API.

Validates the bearer token on every request, resolves it to a customer
account, and attaches the account to the request context before the route
handler runs.
"""

from __future__ import annotations

from dataclasses import dataclass

from dataforge.errors import Unauthorized
from dataforge.session_store import SessionStore


@dataclass
class Account:
    id: str
    plan: str
    rate_limit_per_min: int


class AuthMiddleware:
    def __init__(self, session_store: SessionStore) -> None:
        self._sessions = session_store

    def authenticate(self, token: str) -> Account:
        session = self._sessions.get(token)
        if session is None or session.expired:
            raise Unauthorized("token invalid or expired")
        return Account(
            id=session.account_id,
            plan=session.plan,
            rate_limit_per_min=session.rate_limit_per_min,
        )

    def refresh(self, token: str) -> str:
        return self._sessions.rotate(token)
