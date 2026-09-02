import httpx
from bnf_p0.http import RobustHttpClient
from bnf_p0.rate_limit import RateLimiter


def test_429_retry_after_is_respected():
    calls = {"n": 0}
    slept = []

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "2"}, request=request)
        return httpx.Response(200, content=b"ok", request=request)

    client = RobustHttpClient(
        transport=httpx.MockTransport(handler),
        limiter=RateLimiter(intervals={"default": 0}),
        sleeper=slept.append,
    )
    try:
        response = client.get("https://example.test/x")
        assert response.content == b"ok"
        assert slept == [2.0]
        assert calls["n"] == 2
    finally:
        client.close()
