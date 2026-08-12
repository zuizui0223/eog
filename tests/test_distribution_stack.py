from benchmarks.distribution_model_heldout_benchmark import build_replicated_landscape
from eog import BridgeGraphDeclaration, EOGDistributionConfig
from eog.distribution_stack import EOGStackedFusionConfig, fit_eog_stacked_distribution


def test_cross_fitted_stack_uses_structural_meta_features_on_identifiable_case():
    (
        nodes,
        observed_ids,
        observed_response,
        gate_folds,
        target_ids,
        _target_response,
        _sources,
    ) = build_replicated_landscape(4)
    model = fit_eog_stacked_distribution(
        nodes,
        observed_ids,
        observed_response,
        EOGStackedFusionConfig(
            base_config=EOGDistributionConfig(
                graph_declaration=BridgeGraphDeclaration(max_geographic_km=15.0),
                min_class_count=4,
            ),
            fusion_l2_penalty=1.0,
        ),
        gate_fold_ids=gate_folds,
    )
    prediction = model.predict(target_ids)
    assert model.structural_fusion_present is True
    assert any(index in {1, 2} for index in model.fusion_feature_indices)
    assert prediction.distribution_support.shape == (len(target_ids),)
    assert ((prediction.distribution_support >= 0.0) & (prediction.distribution_support <= 1.0)).all()
