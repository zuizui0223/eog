import csv
import json
import runpy
from pathlib import Path

import pytest


_NODES = runpy.run_path("benchmarks/freeze_sivflora_nodes.py")
_WORLDS = runpy.run_path("benchmarks/freeze_sivflora_world_universe.py")
parse_dms = _NODES["parse_dms"]
freeze_worlds = _WORLDS["freeze_worlds"]


def test_parse_dms_handles_frozen_sivflora_styles():
    assert parse_dms("37°49'S", latitude=True) == pytest.approx(-(37 + 49 / 60))
    assert parse_dms("178°45′58″E", latitude=False) == pytest.approx(178 + 45 / 60 + 58 / 3600)
    assert parse_dms("53°03’S", latitude=True) == pytest.approx(-(53 + 3 / 60))
    assert parse_dms("\u00a064°15′W", latitude=False) == pytest.approx(-(64 + 15 / 60))


def test_parse_dms_rejects_wrong_hemisphere():
    with pytest.raises(ValueError, match="latitude has invalid hemisphere"):
        parse_dms("37°49'E", latitude=True)


def test_world_freeze_builds_exactly_twenty_response_blind_worlds(tmp_path: Path):
    climate = tmp_path / "climate.csv"
    fields = [
        "island_id", "acronym", "node_name", "latitude", "longitude",
        *[f"chelsa_bio{i}" for i in (1, 5, 6, 12, 15)],
        *[f"worldclim_bio{i}" for i in (1, 5, 6, 12, 15)],
    ]
    rows = []
    for i in range(1, 23):
        row = {
            "island_id": str(i),
            "acronym": f"N{i:02d}",
            "node_name": f"node-{i:02d}",
            "latitude": str(-30.0 - i),
            "longitude": str(-150.0 + 12.0 * i),
        }
        for variable in (1, 5, 6, 12, 15):
            row[f"chelsa_bio{variable}"] = str(i * (variable + 1) + (i % 3))
            row[f"worldclim_bio{variable}"] = str(i * (variable + 2) + (i % 5))
        rows.append(row)
    with climate.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    worlds_json = tmp_path / "worlds.json"
    manifest_json = tmp_path / "manifest.json"
    result = freeze_worlds(climate, worlds_json, manifest_json)
    payload = json.loads(worlds_json.read_text())

    assert result["world_count"] == 20
    assert payload["world_count"] == 20
    assert len({world["world_id"] for world in payload["worlds"]}) == 20
    assert sum(world["family"] == "geography_only" for world in payload["worlds"]) == 4
    assert sum(str(world["family"]).startswith("chelsa_") for world in payload["worlds"]) == 8
    assert sum(str(world["family"]).startswith("worldclim_") for world in payload["worlds"]) == 8
    assert payload["species_incidence_used"] is False
    assert payload["heldout_outcomes_scored"] is False
