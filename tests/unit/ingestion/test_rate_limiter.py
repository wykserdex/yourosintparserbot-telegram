"""Unit tests for TokenBucketRateLimiter."""

import time

import pytest

from yourosint.contexts.ingestion.adapters.telegram.rate_limiter import TokenBucketRateLimiter


@pytest.mark.asyncio
async def test_token_bucket_acquire():
    limiter = TokenBucketRateLimiter(rate=100.0, capacity=10.0)
    start = time.time()
    await limiter.acquire(1.0)
    assert time.time() - start < 0.1
