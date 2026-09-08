import numpy as np

from eog.v2.predictive_signature_gate import evaluate_saturated_static_signature
from eog.v2.worldset_contraction_audit import audit_worldset_contraction


def test_blocks_exact_tampa_like_saturated_static_injective_signature():
    features = np.asarray(
        [
            [0.1, 0.9], [0.1, 0.9],
            [0.4, 0.6], [0.4, 0.6],
            [0.8, 0.2], [0.8, 0.2],
        ],
        dtype=float,
    )
    audit = audit_worldset_contraction(5, [5, 5, 5])
    result = evaluate_saturated_static_signature(
        features, ["a", "a", "b", "b", "c", "c"], audit
    )
    assert result.status == "structural_only_spatial_signature"
    assert result.predictive_use_allowed is False
    assert result.worldset_fully_saturated is True
    assert result.all_repeated_entities_static is True
    assert result.entity_signature_injective is True
    assert result.entity_signature_count == 3


def test_dynamic_refresh_prevents_block_even_when_worldset_saturated():
    features = np.asarray(
        [[0.1], [0.2], [0.4], [0.5], [0.8], [0.9]], dtype=float
    )
    audit = audit_worldset_contraction(5, [5, 5, 5])
    result = evaluate_saturated_static_signature(
        features, ["a", "a", "b", "b", "c", "c"], audit
    )
    assert result.predictive_use_allowed is True
    assert result.all_repeated_entities_static is False


def test_worldset_contraction_prevents_saturation_block():
    features = np.asarray(
        [[0.1], [0.1], [0.4], [0.4], [0.8], [0.8]], dtype=float
    )
    audit = audit_worldset_contraction(5, [5, 4, 3])
    result = evaluate_saturated_static_signature(
        features, ["a", "a", "b", "b", "c", "c"], audit
    )
    assert result.predictive_use_allowed is True
    assert result.worldset_fully_saturated is False


def test_shared_static_vector_is_not_identity_signature():
    features = np.asarray(
        [[0.2], [0.2], [0.2], [0.2], [0.7], [0.7]], dtype=float
    )
    audit = audit_worldset_contraction(5, [5, 5, 5])
    result = evaluate_saturated_static_signature(
        features, ["a", "a", "b", "b", "c", "c"], audit
    )
    assert result.predictive_use_allowed is True
    assert result.entity_signature_injective is False
    assert result.entity_signature_count == 2
