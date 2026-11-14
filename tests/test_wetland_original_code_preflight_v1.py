"""Offline tests of published R-source-only preflight."""
from benchmarks import wetland_original_code_preflight_v1 as pre


def test_matcher_is_bounded_and_line_numbered():
    payload = b"x <- 1\nfoo <- distinct(surv)\nbar <- filter(dat, num > 0)\n"
    ev = pre.bounded_evidence(payload, limit=1)
    assert ev["line_count"] == 3
    assert ev["keyword_hit_count"] == 2
    assert ev["selected_matches"] == [{"line": 2, "text": "foo <- distinct(surv)"}]
    assert ev["truncated"]


def test_original_source_md5_is_source_only():
    assert set(pre.SOURCES) == {
        "wetland_amp_q1_multispecies_occu_modelling.R",
        "wetland_amp_q2_multispecies_occu_modelling.R",
    }
    assert all(len(md5) == 32 for md5 in pre.SOURCES.values())
