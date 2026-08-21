from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from pathlib import Path

from audit_giant_kelp_process_mapping import download

ROOT = Path("validation/giant_kelp_complementarity")
OUT = Path("build/giant_kelp_patch_identity")


def integer_like(token: str) -> str | None:
    value = token.strip()
    if not re.fullmatch(r"[+-]?[0-9]+(?:\.0+)?", value):
        return None
    try:
        number = Decimal(value)
    except InvalidOperation:
        return None
    if number != number.to_integral_value():
        return None
    return str(int(number))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    process_contract = json.loads((ROOT / "process_object_contract.json").read_text(encoding="utf-8"))
    geometry_contract = json.loads((ROOT / "southern_geometry_object_contract.json").read_text(encoding="utf-8"))
    process = process_contract["process_entity"]
    geometry = geometry_contract["southern_geometry_entity"]
    transport: list[dict] = []

    geometry_path = download(
        geometry["data_pid"], int(geometry["size_bytes"]), geometry["checksum"], "giant_kelp_geometry_identity", transport
    )
    process_path = download(
        process["data_pid"], int(process["size_bytes"]), process["checksum"], "giant_kelp_process_identity", transport
    )

    geometry_ids: set[str] = set()
    with geometry_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            geometry_ids.add(str(row["patch_number"]).strip())

    source_ids: set[str] = set()
    destination_ids: set[str] = set()
    with process_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            source_ids.add(str(row["source_patch"]).strip())
            destination_ids.add(str(row["destination_patch"]).strip())
    process_ids = source_ids | destination_ids

    def normalized(values: set[str]) -> tuple[set[str], dict[str, list[str]], list[str]]:
        mapping: dict[str, list[str]] = {}
        non_numeric: list[str] = []
        for raw in sorted(values):
            norm = integer_like(raw)
            if norm is None:
                non_numeric.append(raw)
            else:
                mapping.setdefault(norm, []).append(raw)
        return set(mapping), mapping, non_numeric

    geom_norm, geom_map, geom_non_numeric = normalized(geometry_ids)
    proc_norm, proc_map, proc_non_numeric = normalized(process_ids)
    geom_collisions = {key: vals for key, vals in geom_map.items() if len(vals) > 1}
    proc_collisions = {key: vals for key, vals in proc_map.items() if len(vals) > 1}
    bijective_integer_equivalence = bool(
        not geom_non_numeric
        and not proc_non_numeric
        and not geom_collisions
        and not proc_collisions
        and geom_norm == proc_norm
        and len(geometry_ids) == len(geom_norm)
        and len(process_ids) == len(proc_norm)
    )

    payload = {
        "status": "nonresponse_patch_identity_diagnostic_complete",
        "geometry_raw_count": len(geometry_ids),
        "process_source_raw_count": len(source_ids),
        "process_destination_raw_count": len(destination_ids),
        "process_union_raw_count": len(process_ids),
        "raw_source_subset_geometry": source_ids <= geometry_ids,
        "raw_destination_subset_geometry": destination_ids <= geometry_ids,
        "raw_union_equals_geometry": process_ids == geometry_ids,
        "raw_geometry_sample": sorted(geometry_ids)[:30],
        "raw_process_sample": sorted(process_ids)[:30],
        "raw_geometry_only_sample": sorted(geometry_ids - process_ids)[:30],
        "raw_process_only_sample": sorted(process_ids - geometry_ids)[:30],
        "integer_normalized_geometry_count": len(geom_norm),
        "integer_normalized_process_count": len(proc_norm),
        "integer_normalized_sets_equal": geom_norm == proc_norm,
        "geometry_integer_normalization_collisions": geom_collisions,
        "process_integer_normalization_collisions": proc_collisions,
        "geometry_non_integer_like_sample": geom_non_numeric[:30],
        "process_non_integer_like_sample": proc_non_numeric[:30],
        "bijective_integer_representation_equivalence": bijective_integer_equivalence,
        "geometry_representation_examples": [
            {"canonical": key, "raw": geom_map[key]} for key in sorted(geom_map, key=lambda x: int(x))[:20]
        ],
        "process_representation_examples": [
            {"canonical": key, "raw": proc_map[key]} for key in sorted(proc_map, key=lambda x: int(x))[:20]
        ],
        "geometry_object_bytes_opened": True,
        "process_object_bytes_opened": True,
        "response_package_bytes_opened": False,
        "response_rows_opened": False,
        "transport": transport,
        "interpretation": (
            "A one-to-one integer-value representation mapping exists between the two frozen non-response sources; topology and node cardinality would be unchanged by freezing canonical integer node IDs before response access."
            if bijective_integer_equivalence
            else "No one-to-one integer-value representation equivalence is established; do not repair patch IDs or open response."
        ),
    }
    payload["fingerprint"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    (OUT / "patch_identity_diagnostic.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
