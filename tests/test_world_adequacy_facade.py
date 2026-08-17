import eog.v2.reachability as reachability
import eog.v2.validation as validation


def test_world_structural_adequacy_belongs_to_validation_facade():
    for name in (
        "StructuralAdequacyDeclaration",
        "WorldStructuralAudit",
        "WorldUniverseStructuralAudit",
        "WorldUniverseStructuralGate",
        "audit_world_universe_structure",
        "apply_structural_adequacy_gate",
    ):
        assert hasattr(validation, name)
        assert not hasattr(reachability, name)
