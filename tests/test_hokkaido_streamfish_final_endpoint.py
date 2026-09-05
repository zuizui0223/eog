import copy

import numpy as np
import pytest

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
    summarize_first_passage,
)
from validation.hokkaido_streamfish_endpoint3.final_endpoint import (
    FinalEndpointTerminal,
    _validate_frozen_declaration,
    layer_b_for_occurrences,
    parse_response_table,
    precompute_cumulative_hitting,
    training_occurrence_set,
)
from validation.hokkaido_streamfish_endpoint3.pre_response_geometry import git_blob_sha1
from validation.hokkaido_streamfish_endpoint3.final_endpoint import load_contracts


def test_frozen_declaration_fingerprints_rederive_exactly():
    _, _, declaration = load_contracts()
    _validate_frozen_declaration(declaration)
    paired = declaration["paired_complementarity"]
    assert paired["expected_outer_unit_count"] == 5
    assert paired["favorable_min_augmented_wins"] == 4
    assert paired["adverse_min_baseline_wins"] == 4
    assert paired["tie_tolerance"] == 0.0


def test_batch_first_passage_matches_existing_target_specific_operator():
    node_ids = ("a", "b", "c", "d")
    edges = [
        DynamicReachabilityEdge(0, 1, geographic_support=1.0),
        DynamicReachabilityEdge(1, 0, geographic_support=1.0),
        DynamicReachabilityEdge(1, 2, geographic_support=1.0),
        DynamicReachabilityEdge(2, 1, geographic_support=1.0),
        DynamicReachabilityEdge(2, 3, geographic_support=1.0),
        DynamicReachabilityEdge(3, 2, geographic_support=1.0),
    ]
    operator = build_dynamic_transition_operator(node_ids, edges, loss_support=1.0)
    history = precompute_cumulative_hitting(operator, max_steps=5)
    for source_index, source_id in enumerate(node_ids):
        for target_index, target_id in enumerate(node_ids):
            summary = summarize_first_passage(
                operator,
                [source_id],
                target_id,
                max_steps=5,
                support_tolerance=0.0,
            )
            np.testing.assert_allclose(
                history[:, source_index, target_index],
                summary.cumulative_support,
                rtol=0.0,
                atol=1e-15,
            )


def test_training_occurrence_set_is_self_excluded_for_positive_and_noop_for_negative():
    node_ids = ("a1", "a2", "a3", "a4")
    full_positive = ("a1", "a3")
    assert training_occurrence_set(full_positive, "a1", node_ids) == ("a3",)
    assert training_occurrence_set(full_positive, "a2", node_ids) == full_positive


def _synthetic_nodes():
    return [
        {"site_id": "alpha1", "river": "alpha", "site_integer": 1},
        {"site_id": "alpha2", "river": "alpha", "site_integer": 2},
        {"site_id": "alpha3", "river": "alpha", "site_integer": 3},
        {"site_id": "alpha4", "river": "alpha", "site_integer": 4},
    ]


def test_layer_b_projection_uses_unchanged_ten_feature_interface():
    nodes = _synthetic_nodes()
    node_ids = tuple(row["site_id"] for row in nodes)
    local_edges = [
        DynamicReachabilityEdge(0, 1, geographic_support=1.0),
        DynamicReachabilityEdge(1, 0, geographic_support=1.0),
        DynamicReachabilityEdge(1, 2, geographic_support=1.0),
        DynamicReachabilityEdge(2, 1, geographic_support=1.0),
        DynamicReachabilityEdge(2, 3, geographic_support=1.0),
        DynamicReachabilityEdge(3, 2, geographic_support=1.0),
    ]
    complete_edges = [
        DynamicReachabilityEdge(i, j, geographic_support=1.0)
        for i in range(4)
        for j in range(4)
        if i != j
    ]
    operators = {
        "local": build_dynamic_transition_operator(node_ids, local_edges, loss_support=1.0),
        "external_open": build_dynamic_transition_operator(node_ids, complete_edges, loss_support=1.0),
    }
    histories = {
        key: precompute_cumulative_hitting(value, max_steps=3)
        for key, value in operators.items()
    }
    _, final_contract, _ = load_contracts()
    small_contract = copy.deepcopy(final_contract)
    small_contract["worlds"]["max_steps"] = 3
    small_contract["worlds"]["support_tolerance"] = 0.0
    matrix, audit = layer_b_for_occurrences(
        ("alpha1", "alpha3"),
        nodes=nodes,
        operators=operators,
        hitting_history=histories,
        final_contract=small_contract,
    )
    assert matrix.shape == (4, 10)
    assert np.isfinite(matrix).all()
    assert audit["source_ids"] == ["alpha1"]
    assert audit["compatibility_target_ids"] == ["alpha3"]
    assert "external_open" in audit["compatible_world_ids"]


