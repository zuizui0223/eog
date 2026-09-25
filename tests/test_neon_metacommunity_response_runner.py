from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = (
    ROOT
    / "validation"
    / "neon_metacommunity_connectivity_v1"
    / "run_response_once.py"
)

spec = importlib.util.spec_from_file_location("neon_meta_response_runner", RUNNER)
assert spec is not None and spec.loader is not None
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_species_response_parser_separates_x_unknown_and_regular_nodes():
    raw = (
        "namedLocation,trapCoordinate,trapStatus,taxonID\n"
        "JORN_001.mammalGrid.mam,A1,1 - capture,TARGET\n"
        "JORN_001.mammalGrid.mam,XX,1 - capture,TARGET\n"
        "JORN_001.mammalGrid.mam,A2,0 - no capture,TARGET\n"
        "JORN_001.mammalGrid.mam,Z9,1 - capture,TARGET\n"
        "JORN_001.mammalGrid.mam,A1,1 - capture,OTHER\n"
    ).encode()

    geometries = {
        "JORN": {
            "node_ids": (
                "JORN_001.mammalGrid.mam.A1",
                "JORN_001.mammalGrid.mam.A2",
            )
        }
    }
    species_by_node = {"JORN": {}}
    unknown = {"JORN": set()}
    x_nodes = {"JORN": set()}
    counters = {
        "JORN": {
            "rows": 0,
            "target_capture_rows": 0,
            "x_excluded_rows": 0,
        }
    }

    runner.parse_response_file(
        raw,
        {"site_code": "JORN", "name": "fake.csv"},
        target_taxa={"TARGET"},
        geometries=geometries,
        species_by_node=species_by_node,
        unknown_non_x=unknown,
        x_positive_nodes=x_nodes,
        counters_by_site=counters,
    )

    assert species_by_node["JORN"] == {
        "JORN_001.mammalGrid.mam.A1": {"TARGET"}
    }
    assert x_nodes["JORN"] == {"JORN_001.mammalGrid.mam.XX"}
    assert unknown["JORN"] == {"JORN_001.mammalGrid.mam.Z9"}
    assert counters["JORN"]["rows"] == 5
    assert counters["JORN"]["target_capture_rows"] == 3
    assert counters["JORN"]["x_excluded_rows"] == 1


def test_response_inventory_keeps_only_pertrapnight_csv():
    payload = {
        "data": {
            "productCode": "DP1.10072.001",
            "releases": [
                {
                    "release": "RELEASE-2026",
                    "packages": [
                        {
                            "siteCode": "JORN",
                            "month": "2025-06",
                            "packageType": "basic",
                            "files": [
                                {
                                    "name": "x.mam_pertrapnight.y.csv",
                                    "md5": "0" * 32,
                                    "url": "https://example.org/a.csv",
                                    "size": 10,
                                },
                                {
                                    "name": "x.mam_perplotnight.y.csv",
                                    "md5": "1" * 32,
                                    "url": "https://example.org/b.csv",
                                    "size": 10,
                                },
                            ],
                        }
                    ],
                }
            ],
        }
    }
    rows = runner.response_inventory(payload, ("JORN",))
    assert len(rows) == 1
    assert rows[0]["name"] == "x.mam_pertrapnight.y.csv"


def test_geolocatable_trap_rule_excludes_any_x_coordinate():
    assert runner.is_geolocatable_trap(
        "JORN", "JORN_001.mammalGrid.mam.A1"
    )
    assert not runner.is_geolocatable_trap(
        "JORN", "JORN_001.mammalGrid.mam.XX"
    )
    assert not runner.is_geolocatable_trap(
        "JORN", "JORN_001.mammalGrid.mam.JX"
    )
