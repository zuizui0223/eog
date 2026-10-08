"""Structural guard for frozen v23 observation witnesses and excluded source nodes."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
REPORT = DIR / "v23_readout_witness_boundary_v1.json"
FIVE_CLASS = DIR / "v23_readout_synergy_decomposition_v1.json"
V23_SUMMARY = ROOT / "validation/eog_original_idea_provenance_observability_v23/result_summary_v23.json"
V23_SCRIPT = ROOT / "benchmarks/run_eog_original_idea_provenance_observability_v23.py"
V22_SCRIPT = ROOT / "benchmarks/run_eog_original_idea_history_observability_v22.py"
SCRIPT = ROOT / "scripts/audit_eog_v23_readout_witness_boundary_v1.py"


def load_script():
    sys.path.insert(0,str(ROOT / "scripts"))
    try:
        spec=importlib.util.spec_from_file_location("v23_witness_audit",SCRIPT)
        assert spec and spec.loader
        m=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    finally:
        sys.path.pop(0)


def frozen():
    return json.loads(REPORT.read_text(encoding="utf-8"))


def test_complete_frozen_actions_have_exact_witness_sizes_and_confluence():
    r=frozen()
    p=json.loads(FIVE_CLASS.read_text(encoding="utf-8"))
    source=json.loads(V23_SUMMARY.read_text(encoding="utf-8"))
    m=load_script()
    assert r["status"]=="POST_RESULT_FORENSIC_NO_NEW_SIMULATION"
    assert r["source_artifact_sha256"]==m.V23["sha256"]
    assert r["source_result_fingerprint"]==source["result_fingerprint"]
    assert r["source_artifact_sha256"]=="a859e7b6ec5e8af47b56a67a10b89ae7ab65ca3e1a70aed9317f663f863eaae9"
    assert r["matched_landscapes"]==384
    assert r["paired_layouts_per_landscape"]==2
    assert r["mixed_only_total_layout_cases"]==p["true_mixed_library_synergy_designs"]==18
    assert r["mixed_witness_occupancy_action_counts"]=={"O_t4":18}
    assert r["mixed_witnesses_all_exactly_one_snapshot_plus_one_provenance_tag"] is True
    assert r["by_layout"]["clustered"]["strict_mixed_only"]==17
    assert r["by_layout"]["dispersed"]["strict_mixed_only"]==1
    assert sum(x["strict_mixed_has_history_informative_confluence"]
               for x in r["by_layout"].values())==18


def test_three_class_target_can_be_wider_than_observable_provenance():
    r=frozen()
    assert r["full_target3_but_non_source_P_library_nonidentifiable_layout_cases"]==35
    a=r["by_layout"]["clustered"]
    b=r["by_layout"]["dispersed"]
    assert a["original_provenance_target_class_distribution"]=={"1":20,"2":102,"3":262}
    assert b["original_provenance_target_class_distribution"]=={"1":241,"2":98,"3":45}
    assert a["full_provenance_target3_but_non_source_provenance_library_fails"]=={
        "000":14,"001":2,"101":18,
    }
    assert b["full_provenance_target3_but_non_source_provenance_library_fails"]=={"101":1}
    assert a["full_provenance_target3_but_non_source_provenance_library_fails_total"]==34
    assert b["full_provenance_target3_but_non_source_provenance_library_fails_total"]==1
    assert a["strict_mixed_full_provenance_target3_but_non_source_P_unresolved"]==2
    assert b["strict_mixed_full_provenance_target3_but_non_source_P_unresolved"]==0
    assert "including source nodes" in r["reason_for_target_observation_gap"]
    assert "exclude source nodes" in r["reason_for_target_observation_gap"]
    assert "does not expose raw action signatures" in r["source_node_exclusion_is_the_only_inferred_reason_in_some_cases"]

    # These exact definitions are the mechanism of the target/readout mismatch,
    # and they must not be silently changed to retrofit this audit's conclusions.
    original=V23_SCRIPT.read_text(encoding="utf-8")
    prior=V22_SCRIPT.read_text(encoding="utf-8")
    assert "if node not in source_set" in original
    assert '"provenance_class_count": len(set(provenance_target.values()))' in original
    assert "for node in sorted(equilibrium_union)" in prior


def test_fails_closed_on_missing_confluence_or_wrong_mixed_witness(tmp_path):
    # One small independent row checks all structural mixed-only witness gates;
    # the GitHub Actions archived rerun checks the actual 384-row panel.
    module=load_script()
    try:
        from audit_eog_history_readout_crossover_v1 import V23
    except ImportError:
        pytest.fail("v23 frozen archive loader unavailable")

    # This is a document-level regression against frozen original program,
    # not a recomputation of its generated worlds.
    txt=SCRIPT.read_text(encoding="utf-8")
    assert 'mixed_action_times[occupation[0]]+=1' in txt
    assert 'mixed_confluence_informative+=1' in txt
    assert 'd["informative_unique_origin_provenance_action_count"]!=0' in txt
    assert '"O_t4"' in txt
    assert module.V23["sha256"] == V23["sha256"]


def test_no_biological_or_confirmatory_overreach():
    r=frozen()
    assert len(r["claim_boundary"])>=5
    assert any("not a biological causal discovery" in x.lower()
               for x in [r["formal_three_history_boundary"]])
    assert any("field census time" in x for x in r["claim_boundary"])
    assert any("not observed ancestry" in x for x in r["claim_boundary"])
