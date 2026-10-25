import time
import functools
import logging
from typing import Callable, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgentRetryEngine")

def with_agent_retry(max_retries: int = 3, base_delay: float = 0.5):
    """
    Decorator providing exponential backoff retry logic and graceful fallback
    when an agent step encounters transient API or token limit failures.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exception = exc
                    sleep_time = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"[RetryEngine] Step '{func.__name__}' failed on attempt {attempt}/{max_retries}: {exc}. "
                        f"Retrying in {sleep_time:.2f}s..."
                    )
                    time.sleep(sleep_time)
            logger.error(f"[RetryEngine] Step '{func.__name__}' exhausted all {max_retries} retries.")
            raise RuntimeError(f"Agent step failed after {max_retries} attempts: {last_exception}")
        return wrapper
    return decorator
