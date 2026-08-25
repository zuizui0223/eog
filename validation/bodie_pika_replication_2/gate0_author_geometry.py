from __future__ import annotations

import hashlib
import json
import math
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "build" / "bodie_pika_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)

EXPECTED_N = 82
AUTHOR_REPO = "eastonwhite/BodiePikaMetapop"
AUTHOR_REF = "master"
FILES = {
    "patch_coordinates": {
        "path": "Scripts/patch_coordinates.txt",
        "git_blob_sha": "ff0395777cb35bbe1364d12b8cb967c5fa0f9d91",
    },
    "inter_patch_distances": {
        "path": "Scripts/inter_patch_distances.txt",
        "git_blob_sha": "b04f3c56a347b79ab3f9db866449355f446fc1c3",
    },
}


def get_raw(path: str) -> bytes:
    url = f"https://raw.githubusercontent.com/{AUTHOR_REPO}/{AUTHOR_REF}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "EOG-Bodie-Author-Geometry-Audit/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def canonical_sha256(obj) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def parse_coordinates(data: bytes):
    text = data.decode("utf-8-sig").strip()
    lines = [x for x in text.splitlines() if x.strip()]
    header = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        vals = line.split("\t")
        if len(vals) != 2:
            raise RuntimeError(f"coordinate row has {len(vals)} fields")
        x, y = map(float, vals)
        if not (math.isfinite(x) and math.isfinite(y)):
            raise RuntimeError("non-finite coordinate")
        rows.append((x, y))
    return header, rows


def parse_matrix(data: bytes):
    text = data.decode("utf-8-sig").strip()
    matrix = []
    for line in text.splitlines():
        if not line.strip():
            continue
        row = [float(v) for v in line.split("\t") if v != ""]
        if not all(math.isfinite(v) for v in row):
            raise RuntimeError("non-finite distance")
        matrix.append(row)
    n = len(matrix)
    widths = sorted(set(len(r) for r in matrix))
    square = widths == [n]
    symmetric = square and all(abs(matrix[i][j] - matrix[j][i]) <= 1e-6 for i in range(n) for j in range(n))
    diagonal_zero = square and all(abs(matrix[i][i]) <= 1e-9 for i in range(n))
    return matrix, widths, square, symmetric, diagonal_zero


def main():
    result = {
        "schema": "eog.bodie_pika_replication_2.author_geometry_gate.v1",
        "attempt_id": "bodie_pika_terrestrial_fragmented_fresh_paired_v1",
        "frozen_expected_patch_count": EXPECTED_N,
        "author_repo": AUTHOR_REPO,
        "author_ref": AUTHOR_REF,
        "source_files": {},
        "geometry": {},
        "response_firewall": {
            "census_payload_requests": 0,
            "census_payload_bytes_opened": 0,
            "census_header_bytes_opened": 0,
            "census_sheet_names_opened": False,
            "census_rows_opened": False,
            "census_values_opened": False,
            "scientific_model_fits": 0,
            "heldout_scores": 0,
        },
    }

    coord_data = None
    dist_data = None
    for key, spec in FILES.items():
        data = get_raw(spec["path"])
        actual_blob = git_blob_sha(data)
        if actual_blob != spec["git_blob_sha"]:
            raise RuntimeError(f"Git blob mismatch for {spec['path']}: {actual_blob} != {spec['git_blob_sha']}")
        result["source_files"][key] = {
            "path": spec["path"],
            "bytes": len(data),
            "git_blob_sha": actual_blob,
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        if key == "patch_coordinates":
            coord_data = data
        else:
            dist_data = data

    header, coords = parse_coordinates(coord_data)
    matrix, widths, square, symmetric, diagonal_zero = parse_matrix(dist_data)
    result["geometry"] = {
        "coordinate_header": header,
        "coordinate_row_count": len(coords),
        "coordinate_unique_pair_count": len(set(coords)),
        "distance_matrix_row_count": len(matrix),
        "distance_matrix_column_widths": widths,
        "distance_matrix_square": square,
        "distance_matrix_symmetric": symmetric,
        "distance_matrix_diagonal_zero": diagonal_zero,
        "coordinate_and_matrix_counts_match": len(coords) == len(matrix),
        "registry_fingerprint_ordered_coordinates": canonical_sha256(coords),
    }

    if (
        len(coords) == EXPECTED_N
        and len(set(coords)) == EXPECTED_N
        and len(matrix) == EXPECTED_N
        and square and symmetric and diagonal_zero
    ):
        result["status"] = "gate0_pass_author_geometry_matches_frozen_universe"
        result["reason"] = "author-released response-independent geometry exactly reproduces frozen 82-patch universe"
    else:
        result["status"] = "stop_response_independent_complete_geometry_not_found"
        result["reason"] = (
            "author-released response-independent geometry is internally coherent but does not reproduce the prospectively frozen "
            f"{EXPECTED_N}-patch census universe; no patch-count weakening or census-derived repair is permitted"
        )

    result["fingerprint"] = canonical_sha256({k: v for k, v in result.items() if k != "fingerprint"})
    out = BUILD / "author_geometry_gate.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
