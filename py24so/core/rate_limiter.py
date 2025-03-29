import time
from typing import Any, Dict, Optional, Tuple


class RateLimiter:
    """
    A token bucket rate limiter implementation.
    
    This class implements the token bucket algorithm for rate limiting API calls.
    It maintains a bucket of tokens that refills at a constant rate. Each API call
    consumes one token. If the bucket is empty, the caller must wait for more tokens.
    """

    def __init__(self, rate: int = 100, period: int = 60):
        """
        Initialize the rate limiter.
        
        Args:
            rate: Maximum number of tokens (requests) per period
            period: Time period in seconds
        """
        self.rate = rate
        self.period = period
        self.tokens = rate
        self.last_refill_time = time.time()
        self._lock = False  # Simple lock mechanism

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill_time
        
        # Calculate new tokens to add based on elapsed time
        new_tokens = (elapsed / self.period) * self.rate
        
        # Add new tokens up to the maximum rate
        self.tokens = min(self.rate, self.tokens + new_tokens)
        self.last_refill_time = now

    def acquire(self, block: bool = True) -> Tuple[bool, Optional[float]]:
        """
        Acquire a token from the bucket.
        
        Args:
            block: If True, block until a token is available
            
        Returns:
            A tuple of (success, wait_time) where success is True if a token was acquired
            and wait_time is the time to wait in seconds (None if not blocking)
        """
        # Simple lock mechanism to avoid race conditions in async context
        if self._lock:
            return False, 0.01  # Try again after 10ms
            
        try:
            self._lock = True
            self._refill_tokens()
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True, None
            
            if not block:
                return False, None
            
            # Calculate wait time
            wait_time = (1 - self.tokens) * (self.period / self.rate)
            return False, wait_time
        finally:
            self._lock = False
            
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the rate limiter.
        
        Returns:
            Dictionary with current tokens, maximum rate, and period
        """
        self._refill_tokens()  # Update tokens
        return {
            "available_tokens": self.tokens,
            "max_rate": self.rate,
            "period_seconds": self.period,
        } 