def _response_fixture():
    header = "year,river,site,pass,area,area_unit,latin,abundance,family,genus,c_name\n"
    rows = [
        "1999,alpha,1,1,10,m2,Noemacheilus_barbatulus,2,Nemacheilidae,Noemacheilus,loach\n",
        "2000,alpha,1,2,10,m2,Other_species,1,Other,Other,other\n",
        "1999,alpha,2,1,10,m2,Other_species,4,Other,Other,other\n",
        "1999,alpha,3,1,10,m2,Noemacheilus_barbatulus,NA,Nemacheilidae,Noemacheilus,loach\n",
    ]
    return (header + "".join(rows)).encode("utf-8")


def test_response_parser_constructs_ever_detection_and_accepts_frozen_missing_abundance():
    source_contract, final_contract, _ = load_contracts()
    final = copy.deepcopy(final_contract)
    payload = _response_fixture()
    final["source"]["response_table"]["size_bytes"] = len(payload)
    final["source"]["response_table"]["git_blob_sha1"] = git_blob_sha1(payload)
    nodes = [
        {"site_id": "alpha1"},
        {"site_id": "alpha2"},
        {"site_id": "alpha3"},
    ]
    labels, audit = parse_response_table(
        payload,
        nodes,
        (),
        source_contract,
        final,
    )
    assert labels == {"alpha1": 1, "alpha2": 0, "alpha3": 0}
    assert audit["positive_node_count"] == 1
    assert audit["negative_node_count"] == 2
    assert audit["missing_abundance_rows"] == 1


def test_response_parser_fails_closed_on_unknown_site_and_invalid_abundance():
    source_contract, final_contract, _ = load_contracts()
    nodes = [{"site_id": "alpha1"}]
    bad_site = (
        "year,river,site,pass,area,area_unit,latin,abundance,family,genus,c_name\n"
        "1999,beta,9,1,10,m2,Noemacheilus_barbatulus,1,Nemacheilidae,Noemacheilus,loach\n"
    ).encode("utf-8")
    final = copy.deepcopy(final_contract)
    final["source"]["response_table"]["size_bytes"] = len(bad_site)
    final["source"]["response_table"]["git_blob_sha1"] = git_blob_sha1(bad_site)
    with pytest.raises(FinalEndpointTerminal, match="outside the frozen 129-site registry"):
        parse_response_table(bad_site, nodes, (), source_contract, final)

    bad_abundance = (
        "year,river,site,pass,area,area_unit,latin,abundance,family,genus,c_name\n"
        "1999,alpha,1,1,10,m2,Noemacheilus_barbatulus,-1,Nemacheilidae,Noemacheilus,loach\n"
    ).encode("utf-8")
    final["source"]["response_table"]["size_bytes"] = len(bad_abundance)
    final["source"]["response_table"]["git_blob_sha1"] = git_blob_sha1(bad_abundance)
    with pytest.raises(FinalEndpointTerminal, match="finite and non-negative"):
        parse_response_table(bad_abundance, nodes, (), source_contract, final)
