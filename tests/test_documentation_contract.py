"""Le vérificateur documentaire doit séparer « le site a changé » de
« le site n'a pas répondu ». Sans cette distinction, une indisponibilité
d'api.bnf.fr se présente comme une dérive éditoriale."""

import importlib.util
import sys
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location(
    "verify_public_documentation_contract",
    ROOT / "scripts" / "verify_public_documentation_contract.py",
)
contract = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = contract
spec.loader.exec_module(contract)


def test_all_green_is_a_pass():
    assert contract.overall_status([
        {"check": "fetch:quotas", "status": "PASS"},
        {"check": "quota-contract", "status": "PASS"},
    ]) == "PASS"


def test_unreachable_page_is_not_reported_as_drift():
    assert contract.overall_status([
        {"check": "fetch:wrappers", "status": "UNREACHABLE"},
        {"check": "wrapper-list-contract", "status": "SKIPPED"},
    ]) == "UNREACHABLE"


def test_real_drift_still_fails():
    assert contract.overall_status([
        {"check": "fetch:iiif", "status": "PASS"},
        {"check": "iiif-public-version-2", "status": "DRIFT"},
    ]) == "FAIL"


def test_drift_wins_over_an_unreachable_page():
    # Une page lisible qui a changé reste un signal éditorial, même si une
    # autre page est injoignable au même moment.
    assert contract.overall_status([
        {"check": "fetch:wrappers", "status": "UNREACHABLE"},
        {"check": "fetch:iiif", "status": "PASS"},
        {"check": "iiif-public-version-2", "status": "DRIFT"},
    ]) == "FAIL"


def test_non_normative_observation_never_fails_the_build():
    assert contract.overall_status([
        {"check": "fetch:pyllica", "status": "PASS"},
        {"check": "pyllica-hd-examples-still-present", "status": "CHANGED"},
    ]) == "PASS"


def test_exit_codes_separate_the_three_verdicts():
    assert (contract.EXIT_PASS, contract.EXIT_UNREACHABLE, contract.EXIT_DRIFT) == (0, 2, 4)


def test_fetch_retries_before_declaring_a_page_unreachable():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] < 3:
            raise httpx.ReadTimeout("trop lent", request=request)
        return httpx.Response(200, html="<p>Contenu</p>", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    contract.time.sleep = lambda _: None
    body, error, code = contract.fetch(client, "https://api.bnf.fr/fr/x")
    assert calls["n"] == 3
    assert error is None
    assert body == "Contenu"


def test_a_page_that_never_answers_is_reported_with_its_error():
    def handler(request):
        raise httpx.ReadTimeout("trop lent", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    contract.time.sleep = lambda _: None
    body, error, code = contract.fetch(client, "https://api.bnf.fr/fr/x")
    assert body is None
    assert "ReadTimeout" in error


def test_the_checker_diagnoses_the_right_host():
    # Le diagnostic réseau était figé sur gallica.bnf.fr ; il accepte
    # désormais un hôte, ce dont ce script a besoin pour api.bnf.fr.
    assert contract.HOST == "api.bnf.fr"
    assert contract.diagnose("example.invalid")["host"] == "example.invalid"


def test_an_unresolvable_host_is_diagnosed_not_crashed():
    report = contract.diagnose("hote-qui-nexiste-pas.invalid")
    assert report["ok"] is False
    assert report["dns"]["ok"] is False
