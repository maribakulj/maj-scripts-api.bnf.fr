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
