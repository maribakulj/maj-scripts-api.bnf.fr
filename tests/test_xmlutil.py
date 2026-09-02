from pathlib import Path
from bnf_p0.xmlutil import document_to_dict, parse_xml, find_first_text

FIX = Path(__file__).parent / "fixtures"


def test_pagination_structure_singular():
    data = (FIX / "pagination.xml").read_bytes()
    doc = document_to_dict(data)
    assert doc["livre"]["structure"]["nbVueImages"] == "374"
    assert find_first_text(parse_xml(data), "nbVueImages") == "374"


def test_namespaced_sru_parses():
    doc = document_to_dict((FIX / "sru.xml").read_bytes())
    assert doc["searchRetrieveResponse"]["numberOfRecords"] == "42"
