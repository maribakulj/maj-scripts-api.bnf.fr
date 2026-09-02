from bnf_p0.compat.pyllica import pressdate


def test_gregorian_leap_year_2000():
    assert pressdate(2000, 2, 28, 1, 3) == ["20000228", "20000229", "20000301"]


def test_non_leap_year_1900():
    assert pressdate(1900, 2, 28, 1, 2) == ["19000228", "19000301"]
