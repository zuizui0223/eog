from __future__ import annotations

import binascii
import hashlib
import io
import json
from pathlib import Path
import struct
import urllib.request
import zlib

import numpy as np

from eog.v2.world_scale_ladder import (
    StructuralScaleLadderDeclaration,
    build_structural_scale_ladder,
    structural_scale_adjacencies,
)
from eog.v2.world_adequacy import (
    StructuralAdequacyDeclaration,
    audit_world_universe_structure,
    apply_structural_adequacy_gate,
)

URL = "https://ndownloader.figshare.com/files/36330951"
UA = "eog-response-blind-daphnia-gate1/1.0"
N = 546
TARGETS = (0.25, 0.50, 0.75, 0.90)
HORIZON = 1
MIN_LCC = 0.90
MAX_ISOLATED = 0.05
MIN_DISTINCT = 3
MEMBER = {
    "name": "code_SpatialCoex/Bayesian model fitting/distance.csv",
    "local_header_offset": 9093,
    "compressed_size": 2362738,
    "uncompressed_size": 5235396,
    "crc32": "f5f840c0",
    "sha256": "4ffb62d36b808b18fb999aa1f585e1987d0df76e289543ef43941f2e3037b750",
}
OUT = Path("build/daphnia_rockpool_gate1")
OUT.mkdir(parents=True, exist_ok=True)


