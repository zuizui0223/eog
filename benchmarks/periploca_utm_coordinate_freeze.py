"""Freeze Periploca WGS84 coordinates from the response-free compact UTM rows.

The admissible scale is selected only from the predeclared {1,10,100} family and only
with geographic UTM/latitude-band constraints.  No genetic input is accepted.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path

from pyproj import Transformer

EXPECTED_UTM_ROWS_FINGERPRINT = "01ebd21add5c912c9420807c68229f76a8fb0f5f2fa0b59158911802322e915a"
EXPECTED_GEOGRAPHY_SHA256 = "d54af743f39332aab753964ee0d6950550097d7b29216d155a50967153d5d233"
SCALE_CANDIDATES = (1, 10, 100)
BANDS = "CDEFGHJKLMNPQRSTUVWX"
CANARY_REGIONS = (
    "Lanzarote",
    "Fuerteventura",
    "Gran Canaria",
    "Tenerife",
    "La Gomera",
    "La Palma",
    "El Hierro",
)
EXPECTED_CANARY_CODES = (
    "FAM", "COF", "CAR", "GUA", "BAN", "AMA", "CHO", "GUI", "ANA", "PHI",
    "HER", "RAS", "TEN", "BVI", "VAL", "ARG", "TIM", "FAG", "SAB", "RES",
)
UTM_RE = re.compile(r"^(\d{1,2})([C-HJ-NP-X])\s+(\d+)\s+(\d+)$")


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _band_range(letter: str) -> tuple[float, float]:
    index = BANDS.index(letter)
    lower = -80.0 + 8.0 * index
    upper = 84.0 if letter == "X" else lower + 8.0
    return lower, upper


def _central_meridian(zone: int) -> float:
    return zone * 6.0 - 183.0


def _parse_utm(value: str) -> tuple[int, str, float, float]:
    match = UTM_RE.fullmatch(value.strip())
    if match is None:
        raise ValueError(f"unexpected compact UTM syntax: {value!r}")
    return int(match.group(1)), match.group(2), float(match.group(3)), float(match.group(4))


def _evaluate_scale(rows: list[dict[str, object]], scale: int) -> dict[str, object]:
    converted: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    for row in rows:
        zone, band, raw_easting, raw_northing = _parse_utm(str(row["utm"]))
        easting = raw_easting * scale
        northing = raw_northing * scale
        population = str(row["population"])
        if not 100000.0 <= easting <= 900000.0:
            failures.append({"population": population, "reason": "easting_range", "value": easting})
            continue
        if not 0.0 <= northing <= 10000000.0:
            failures.append({"population": population, "reason": "northing_range", "value": northing})
            continue
        northern = BANDS.index(band) >= BANDS.index("N")
        epsg = (32600 if northern else 32700) + zone
        longitude, latitude = Transformer.from_crs(epsg, 4326, always_xy=True).transform(easting, northing)
        if not (math.isfinite(longitude) and math.isfinite(latitude)):
            failures.append({"population": population, "reason": "nonfinite_wgs84"})
            continue
        central = _central_meridian(zone)
        if not central - 3.25 <= longitude <= central + 3.25:
            failures.append(
                {"population": population, "reason": "longitude_zone", "longitude": longitude, "central": central}
            )
            continue
        lower, upper = _band_range(band)
        if not lower - 0.25 <= latitude <= upper + 0.25:
            failures.append(
                {"population": population, "reason": "latitude_band", "latitude": latitude, "lower": lower, "upper": upper}
            )
            continue
        converted.append(
            {
                "row": int(row["row"]),
                "island_region": str(row["island_region"]),
                "population": population,
                "released_utm": str(row["utm"]),
                "utm_zone": zone,
                "utm_band": band,
                "easting_m": easting,
                "northing_m": northing,
                "latitude": latitude,
                "longitude": longitude,
            }
        )
    return {
        "scale": scale,
        "admissible": len(failures) == 0 and len(converted) == len(rows),
        "n_converted": len(converted),
        "n_failures": len(failures),
        "failure_examples": failures[:12],
        "converted": converted,
    }


def freeze(utm_rows_path: Path) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    source = json.loads(utm_rows_path.read_text(encoding="utf-8"))
    if source.get("fingerprint") != EXPECTED_UTM_ROWS_FINGERPRINT:
        raise ValueError("Periploca response-free UTM-row fingerprint drifted")
    if source.get("geography_sha256") != EXPECTED_GEOGRAPHY_SHA256:
        raise ValueError("Periploca response-free geography SHA drifted")
    if source.get("genetic_contents_accessed") is not False:
        raise ValueError("Periploca UTM-row source is not response-free")
    rows = list(source.get("rows") or [])
    if len(rows) != 33 or len({str(row["population"]) for row in rows}) != 33:
        raise ValueError("Periploca UTM-row source must contain exactly 33 unique populations")

    screens = [_evaluate_scale(rows, scale) for scale in SCALE_CANDIDATES]
    admissible = [screen for screen in screens if bool(screen["admissible"])]
    if len(admissible) != 1:
        raise RuntimeError(f"non_estimable_utm_scale_ambiguous: surviving scales={[s['scale'] for s in admissible]}")
    selected = admissible[0]
    all_coordinates = list(selected["converted"])
    if len(all_coordinates) != 33:
        raise RuntimeError("Periploca coordinate freeze lost populations")

    canary = [row for row in all_coordinates if row["island_region"] in CANARY_REGIONS]
    if tuple(row["population"] for row in canary) != EXPECTED_CANARY_CODES:
        raise RuntimeError("Periploca Canary subset differs from the frozen geography-only rule")

    coordinate_payload = [
        {
            "population": row["population"],
            "island_region": row["island_region"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
        }
        for row in all_coordinates
    ]
    canary_payload = [
        {
            "population": row["population"],
            "island_region": row["island_region"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
        }
        for row in canary
    ]
    manifest: dict[str, object] = {
        "status": "periploca-response-free-coordinate-freeze",
        "utm_rows_fingerprint": EXPECTED_UTM_ROWS_FINGERPRINT,
        "geography_sha256": EXPECTED_GEOGRAPHY_SHA256,
        "scale_candidates": list(SCALE_CANDIDATES),
        "scale_screens": [
            {key: value for key, value in screen.items() if key != "converted"}
            for screen in screens
        ],
        "selected_multiplier": int(selected["scale"]),
        "n_populations": len(all_coordinates),
        "n_canary_populations": len(canary),
        "canary_population_codes": [row["population"] for row in canary],
        "coordinate_fingerprint": _canonical_sha256(coordinate_payload),
        "canary_coordinate_fingerprint": _canonical_sha256(canary_payload),
        "genetic_contents_accessed": False,
        "genetic_response_computed": False,
        "claim_boundary": (
            "Coordinates are derived only from the released response-free compact UTM strings under the predeclared "
            "1/10/100 scale screen. The primary subset is the geography-only 20-population Canary Archipelago rule."
        ),
    }
    manifest["fingerprint"] = _canonical_sha256(manifest)
    return manifest, all_coordinates, canary


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "row", "island_region", "population", "released_utm", "utm_zone", "utm_band",
        "easting_m", "northing_m", "latitude", "longitude",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--utm-rows", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--all-coordinates", type=Path, required=True)
    parser.add_argument("--canary-coordinates", type=Path, required=True)
    args = parser.parse_args()
    manifest, all_coordinates, canary = freeze(args.utm_rows)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    _write_csv(args.all_coordinates, all_coordinates)
    _write_csv(args.canary_coordinates, canary)
    print(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
