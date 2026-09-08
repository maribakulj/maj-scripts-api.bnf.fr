from bnf_p0.rate_limit import RateLimiter


class FakeTime:
    def __init__(self): self.value = 0.0
    def clock(self): return self.value
    def sleep(self, seconds): self.value += seconds


def test_hd_interval_is_enforced():
    ft = FakeTime()
    rl = RateLimiter(intervals={"iiif_hd": 12.25, "default": 0}, clock=ft.clock, sleeper=ft.sleep)
    assert rl.acquire("iiif_hd") == 0
    waited = rl.acquire("iiif_hd")
    assert waited == 12.25
    assert ft.value == 12.25


def test_alto_is_paced_like_the_text_route():
    # L'ALTO remplace .texteBrut : sans cadence, une extraction de plusieurs
    # pages enchaîne les requêtes et Gallica répond 429.
    from bnf_p0.rate_limit import DEFAULT_INTERVALS
    assert DEFAULT_INTERVALS["alto"] == DEFAULT_INTERVALS["text"]


def test_alto_requests_go_through_the_alto_bucket():
    import httpx
    from bnf_p0.client import GallicaClient
    from bnf_p0.http import RobustHttpClient
    from bnf_p0.rate_limit import RateLimiter

    buckets = []

    class Spy(RateLimiter):
        def acquire(self, bucket="default"):
            buckets.append(bucket)
            return 0.0

    def handler(request):
        return httpx.Response(200, content=b"<alto/>", request=request,
                              headers={"content-type": "application/xml"})

    http = RobustHttpClient(transport=httpx.MockTransport(handler),
                            limiter=Spy(intervals={"alto": 0, "default": 0}),
                            sleeper=lambda _: None)
    with GallicaClient(http) as client:
        client.alto("bpt6kX", 3)
    assert buckets == ["alto"]