def canonical_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def range_get(start: int, end: int) -> bytes:
    req = urllib.request.Request(
        URL,
        headers={
            "User-Agent": UA,
            "Range": f"bytes={start}-{end}",
            "Accept-Encoding": "identity",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        status = getattr(response, "status", None) or response.getcode()
        if status != 206:
            raise RuntimeError(f"range request returned HTTP {status}, expected 206")
        body = response.read()
    if len(body) != end - start + 1:
        raise RuntimeError("range response length mismatch")
    return body


def extract_distance() -> bytes:
    offset = MEMBER["local_header_offset"]
    fixed = range_get(offset, offset + 29)
    fields = struct.unpack("<4s5H3I2H", fixed)
    if fields[0] != b"PK\x03\x04":
        raise RuntimeError("invalid local ZIP header for frozen distance member")
    method = fields[3]
    name_len = fields[9]
    extra_len = fields[10]
    raw_name = range_get(offset + 30, offset + 30 + name_len - 1)
    name = raw_name.decode("utf-8", errors="replace")
    if name != MEMBER["name"]:
        raise RuntimeError(f"distance member name mismatch: {name!r}")
    data_start = offset + 30 + name_len + extra_len
    compressed = range_get(data_start, data_start + MEMBER["compressed_size"] - 1)
    if method == 8:
        content = zlib.decompress(compressed, -15)
    elif method == 0:
        content = compressed
    else:
        raise RuntimeError(f"unsupported ZIP compression method {method}")
    if len(content) != MEMBER["uncompressed_size"]:
        raise RuntimeError("distance member uncompressed-size mismatch")
    crc = f"{binascii.crc32(content) & 0xffffffff:08x}"
    if crc != MEMBER["crc32"]:
        raise RuntimeError(f"distance member CRC mismatch: {crc}")
    sha = hashlib.sha256(content).hexdigest()
    if sha != MEMBER["sha256"]:
        raise RuntimeError(f"distance member SHA-256 mismatch: {sha}")
    return content


def sequential_labels(values: np.ndarray, n: int) -> bool:
    if values.shape != (n,) or not np.isfinite(values).all():
        return False
    one_based = np.allclose(values, np.arange(1, n + 1), atol=1e-9, rtol=0.0)
    zero_based = np.allclose(values, np.arange(n), atol=1e-9, rtol=0.0)
    return bool(one_based or zero_based)


def normalize_distance_csv(content: bytes) -> tuple[np.ndarray, tuple[int, ...]]:
    raw = np.genfromtxt(io.StringIO(content.decode("utf-8-sig")), delimiter=",", dtype=float)
    raw = np.asarray(raw, dtype=float)
    if raw.ndim == 0:
        raw = raw.reshape(1, 1)
    elif raw.ndim == 1:
        raw = raw.reshape(-1, 1)
    original_shape = tuple(int(x) for x in raw.shape)

    # Match the already-passed Gate-0 geometry parser: discard only rows/columns
    # containing no numeric value. This removes ordinary CSV header/index labels
    # without inspecting any response-bearing member.
    keep_rows = ~np.all(~np.isfinite(raw), axis=1)
    keep_cols = ~np.all(~np.isfinite(raw), axis=0)
    arr = raw[keep_rows][:, keep_cols]

    if arr.shape == (N, N):
        return arr, original_shape
    if arr.shape == (N, N + 1) and sequential_labels(arr[:, 0], N):
        return arr[:, 1:], original_shape
    if arr.shape == (N + 1, N) and sequential_labels(arr[0, :], N):
        return arr[1:, :], original_shape
    if arr.shape == (N + 1, N + 1):
        if sequential_labels(arr[1:, 0], N) and sequential_labels(arr[0, 1:], N):
            return arr[1:, 1:], original_shape
    raise RuntimeError(
        f"distance.csv could not be deterministically normalized to {N}x{N}; "
        f"raw shape={original_shape}, numeric shape={arr.shape}"
    )


def main() -> int:
    content = extract_distance()
    distance, raw_shape = normalize_distance_csv(content)

    if distance.shape != (N, N):
        raise RuntimeError(f"expected {N}x{N} distance matrix, found {distance.shape}")
    if not np.isfinite(distance).all() or np.any(distance < -1e-12):
        raise RuntimeError("distance matrix contains invalid values")
    if not np.allclose(distance, distance.T, atol=1e-9, rtol=1e-9):
        raise RuntimeError("distance matrix is not symmetric")
    if not np.allclose(np.diag(distance), 0.0, atol=1e-9, rtol=0.0):
        raise RuntimeError("distance matrix diagonal is not zero")

    node_ids = tuple(f"pool_{i+1:03d}" for i in range(N))
    declaration = StructuralScaleLadderDeclaration(
        axis_id="geo",
        target_largest_component_fractions=TARGETS,
    )
    ladder = build_structural_scale_ladder(node_ids, distance, declaration)
    structural = structural_scale_adjacencies(ladder, distance)
    worlds = {
        f"structural::{world_id}": adjacency
        for world_id, adjacency in structural.items()
    }
    audit = audit_world_universe_structure(node_ids, worlds, horizon=HORIZON)
    gate = apply_structural_adequacy_gate(
        audit,
        StructuralAdequacyDeclaration(
            min_largest_weak_component_fraction=MIN_LCC,
            max_isolated_node_fraction=MAX_ISOLATED,
            require_at_least_one_world_pass=True,
        ),
    )

    audits = {row.world_id: row for row in audit.world_audits}
    level90 = audits.get("structural::geo_lcc900")
    if level90 is None:
        raise RuntimeError("missing structural::geo_lcc900 world")
    positive = [value for value in ladder.thresholds if value > 0]
    distinct_count = len({round(value, 12) for value in positive})
    distinct_pass = distinct_count >= MIN_DISTINCT
    level90_pass = (
        level90.largest_weak_component_fraction >= MIN_LCC - 1e-12
        and level90.isolated_node_fraction <= MAX_ISOLATED + 1e-12
    )
    ordered = [structural[level.level_id] for level in ladder.levels]
    nested_pass = all(np.all(~before | after) for before, after in zip(ordered, ordered[1:]))
    final_pass = bool(gate.passed and level90_pass and distinct_pass and nested_pass)

    payload = {
        "status": (
            "gate1_pass_structural_adequacy"
            if final_pass
            else "gate1_stop_structural_inadequacy"
        ),
        "candidate": "Luo et al. 2022 Tvärminne Daphnia rock-pool metacommunity",
        "response_rows_opened": False,
        "response_member_bytes_downloaded": False,
        "distance_member_sha256": MEMBER["sha256"],
        "distance_csv_raw_numeric_shape": list(raw_shape),
        "distance_matrix_shape": list(distance.shape),
        "node_count": N,
        "node_identity": "stable response-independent row order 1..546 of frozen distance.csv",
        "structural_targets": list(TARGETS),
        "audit_horizon": HORIZON,
        "structural_ladder": [
            {
                "level_id": level.level_id,
                "target_largest_component_fraction": level.target_largest_component_fraction,
                "distance_threshold_released_units": level.distance_threshold,
                "achieved_largest_component_fraction": level.achieved_largest_component_fraction,
                "weak_component_count": level.weak_component_count,
                "isolated_node_fraction": level.isolated_node_fraction,
                "directed_edge_count": level.directed_edge_count,
                "fingerprint": level.fingerprint,
            }
            for level in ladder.levels
        ],
        "distinct_positive_structural_thresholds": distinct_count,
        "level90_pass": level90_pass,
        "distinct_scale_pass": distinct_pass,
        "nested_scale_pass": nested_pass,
        "generic_gate_pass": gate.passed,
        "generic_gate_passing_world_ids": list(gate.passing_world_ids),
        "declaration_fingerprint": ladder.declaration_fingerprint,
        "distance_matrix_fingerprint": ladder.distance_matrix_fingerprint,
        "ladder_fingerprint": ladder.fingerprint,
        "audit_fingerprint": audit.fingerprint,
        "gate_fingerprint": gate.fingerprint,
        "final_gate_pass": final_pass,
        "scientific_boundary": (
            "These are response-blind analyst-choice structural scales in released "
            "distance units, not biological Daphnia dispersal distances or fitted "
            "colonisation parameters."
        ),
        "next": (
            "if pass, freeze source/process semantics, temporal split, Layer A, "
            "unchanged Layer B, strong comparators, exact count gate and once-only "
            "runner before opening data_M.csv"
        ),
    }
    payload["fingerprint"] = canonical_sha256(payload)
    (OUT / "gate1_result.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if final_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
