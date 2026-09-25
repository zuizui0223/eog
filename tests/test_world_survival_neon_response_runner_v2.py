from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = (
    ROOT
    / "validation"
    / "world_survival_regime_v2"
    / "run_neon_small_mammal_response_once_v2_2.py"
)

spec = importlib.util.spec_from_file_location("neon_response_v2_2_runner", RUNNER_PATH)
assert spec is not None and spec.loader is not None
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_response_inventory_selects_only_frozen_pertrapnight_csv():
    payload = {
        "data": {
            "productCode": "DP1.10072.001",
            "siteCodes": ["ABBY"],
            "releases": [
                {
                    "release": "RELEASE-2026",
                    "packages": [
                        {
                            "siteCode": "ABBY",
                            "month": "2024-06",
                            "packageType": "basic",
                            "files": [
                                {
                                    "name": "NEON.D01.ABBY.DP1.10072.001.mam_pertrapnight.2024-06.basic.20260201T000000Z.csv",
                                    "size": 123,
                                    "md5": "0" * 32,
                                    "url": "https://example.org/pertrap.csv",
                                },
                                {
                                    "name": "NEON.D01.ABBY.DP1.10072.001.mam_perplotnight.2024-06.basic.20260201T000000Z.csv",
                                    "size": 45,
                                    "md5": "1" * 32,
                                    "url": "https://example.org/perplot.csv",
                                },
                            ],
                        }
                    ],
                }
            ],
        }
    }
    rows = runner.response_file_inventory(payload, ("ABBY",))
    assert len(rows) == 1
    assert "mam_pertrapnight" in rows[0]["name"]


def test_response_inventory_rejects_conflicting_duplicate_file_identity():
    base = {
        "name": "NEON.D01.ABBY.DP1.10072.001.mam_pertrapnight.2024-06.basic.csv",
        "size": 123,
        "md5": "0" * 32,
        "url": "https://example.org/a.csv",
    }
    payload = {
        "data": {
            "productCode": "DP1.10072.001",
            "siteCodes": ["ABBY"],
            "releases": [
                {
                    "release": "RELEASE-2026",
                    "packages": [
                        {
                            "siteCode": "ABBY",
                            "month": "2024-06",
                            "packageType": "basic",
                            "files": [
                                base,
                                {**base, "md5": "1" * 32},
                            ],
                        }
                    ],
                }
            ],
        }
    }
    with pytest.raises(RuntimeError, match="conflicting duplicate"):
        runner.response_file_inventory(payload, ("ABBY",))


def test_csv_parser_uses_exact_frozen_columns_and_official_node_join_rule():
    raw = (
        "namedLocation,trapCoordinate,trapStatus,taxonID\n"
        "ABBY_001.mammalGrid.mam,A1,1 - capture,TARGET\n"
        "ABBY_001.mammalGrid.mam,A2,0 - no capture,TARGET\n"
        "ABBY_001.mammalGrid.mam,A3,1 - capture,NONTARGET\n"
    ).encode()
    node_ids = (
        "ABBY_001.mammalGrid.mam.A1",
        "ABBY_001.mammalGrid.mam.A2",
        "ABBY_001.mammalGrid.mam.A3",
    )
    geometries = {"ABBY": {"node_ids": node_ids}}
    positive = {"ABBY": set()}
    unknown = {"ABBY": set()}
    counts = {"ABBY": 0}

    runner.update_positive_nodes(
        raw=raw,
        row={"site_code": "ABBY", "name": "fake.csv"},
        target_taxon_ids={"TARGET"},
        geometries=geometries,
        positive_nodes=positive,
        unknown_positive_nodes=unknown,
        row_counts=counts,
    )

    assert positive["ABBY"] == {"ABBY_001.mammalGrid.mam.A1"}
    assert unknown["ABBY"] == set()
    assert counts["ABBY"] == 3


def test_unknown_target_positive_node_is_not_silently_added():
    raw = (
        "namedLocation,trapCoordinate,trapStatus,taxonID\n"
        "ABBY_001.mammalGrid.mam,Z9,1 - capture,TARGET\n"
    ).encode()
    geometries = {
        "ABBY": {"node_ids": ("ABBY_001.mammalGrid.mam.A1",)}
    }
    positive = {"ABBY": set()}
    unknown = {"ABBY": set()}
    counts = {"ABBY": 0}

    runner.update_positive_nodes(
        raw=raw,
        row={"site_code": "ABBY", "name": "fake.csv"},
        target_taxon_ids={"TARGET"},
        geometries=geometries,
        positive_nodes=positive,
        unknown_positive_nodes=unknown,
        row_counts=counts,
    )

    assert positive["ABBY"] == set()
    assert unknown["ABBY"] == {"ABBY_001.mammalGrid.mam.Z9"}


def test_observed_regime_uses_distinct_canonical_worlds_only():
    node_ids = ("a", "b", "c")
    index = {node: i for i, node in enumerate(node_ids)}

    connecting = np.zeros((3, 3), dtype=bool)
    connecting[0, 1] = connecting[1, 0] = True

    failing = np.zeros((3, 3), dtype=bool)
    failing[1, 2] = failing[2, 1] = True

    geometry = {
        "site_code": "TEST",
        "node_ids": node_ids,
        "node_index": index,
        "canonical_worlds": {
            "canonical_connecting": connecting,
            "canonical_failing": failing,
        },
        "forecast_regime": "contracting",
        "forecast_fraction": 0.5,
        "forecast_fingerprint": "forecast",
        "preparation_fingerprint": "preparation",
        "alias_groups": [
            {
                "canonical_world_id": "canonical_connecting",
                "alias_world_ids": ["canonical_connecting", "duplicate_label"],
                "adjacency_fingerprint": "x",
            },
            {
                "canonical_world_id": "canonical_failing",
                "alias_world_ids": ["canonical_failing"],
                "adjacency_fingerprint": "y",
            },
        ],
    }

    result = runner.observed_site_result(geometry, {"a", "b"})

    assert result["distinct_world_count"] == 2
    assert result["surviving_world_ids"] == ["canonical_connecting"]
    assert result["observed_survival_fraction"] == 0.5
    assert result["observed_regime"] == "contracting"
    assert result["exact_regime_match"] is True


def test_less_than_two_positive_nodes_is_non_estimable_not_falsified():
    geometry = {
        "site_code": "TEST",
        "forecast_regime": "contracting",
        "forecast_fraction": 0.5,
    }
    result = runner.observed_site_result(geometry, {"a"})
    assert result["status"] == "response_consumed_non_estimable_positive_support"
    assert result["counts_as_scored_system"] is False
