"""Gallica refuse par 403 les agents par défaut de plusieurs bibliothèques HTTP
(`python-requests`, `Python-urllib`, `python-httpx`, `curl`). Cette liste n'est
documentée nulle part : si elle s'élargissait jusqu'à l'agent de ce client, il
faut que la validation dise « notre agent est refusé » et non « Gallica est
cassé »."""

import httpx

from bnf_p0.http import DEFAULT_USER_AGENT, probe_user_agent

URL = "https://gallica.bnf.fr/services/Pagination?ark=bpt6kX"


def transport(*, with_ua: int, without_ua: int):
    def handler(request):
        declared = request.headers.get("user-agent")
        code = with_ua if declared else without_ua
        return httpx.Response(code, content=b"<x/>", request=request)
    return httpx.MockTransport(handler)


def test_accepted_user_agent_is_reported_as_such():
    result = probe_user_agent(URL, transport=transport(with_ua=200, without_ua=200))
    assert result["status"] == "ACCEPTED"
    assert result["ok"] is True


def test_a_refused_user_agent_is_named_as_the_cause():
    result = probe_user_agent(URL, transport=transport(with_ua=403, without_ua=200))
    assert result["status"] == "REFUSED"
    assert result["ok"] is False
    assert DEFAULT_USER_AGENT in result["detail"]
    assert "BnF" in result["detail"]


def test_a_service_that_answers_nobody_is_not_blamed_on_the_user_agent():
    result = probe_user_agent(URL, transport=transport(with_ua=503, without_ua=503))
    assert result["status"] == "SERVICE_UNAVAILABLE"
    assert result["ok"] is False
    assert "identification" in result["detail"]


def test_the_control_request_sends_no_user_agent_at_all():
    """Le témoin ne doit pas inventer une autre identité : il n'envoie rien."""
    seen = []

    def handler(request):
        seen.append(request.headers.get("user-agent"))
        return httpx.Response(403 if seen[-1] else 200, content=b"<x/>", request=request)

    probe_user_agent(URL, transport=httpx.MockTransport(handler))
    assert seen[0] == DEFAULT_USER_AGENT
    assert seen[1] is None


def test_the_client_and_the_probe_share_one_definition():
    """La sonde doit tester l'agent que le client envoie réellement, pas une
    copie qui pourrait diverger."""
    import inspect
    from bnf_p0.http import RobustHttpClient
    defaut = inspect.signature(RobustHttpClient).parameters["user_agent"].default
    assert defaut == DEFAULT_USER_AGENT
