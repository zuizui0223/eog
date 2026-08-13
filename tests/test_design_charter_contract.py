from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHARTER = ROOT / "docs/eog_design_charter.md"
SRC = ROOT / "src/eog"

ABSENCE_STATES = (
    "environmentally_unsupported",
    "reachability_limited",
    "surveyed_empty",
    "unsurveyed",
    "unresolved",
)


def _charter_text() -> str:
    return CHARTER.read_text(encoding="utf-8")


def _source_text() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(SRC.glob("*.py"))
    )


def test_charter_declares_the_four_separated_layers() -> None:
    text = _charter_text()
    for layer in (
        "Layer 1 — Environmental-state geometry",
        "Layer 2 — Spatial support topology",
        "Layer 3 — Bridge / reachability inference",
        "Layer 4 — Hypothesis-discriminating survey",
    ):
        assert layer in text
    assert "Can the organism persist at that location?" in text
    assert "Can it be reached from a known population?" in text


def test_charter_lists_the_seven_separated_bridge_quantities() -> None:
    text = _charter_text()
    for quantity in (
        "geographic transition",
        "environmental transition",
        "structural barrier",
        "cumulative path cost",
        "maximum bottleneck",
        "alternative-path redundancy",
        "sampling uncertainty",
    ):
        assert quantity in text


def test_charter_keeps_the_full_absence_taxonomy() -> None:
    text = _charter_text()
    for state in ABSENCE_STATES:
        assert state in text
    assert "Absence is not barrier" in text


def test_charter_keeps_the_admission_checklist_and_prospective_rule() -> None:
    text = _charter_text()
    for check in (
        "Which of the four layers' questions does it belong to?",
        "Does it duplicate the estimand of an existing layer?",
        "Does it conflate suitability with reachability?",
        "Does it conflate spatial correlation with propagation?",
        "Does it conflate absence with sampling gap?",
        "Is it verifiable on held-out empirical data",
        "Can it preserve failure conditions, sensitivity and claim boundary",
    ):
        assert check in text
    assert "prospective development rule" in text
    assert "docs/structural_validation_synthesis.md" in text


def test_charter_is_subordinate_to_frozen_evidence() -> None:
    text = _charter_text()
    assert "design document, not a result document" in text
    assert "the frozen contract wins" in text
    for reference in (
        "docs/evidence_ledger.md",
        "manuscript/submission/novelty_claim_matrix.md",
    ):
        assert reference in text


def test_charter_forbids_overclaiming_against_existing_methods() -> None:
    text = _charter_text()
    assert "SDMs do not handle dispersal" in text
    assert "forbidden framings" in text


def test_recorded_gap_absence_taxonomy_is_not_enforced_in_inference() -> None:
    """The charter records the absence taxonomy as present in I/O but not in inference.

    v2 separates surveyed, current-occurrence, historical and unsurveyed states in its
    simulator and validation I/O. The gap is that the propagation operator does not
    reason over them. If a node-state type reaches the operator, this test must fail so
    that the conformance table is updated in the same change rather than drifting.
    """
    operator = (SRC / "dynamic_island_reachability.py").read_text(encoding="utf-8")
    for state in ("unsurveyed", "surveyed_empty", "surveyed_absent", "historical_occurrence"):
        assert state not in operator, (
            f"node state {state!r} now reaches the propagation operator; "
            "update the conformance table in docs/eog_design_charter.md"
        )
    charter = _charter_text()
    assert "The absence taxonomy is not enforced in inference" in charter


def test_recorded_gap_sampling_uncertainty_absent_from_bridge_inference() -> None:
    """Section 2 requires sampling uncertainty as a separate Layer 3 estimand."""
    module = ast.parse((SRC / "bridge.py").read_text(encoding="utf-8"))
    inference = next(
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == "BridgeInference"
    )
    fields = {
        node.target.id
        for node in inference.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }
    assert "sampling_uncertainty" not in fields, (
        "BridgeInference now carries sampling uncertainty; "
        "update the conformance table in docs/eog_design_charter.md"
    )
    assert "sampling uncertainty is not carried as a per-pair estimand" in _charter_text()


def test_structural_layers_never_fit_the_support_field() -> None:
    """Layers 2-4 consume a frozen support field; they must not fit one."""
    for name in (
        "support_topology.py",
        "island_reachability.py",
        "conditional_reachability.py",
        "bridge.py",
        "hypothesis_discrimination.py",
    ):
        module = ast.parse((SRC / name).read_text(encoding="utf-8"))
        defined = {
            node.name
            for node in ast.walk(module)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        offending = {
            item
            for item in defined
            if item.startswith("fit_") or item.startswith("predict_")
        }
        assert not offending, f"{name} defines support-fitting entry points {offending}"
