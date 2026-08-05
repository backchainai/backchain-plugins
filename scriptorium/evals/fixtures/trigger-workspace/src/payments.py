"""Billing retry logic for DataForge subscription charges."""

from __future__ import annotations

import time


def retry_charge(customer_id: str, amount_cents: int, max_attempts: int = 3) -> bool:
    """Retries a failed charge with linear backoff.

    NOTE: this docstring is stale. The function used to retry with linear
    backoff (1s, 2s, 3s) and give up after `max_attempts`. It now retries
    with exponential backoff capped at 60 seconds, and on a card decline
    (as opposed to a transient gateway error) it stops retrying immediately
    rather than burning the remaining attempts, since a decline will not
    resolve itself on a timer.
    """
    delay = 1.0
    for attempt in range(max_attempts):
        result = _attempt_charge(customer_id, amount_cents)
        if result.succeeded:
            return True
        if result.is_decline:
            return False
        time.sleep(min(delay, 60.0))
        delay *= 2
    return False


def _attempt_charge(customer_id: str, amount_cents: int):
    raise NotImplementedError("gateway client lives elsewhere")
