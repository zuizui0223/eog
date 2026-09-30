import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript" / "bam_identifiability" / "MANUSCRIPT_DRAFT_V3.md"


def _json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_manuscript_v3_matches_frozen_deterministic_evidence_ladder():
    text = MANUSCRIPT.read_text(encoding="utf-8")
    result = _json("validation/known_truth_bam_v3/result_summary_v3.json")

    counts = result["pooled_unique_counts"]
    expected = {
        "E0": 0,
        "E1": 25,
        "E2": 159,
        "E3": 275,
        "E4": 565,
        "E5": 768,
        "E6": 768,
    }
    assert counts == expected
    assert result["eligible_truth_count"] == 768
    assert result["system_roster_size"] == 12

    for stage, value in expected.items():
        if stage == "E0":
            assert "0/768" in text or "0 / 768" in text
        else:
            assert str(value) in text


def test_manuscript_v3_matches_restrictiveness_and_temporal_results():
    text = MANUSCRIPT.read_text(encoding="utf-8")
    restrict = _json(
        "validation/restrictiveness_ambiguity_v3_1/audit_summary_v3_1.json"
    )
    temporal = _json(
        "validation/independent_stochastic_temporal_v3_2/result_summary_v3_2.json"
    )

    assert restrict["strict_support_inclusion_pair_count"] == 304
    assert restrict["nesting_monotonicity_violations"] == 0
    assert "304/304" in text

    assert temporal["static_support_classes"]["count"] == 8
    assert temporal["temporal_signature_classes"]["count"] == 20
    assert temporal["static_M_equivalent_pair_count"] == 48
    assert temporal["realised_temporal_split_pair_count"] == 19
    assert temporal["temporal_strict_gain_runs"] == 256
    assert temporal["planned_runs"] == 384
    assert "256/384" in text


def test_manuscript_v3_matches_multilandscape_and_measurement_audits():
    text = MANUSCRIPT.read_text(encoding="utf-8")
    multi = _json(
        "validation/multilandscape_stochastic_bam_v4/result_summary_v4.json"
    )
    measure = _json(
        "validation/bam_identifiability_theory_v1/"
        "targeted_measurement_exact_audit_summary_v1.json"
    )

    assert multi["planned_landscape_count"] == 8
    assert multi["eligible_landscape_count"] == 6
    assert multi["design_stop_count"] == 2
    assert multi["eligible_stochastic_runs"] == 1152
    assert "1,152" in text
    assert "DESIGN_STOP" in text

    assert measure["truth_cases"] == 768
    assert measure["failures"] == 0
    assert measure["exact_maximum_measurements"] == {
        "A": 1,
        "B": 2,
        "AB_joint": 3,
        "M": 2,
        "tau": 0,
        "M_tau_joint": 2,
    }
    for phrase in (
        "direct A: 1 node",
        "direct B: 2 nodes",
        "joint A+B: 3 nodes",
        "direct M accessibility: 2 nodes",
    ):
        assert phrase in text


def test_manuscript_v3_has_no_known_math_corruption():
    text = MANUSCRIPT.read_text(encoding="utf-8")

    forbidden = (
        "A cap B",
        "R_1subset",
        "C(R_1)supseteq",
        "S_6subseteq",
        "D_msubseteq",
        "bigcup_{min Q}",
        "\x08",
        "\x0b",
    )
    for token in forbidden:
        assert token not in text

    assert "\\cap" in text
    assert "\\subseteq" in text
    assert "\\supseteq" in text
    assert "\\bigcup" in text


def test_manuscript_v3_does_not_import_eog_wf_predictive_results():
    text = MANUSCRIPT.read_text(encoding="utf-8")

    for forbidden in (
        "Azores yellow eel",
        "King Rail",
        "Tampa Bay",
        "Layer B",
        "macro log loss",
        "3/31/3",
    ):
        assert forbidden not in text


def test_manuscript_v3_contains_required_prior_art_boundary():
    text = MANUSCRIPT.read_text(encoding="utf-8")

    for citation in (
        "Soberón & Peterson, 2005",
        "Saupe et al., 2012",
        "Soberón & Osorio-Olvera, 2023",
        "Yanco et al., 2020",
        "Lotterhos et al., 2022",
        "Atkinson & Cox, 1974",
        "Papanikolaou et al., 2023",
    ):
        assert citation in text

    assert "Our contribution is not to rediscover that general fact." in text
    assert "Hitting-set optimization itself is not novel" in text
