from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "manuscript/paper_ready/endpoint_source_ledger.md"


def test_fresh_endpoint_source_identities_match_frozen_issues() -> None:
    text = LEDGER.read_text(encoding="utf-8")
    for token in [
        "10.5281/zenodo.18154777",
        "10.5281/zenodo.18154674",
        "10.1111/jfb.70355",
        "10.5066/P9RRIIR2",
        "5ecf119d82ce30fd980854bd",
        "tbep-tech/obis-example",
        "6c567beff95ea04f0e397101befb49d5233ace8f",
        "583b4d4e328290ab065346579eb4f29f03ea0f99",
        "d34aeb5aedb72459d1e04059629cb09450df929e",
        "e463046726080334637824555309fd89c7c447da",
    ]:
        assert token in text


def test_source_ledger_does_not_invent_unverified_bibliographic_metadata() -> None:
    text = LEDGER.read_text(encoding="utf-8")
    assert "should resolve the full author/title/year metadata" in text
    assert "should not invent a journal article citation" in text
    assert "rather than inventing bibliographic metadata" in text
    assert "do not change endpoint definitions" in text
