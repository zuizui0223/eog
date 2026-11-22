"""Fail-closed source identity gate unit tests."""
from benchmarks import wetland_duplicate_gate_v1 as m

def test_metadata_and_species_separation():
    cols=["surv","site","date","method","num","Pelobates fuscus","Rana dalmatina"]
    assert [c for c in cols if c not in m.META]==["Pelobates fuscus","Rana dalmatina"]

def test_fixed_native_source_digests():
    assert len(m.SURVEY_SHA)==64 and len(m.SITE_SHA)==64
