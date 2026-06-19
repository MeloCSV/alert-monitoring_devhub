import logging
import time
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

_DEFAULT_ATTEMPTS = 3
_DEFAULT_BACKOFF = 1.0  # seconds; doubles on each attempt (1s → 2s → 4s)


def with_retry(
    fn: Callable[[], T],
    attempts: int = _DEFAULT_ATTEMPTS,
    backoff: float = _DEFAULT_BACKOFF,
    label: str = "",
) -> T:
    """Call *fn* up to *attempts* times, retrying on any exception.

    Waits backoff * 2^(attempt-1) seconds between retries.
    Re-raises the last exception if all attempts are exhausted.
    """
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:
            if attempt == attempts:
                raise
            wait = backoff * (2 ** (attempt - 1))
            logger.warning(
                "Retry %d/%d for '%s' after error: %s — waiting %.1fs",
                attempt,
                attempts,
                label,
                exc,
                wait,
            )
            time.sleep(wait)
    raise RuntimeError("unreachable")  # type: ignore[return]
