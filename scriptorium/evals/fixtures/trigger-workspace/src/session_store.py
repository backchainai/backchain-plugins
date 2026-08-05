"""Session storage backing DataForge's auth middleware.

Sessions live in Redis with a sliding TTL; a session is rotated rather than
extended on refresh, so a stolen refresh token has a bounded window.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass


@dataclass
class Session:
    account_id: str
    plan: str
    rate_limit_per_min: int
    expires_at: float

    @property
    def expired(self) -> bool:
        return time.time() > self.expires_at


class SessionStore:
    def __init__(self, redis_client, ttl_s: int = 3600) -> None:
        self._redis = redis_client
        self._ttl_s = ttl_s

    def get(self, token: str) -> Session | None:
        raw = self._redis.get(f"session:{token}")
        return None if raw is None else Session(**raw)

    def rotate(self, token: str) -> str:
        session = self.get(token)
        new_token = uuid.uuid4().hex
        self._redis.set(f"session:{new_token}", session, ex=self._ttl_s)
        self._redis.delete(f"session:{token}")
        return new_token  # old token unusable
