from pathlib import Path


LEGACY_FROZEN_WORKFLOWS = (
    "real-taxon-pilot.yml",
    "robustness-audit.yml",
    "persistent-split.yml",
    "core-local-bridge.yml",
    "real-taxon-mode-audit.yml",
    "multiaxial-archetypes.yml",
    "null-family-comparison.yml",
    "mode-separation-comparators.yml",
    "core-local-bridge-confirmation.yml",
    "calibrated-gap-feature-selection.yml",
)

PROSPECTIVE_CONFIRMATION_WORKFLOWS = (
    "traversability-confirmation.yml",
    "occurrence-rule-compatibility-confirmation.yml",
    "directional-evidence-confirmation.yml",
)


def test_frozen_legacy_workflows_do_not_watch_all_eog_source_files():
    root = Path(".github/workflows")
    for name in LEGACY_FROZEN_WORKFLOWS:
        text = (root / name).read_text()
        assert '"src/eog/**"' not in text, name
        assert "workflow_dispatch:" in text, name


def test_ci_scope_policy_names_every_guarded_legacy_workflow():
    policy = Path("docs/ci_scope_policy.md").read_text()
    for name in LEGACY_FROZEN_WORKFLOWS:
        assert f"`{name}`" in policy


def test_prospective_scientific_confirmations_do_not_watch_facade_only_changes():
    root = Path(".github/workflows")
    for name in PROSPECTIVE_CONFIRMATION_WORKFLOWS:
        text = (root / name).read_text()
        assert '"src/eog/v2/**"' not in text, name
        assert '"src/eog/v2/__init__.py"' not in text, name
        assert "workflow_dispatch:" in text, name
