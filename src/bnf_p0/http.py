from __future__ import annotations

import email.utils
import random
import time
from datetime import datetime, timezone
from typing import Iterable

import httpx

from .rate_limit import RateLimiter

RETRYABLE = {429, 500, 502, 503, 504}


class RobustHttpClient:
    def __init__(self, *, timeout: float = 45.0, max_retries: int = 4, limiter: RateLimiter | None = None, transport: httpx.BaseTransport | None = None, sleeper=time.sleep, user_agent: str = "bnf-api-p0/0.1.3 (api.bnf.fr remediation)") -> None:
        self.max_retries = max_retries
        self.limiter = limiter or RateLimiter()
        self.sleeper = sleeper
        self.client = httpx.Client(timeout=timeout, follow_redirects=True, headers={"User-Agent": user_agent, "Accept": "*/*"}, transport=transport)

    def close(self) -> None:
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    @staticmethod
    def _retry_after_seconds(value: str | None) -> float | None:
        if not value:
            return None
        value = value.strip()
        try:
            return max(0.0, float(value))
        except ValueError:
            pass
        try:
            dt = email.utils.parsedate_to_datetime(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return max(0.0, (dt - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return None

    def request(self, method: str, url: str, *, bucket: str = "default", expected: Iterable[int] = (200,), **kwargs) -> httpx.Response:
        expected_set = set(expected)
        last_response: httpx.Response | None = None
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            self.limiter.acquire(bucket)
            try:
                response = self.client.request(method, url, **kwargs)
                last_response = response
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_exc = exc
                if attempt >= self.max_retries:
                    raise
                self.sleeper(min(30.0, 0.75 * (2 ** attempt)))
                continue
            if response.status_code in expected_set:
                return response
            if response.status_code not in RETRYABLE or attempt >= self.max_retries:
                response.raise_for_status()
                raise RuntimeError(f"Statut HTTP inattendu {response.status_code}")
            retry_after = self._retry_after_seconds(response.headers.get("Retry-After"))
            delay = retry_after if retry_after is not None else min(60.0, 1.0 * (2 ** attempt) + random.uniform(0.0, 0.25))
            self.sleeper(delay)
        if last_response is not None:
            last_response.raise_for_status()
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("Requête HTTP impossible")

    def get(self, url: str, *, bucket: str = "default", **kwargs) -> httpx.Response:
        return self.request("GET", url, bucket=bucket, **kwargs)
