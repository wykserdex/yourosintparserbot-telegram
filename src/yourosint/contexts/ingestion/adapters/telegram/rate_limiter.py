"""Adaptive Token Bucket Rate Limiter."""

import asyncio
import time


class TokenBucketRateLimiter:
    """Async token-bucket rate limiter preventing Telegram flood waits."""

    def __init__(self, rate: float, capacity: float):
        self.rate = rate  # Tokens added per second
        self.capacity = capacity  # Max tokens
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: float = 1.0) -> None:
        async with self._lock:
            while True:
                now = time.time()
                elapsed = now - self.last_refill
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                self.last_refill = now

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return

                needed = tokens - self.tokens
                wait_time = needed / self.rate
                await asyncio.sleep(wait_time)
