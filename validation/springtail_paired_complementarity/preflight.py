#!/usr/bin/env python3
"""Response-blind admission and authorization gate for the springtail attempt.

The script opens only fixed-commit Git tree metadata, three explicitly declared
nonresponse files, and two peer-reviewed aggregate-evidence files.  The row-level
experimental population table is represented only by its Git-tree path, blob ID,
and byte size.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import shlex
import sys
import urllib.error
import urllib.request

from eog.v2.outcome_access import (
    FrozenOutcomeAccessContract,
    REQUIRED_FREEZE_KEYS,
    evaluate_outcome_access_gate,
)
from eog.v2.prospective_estimability import (
    AggregateCountInterval,
    AggregateEstimabilityEvidence,
    ProspectiveEstimabilityDeclaration,
    evaluate_prospective_estimability,
)


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "build/springtail_paired_complementarity/preflight"
USER_AGENT = "EOG-springtail-response-blind-preflight/1.0"


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha1(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def bounded_get(url: str, maximum: int) -> tuple[bytes, str]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read(maximum + 1)
        status = getattr(response, "status", None) or response.getcode()
        content_type = response.headers.get("Content-Type", "")
    if status != 200:
        raise RuntimeError(f"bounded GET returned HTTP {status}: {url}")
    if len(payload) > maximum:
        raise RuntimeError(f"bounded GET exceeded {maximum} bytes: {url}")
    return payload, content_type


def verified_file(spec: dict, audit: dict, *, evidence: bool = False) -> bytes:
    bucket = "aggregate_evidence_requests" if evidence else "nonresponse_requests"
    audit[bucket].append(spec["url"] if evidence else spec["raw_url"])
    url = spec["url"] if evidence else spec["raw_url"]
    payload, content_type = bounded_get(url, int(spec["size"]))
    if len(payload) != int(spec["size"]):
        raise RuntimeError(f"size mismatch for {url}: {len(payload)} != {spec['size']}")
    observed_sha = hashlib.sha256(payload).hexdigest()
    if observed_sha != spec["sha256"]:
        raise RuntimeError(f"SHA-256 mismatch for {url}")
    if not evidence and git_blob_sha1(payload) != spec["git_blob_sha1"]:
        raise RuntimeError(f"Git blob mismatch for {url}")
    audit["opened_files"].append(
        {
            "role": "published_aggregate_evidence" if evidence else "nonresponse",
            "url": url,
            "bytes": len(payload),
            "sha256": observed_sha,
            "content_type": content_type,
        }
    )
    return payload


def parse_whitespace_table(payload: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    try:
        lines = payload.decode("utf-8-sig").splitlines()
    except UnicodeDecodeError as exc:
        raise RuntimeError("declared text table is not UTF-8") from exc
    token_rows = [shlex.split(line, comments=False, posix=True) for line in lines if line.strip()]
    if len(token_rows) < 2:
        raise RuntimeError("declared text table has no data rows")
    header = tuple(token_rows[0])
    if not header or len(set(header)) != len(header):
        raise RuntimeError("declared text table header is empty or duplicated")
    rows: list[dict[str, str]] = []
    for number, values in enumerate(token_rows[1:], start=2):
        if len(values) != len(header):
            raise RuntimeError(
                f"declared text table line {number} has {len(values)} fields; "
                f"expected {len(header)}"
            )
        rows.append(dict(zip(header, values, strict=True)))
    return header, rows


def finite_float(value: str, label: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise RuntimeError(f"{label} is not numeric: {value!r}") from exc
    if not math.isfinite(number):
        raise RuntimeError(f"{label} is not finite")
    return number


def exact_int(value: str, label: str) -> int:
    number = finite_float(value, label)
    integer = int(round(number))
    if abs(number - integer) > 1e-9:
        raise RuntimeError(f"{label} is not integer-valued: {value!r}")
    return integer


def audit_tree(contract: dict, audit: dict) -> dict[str, dict]:
    tree_spec = contract["github_tree"]
    audit["metadata_requests"].append(tree_spec["url"])
    payload, _ = bounded_get(tree_spec["url"], int(tree_spec["maximum_bytes"]))
    value = json.loads(payload.decode("utf-8"))
    if value.get("truncated") is True:
        raise RuntimeError("fixed Git tree response was truncated")
    rows = value.get("tree")
    if not isinstance(rows, list):
        raise RuntimeError("fixed Git tree response has no tree list")
    wanted = {
        spec["path"]: spec
        for spec in [*contract["nonresponse_files"].values(), contract["response_file"]]
    }
    observed: dict[str, dict] = {}
    for row in rows:
        path = row.get("path")
        if path not in wanted:
            continue
        spec = wanted[path]
        compact = {
            "path": path,
            "type": row.get("type"),
            "sha": row.get("sha"),
            "size": row.get("size"),
        }
        if compact["type"] != "blob":
            raise RuntimeError(f"fixed source path is not a blob: {path}")
        if compact["sha"] != spec["git_blob_sha1"]:
            raise RuntimeError(f"fixed source blob drift: {path}")
        if compact["size"] != spec["size"]:
            raise RuntimeError(f"fixed source size drift: {path}")
        observed[path] = compact
    if set(observed) != set(wanted):
        raise RuntimeError(f"fixed Git tree is missing declared paths: {sorted(set(wanted)-set(observed))}")
    audit["metadata_response_bytes"] = len(payload)
    return observed


def audit_geometry(contract: dict, payloads: dict[str, bytes]) -> dict:
    readme = payloads["readme"].decode("utf-8-sig")
    for text in (
        "8 replicates of each configuration (Rep 2 - 9)",
        "each network has ten nodes",
        "landscapeID (experiment only)",
        "Day - days since start of experiment; Ranges from 1-182 in experiment",
        "first day on which node population size is observed to be 1 or greater",
    ):
        if text not in readme:
            raise RuntimeError(f"fixed README semantic token missing: {text!r}")

    node_header, node_rows = parse_whitespace_table(payloads["node_geometry"])
    if node_header != ("Config", "Rep", "node", "distToSource", "degree"):
        raise RuntimeError(f"node geometry header drift: {node_header!r}")
    if len(node_rows) != 270:
        raise RuntimeError(f"node geometry row count drift: {len(node_rows)} != 270")

    registry_nodes: dict[tuple[int, int, int], tuple[float, float]] = {}
    for row in node_rows:
        config = exact_int(row["Config"], "node Config")
        rep = exact_int(row["Rep"], "node Rep")
        node = exact_int(row["node"], "node ID")
        distance = finite_float(row["distToSource"], "distToSource")
        degree = finite_float(row["degree"], "degree")
        if config not in (1, 2, 3) or rep not in range(1, 10) or node not in range(1, 11):
            raise RuntimeError("node geometry contains an undeclared Config/Rep/node")
        if distance < 0 or degree <= 0:
            raise RuntimeError("node geometry contains negative distance or nonpositive degree")
        if rep < 2:
            continue
        key = (config, rep, node)
        if key in registry_nodes:
            raise RuntimeError(f"duplicate closed-registry node row: {key}")
        registry_nodes[key] = (distance, degree)

    expected_nodes = {
        (config, rep, node)
        for config in (1, 2, 3)
        for rep in range(2, 10)
        for node in range(1, 11)
    }
    if set(registry_nodes) != expected_nodes:
        raise RuntimeError("node geometry does not exactly cover the closed 24x10 registry")
    for (config, rep, node), (distance, _) in registry_nodes.items():
        if (node == 5) != (abs(distance) <= 1e-12):
            raise RuntimeError(f"source-distance zero boundary failed for {(config, rep, node)}")

    network_header, network_rows = parse_whitespace_table(payloads["network_geometry"])
    expected_network_header = (
        "Config",
        "Rep",
        "AlgebraicConnectivity_Binary",
        "AlgebraicConnectivity_Weighted",
        "NetworkDiameter_Binary",
        "NetworkDiameter_Weighted",
    )
    if network_header != expected_network_header:
        raise RuntimeError(f"network geometry header drift: {network_header!r}")
    if len(network_rows) != 24:
        raise RuntimeError(f"network geometry row count drift: {len(network_rows)} != 24")
    networks: set[tuple[int, int]] = set()
    for row in network_rows:
        config = exact_int(row["Config"], "network Config")
        rep = exact_int(row["Rep"], "network Rep")
        key = (config, rep)
        if key in networks:
            raise RuntimeError(f"duplicate network geometry row: {key}")
        networks.add(key)
        metrics = [finite_float(row[name], name) for name in expected_network_header[2:]]
        if any(value <= 0 for value in metrics):
            raise RuntimeError(f"nonpositive network metric for {key}")
    expected_networks = {(config, rep) for config in (1, 2, 3) for rep in range(2, 10)}
    if networks != expected_networks:
        raise RuntimeError("network geometry does not exactly cover the closed registry")
    if {(config, rep) for config, rep, _ in registry_nodes} != networks:
        raise RuntimeError("node and network geometry registries disagree")

    return {
        "node_file_rows": len(node_rows),
        "closed_registry_node_rows": len(registry_nodes),
        "closed_registry_landscapes": len(networks),
        "nodes_per_landscape": 10,
        "source_node": 5,
        "source_distance_zero_only_at_source": True,
        "node_network_registry_join_complete": True,
    }


def run(output: Path) -> dict:
    contract_path = HERE / "source_contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=True)
    audit = {
        "attempt_id": contract["attempt_id"],
        "stage": "response_blind_source_geometry_and_outcome_authorization",
        "metadata_requests": [],
        "metadata_response_bytes": 0,
        "nonresponse_requests": [],
        "aggregate_evidence_requests": [],
        "opened_files": [],
        "response_download_requests": [],
        "response_payload_bytes_opened": 0,
        "response_rows_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }
    try:
        tree = audit_tree(contract, audit)
        payloads = {
            name: verified_file(spec, audit)
            for name, spec in contract["nonresponse_files"].items()
        }
        geometry = audit_geometry(contract, payloads)
        aggregate = contract["published_aggregate_evidence"]
        verified_file(aggregate["supplement"], audit, evidence=True)
        verified_file(aggregate["main_figure_2"], audit, evidence=True)

        lower = aggregate["split_specific_lower_bounds"]
        minima = contract["freezes"]["count_gate"]
        declaration = ProspectiveEstimabilityDeclaration(
            calibration_events=int(minima["calibration_events"]),
            calibration_non_events=int(minima["calibration_non_events"]),
            heldout_events=int(minima["heldout_events"]),
            heldout_non_events=int(minima["heldout_non_events"]),
            heldout_outer_units_with_both_classes=int(
                minima["heldout_outer_units_with_both_classes"]
            ),
        )
        intervals = {
            key: AggregateCountInterval(lower=int(lower[key]["lower"]))
            for key in (
                "calibration_events",
                "calibration_non_events",
                "heldout_events",
                "heldout_non_events",
                "heldout_outer_units_with_both_classes",
            )
        }
        estimability = evaluate_prospective_estimability(
            declaration,
            AggregateEstimabilityEvidence(
                source_label=(
                    "Rayfield et al. 2023 main Figure 2 and SI Figure S10 at frozen "
                    "Day-7 split, bound to declared SHA-256 files"
                ),
                endpoint_definition_matches=True,
                response_rows_opened=False,
                intervals=intervals,
                note=aggregate["manual_lower_bound_rule"],
            ),
        )
        if estimability.status != "plausibly_eligible_pre_response":
            raise RuntimeError(f"aggregate estimability did not pass: {estimability.status}")
        if int(lower["heldout_outer_units_with_rows"]["lower"]) < int(
            minima["heldout_outer_units_with_rows"]
        ):
            raise RuntimeError("published outer-unit row lower bound misses frozen minimum")

        freezes = contract["freezes"]
        if set(freezes) != set(REQUIRED_FREEZE_KEYS):
            raise RuntimeError(
                "freeze ledger keys differ from required gate: "
                f"missing={sorted(set(REQUIRED_FREEZE_KEYS)-set(freezes))}, "
                f"extra={sorted(set(freezes)-set(REQUIRED_FREEZE_KEYS))}"
            )
        runner_spec = freezes["runtime_runner"]
        runner_path = ROOT / runner_spec["path"]
        observed_runner_sha = file_sha256(runner_path)
        if observed_runner_sha != runner_spec["sha256"]:
            raise RuntimeError(
                f"frozen runner SHA mismatch: {observed_runner_sha} != {runner_spec['sha256']}"
            )
        freeze_fingerprints = {
            key: canonical_sha256(freezes[key]) for key in REQUIRED_FREEZE_KEYS
        }
        access_contract = FrozenOutcomeAccessContract(
            attempt_id=contract["attempt_id"],
            freeze_fingerprints=freeze_fingerprints,
            response_rows_opened=False,
            exact_count_gate_first=True,
            zero_fit_on_count_failure=True,
            no_post_open_redesign=True,
            note="fresh springtail paired complementarity; one response download only",
        )
        access = evaluate_outcome_access_gate(access_contract, estimability)
        if not access.authorized:
            raise RuntimeError(f"outcome access was not authorized: {access.status}")

        result = {
            **audit,
            "status": "authorized_once_only_exact_count_gate_required",
            "contract_sha256": file_sha256(contract_path),
            "runner_sha256": observed_runner_sha,
            "fixed_source_tree": [tree[path] for path in sorted(tree)],
            "geometry_audit": geometry,
            "aggregate_lower_bounds": lower,
            "prospective_estimability": asdict(estimability),
            "freeze_fingerprints": freeze_fingerprints,
            "outcome_access_contract_fingerprint": access_contract.fingerprint,
            "outcome_access_gate": asdict(access),
        }
        result["fingerprint"] = canonical_sha256(result)
    except Exception as exc:
        result = {
            **audit,
            "status": "pre_response_stop",
            "stop_reason": repr(exc),
        }
        result["fingerprint"] = canonical_sha256(result)
        (output / "preflight.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        raise

    if result["response_download_requests"]:
        raise AssertionError("preflight attempted a response download")
    if result["response_payload_bytes_opened"] != 0 or result["response_rows_opened"]:
        raise AssertionError("preflight opened response payload bytes or rows")
    if result["model_fits"] != 0 or result["heldout_scores"] != 0:
        raise AssertionError("preflight fit a model or scored heldout outcomes")
    (output / "preflight.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    try:
        result = run(output)
    except (OSError, RuntimeError, ValueError, KeyError, urllib.error.URLError) as exc:
        print(f"springtail preflight stopped: {exc!r}", file=sys.stderr)
        raise SystemExit(3) from exc
    print(
        json.dumps(
            {
                "status": result["status"],
                "closed_registry_landscapes": result["geometry_audit"][
                    "closed_registry_landscapes"
                ],
                "closed_registry_node_rows": result["geometry_audit"][
                    "closed_registry_node_rows"
                ],
                "response_download_requests": [],
                "response_payload_bytes_opened": 0,
                "response_rows_opened": False,
                "outcome_access_gate_fingerprint": result["outcome_access_gate"][
                    "fingerprint"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
