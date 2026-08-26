from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sys
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "neon_forest_coyote_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "gate1_time_geometry_contract.json").read_text())
GATE0 = json.loads((HERE / "gate0_source_profile_certificate.json").read_text())
OUT = BUILD / "gate1_time_geometry.json"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fp(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def get_bytes(url: str):
    req = urllib.request.Request(url, headers={"Accept": "text/csv,text/plain,*/*;q=0.5", "User-Agent": "EOG-NEON-coyote-Gate1/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read(), r.geturl(), r.headers.get("Content-Type")


def parse_date(token: str):
    s = str(token or "").strip()
    if not s:
        raise RuntimeError("blank date token")
    for fmt in CONTRACT["deployment_source"]["accepted_date_formats_in_order"]:
        try:
            return datetime.strptime(s, fmt).date(), fmt
        except ValueError:
            continue
    raise RuntimeError(f"unsupported frozen date token {s!r}")


def load_deployments():
    src = CONTRACT["deployment_source"]
    rid = int(src["record_id"])
    fn = src["filename"]
    url = f"https://zenodo.org/records/{rid}/files/{urllib.parse.quote(fn, safe='')}?download=1"
    raw, final_url, ctype = get_bytes(url)
    actual = hashlib.md5(raw).hexdigest()
    if actual != src["expected_md5"]:
        raise RuntimeError(f"deployment MD5 mismatch {actual} != {src['expected_md5']}")
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text), delimiter=",")
    header = list(reader.fieldnames or [])
    rows = list(reader)
    required = list(src["exact_columns"].values())
    missing = [x for x in required if x not in header]
    if missing:
        raise RuntimeError(f"deployment schema drift; missing={missing}; observed={header}")
    if len(rows) != int(GATE0["deployments"]["row_count"]):
        raise RuntimeError(f"deployment row count drift {len(rows)} != {GATE0['deployments']['row_count']}")
    return rows, {
        "size": len(raw),
        "md5": actual,
        "final_host": urllib.parse.urlparse(final_url).netloc,
        "content_type": ctype,
        "header": header,
    }


def haversine_km(a, b):
    radius = 6371.0088
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    return 2.0 * radius * math.asin(min(1.0, math.sqrt(h)))


def components(nodes, edges):
    adj = {n: set() for n in nodes}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    seen = set()
    sizes = []
    for n in nodes:
        if n in seen:
            continue
        stack = [n]
        seen.add(n)
        size = 0
        while stack:
            x = stack.pop()
            size += 1
            for y in adj[x]:
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def structural_ladder(nodes_by_context):
    pair_dist = {}
    positive = set()
    zero_pairs = 0
    total_nodes = sum(len(v) for v in nodes_by_context.values())
    context_summaries = []
    for ctx in sorted(nodes_by_context):
        nodes = nodes_by_context[ctx]
        local = []
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                d = haversine_km(nodes[i]["coord"], nodes[j]["coord"])
                pair_dist[(ctx, nodes[i]["id"], nodes[j]["id"])] = d
                local.append(d)
                if d > 0:
                    positive.add(d)
                else:
                    zero_pairs += 1
        context_summaries.append({
            "context": ctx,
            "node_count": len(nodes),
            "pair_count": len(local),
            "positive_pair_count": sum(d > 0 for d in local),
            "zero_pair_count": sum(d == 0 for d in local),
            "min_positive_km": min([d for d in local if d > 0], default=None),
            "max_km": max(local, default=None),
        })
    candidates = sorted(positive)
    if not candidates:
        return {"status": "stop_no_positive_within_context_distances"}

    targets = [float(x) for x in CONTRACT["structural_ladder"]["targets"]]
    thresholds = []
    coverage_at = {}
    target_i = 0
    for t in candidates:
        lcc_sum = 0
        for ctx, nodes in nodes_by_context.items():
            ids = [n["id"] for n in nodes]
            edges = []
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    d = pair_dist[(ctx, nodes[i]["id"], nodes[j]["id"])]
                    if d <= t:
                        edges.append((nodes[i]["id"], nodes[j]["id"]))
            lcc_sum += components(ids, edges)[0] if ids else 0
        cov = lcc_sum / total_nodes if total_nodes else 0.0
        while target_i < len(targets) and cov >= targets[target_i]:
            thresholds.append(t)
            coverage_at[str(targets[target_i])] = cov
            target_i += 1
        if target_i == len(targets):
            break
    distinct = sorted(set(thresholds))
    passed = (
        len(thresholds) == len(targets)
        and len(distinct) >= int(CONTRACT["structural_ladder"]["minimum_distinct_positive_thresholds"])
        and targets[-1] <= max([float(k) for k in coverage_at.keys()], default=0.0)
    )
    return {
        "status": "pass" if passed else "stop_structural_ladder_gate_failed",
        "total_nodes": total_nodes,
        "context_count": len(nodes_by_context),
        "positive_candidate_threshold_count": len(candidates),
        "zero_distance_pair_count": zero_pairs,
        "targets": targets,
        "thresholds_km": thresholds,
        "distinct_positive_thresholds": len(distinct),
        "coverage_at_selected_thresholds": coverage_at,
        "context_summaries": context_summaries,
        "fingerprint": fp({
            "targets": targets,
            "thresholds_km": thresholds,
            "contexts": {k: [n["id"] for n in v] for k, v in sorted(nodes_by_context.items())},
        }),
    }


def time_gate(deployments):
    cfg = CONTRACT["time_bin_selection"]
    candidates = [int(x) for x in cfg["candidate_width_days_descending"]]
    required_bins = [int(x) for x in cfg["required_relative_bins"]]
    min_fraction = float(cfg["minimum_active_fraction_per_bin"])
    evaluated = []
    selected = None
    selected_registry = None

    for width in candidates:
        registry = []
        by_bin = {}
        all_pass = True
        for k in required_bins:
            eligible = []
            for d in deployments:
                needed = width * min_fraction
                bin_start = (k - 1) * width
                overlap = max(0.0, min(float(width), d["duration_days"] - bin_start))
                if overlap + 1e-12 >= needed:
                    eligible.append(d)
                    registry.append({"deployment_id": d["deployment_id"], "relative_bin": k})
            contexts = {d["context"] for d in eligible}
            subs = {d["subproject"] for d in eligible}
            ok = (
                len(eligible) >= int(cfg["per_required_bin_min_eligible_deployments"])
                and len(contexts) >= int(cfg["per_required_bin_min_contexts"])
                and len(subs) >= int(cfg["per_required_bin_min_subprojects"])
            )
            by_bin[str(k)] = {
                "eligible_deployments": len(eligible),
                "context_count": len(contexts),
                "subproject_count": len(subs),
                "pass": ok,
            }
            all_pass = all_pass and ok
        calibration_total = sum(by_bin[str(k)]["eligible_deployments"] for k in (2, 3))
        heldout_total = sum(by_bin[str(k)]["eligible_deployments"] for k in (4, 5, 6, 7))
        all_pass = all_pass and calibration_total >= int(cfg["calibration_total_min_eligible_deployment_bins"])
        all_pass = all_pass and heldout_total >= int(cfg["heldout_total_min_eligible_deployment_bins"])
        entry = {
            "width_days": width,
            "by_relative_bin": by_bin,
            "calibration_total_eligible_deployment_bins": calibration_total,
            "heldout_total_eligible_deployment_bins": heldout_total,
            "pass": all_pass,
        }
        evaluated.append(entry)
        if all_pass and selected is None:
            selected = width
            selected_registry = sorted(registry, key=lambda x: (x["relative_bin"], x["deployment_id"]))

    if selected is None:
        return {
            "status": "stop_no_candidate_bin_width_passed",
            "evaluated": evaluated,
        }
    selected_entry = next(x for x in evaluated if x["width_days"] == selected)
    return {
        "status": "pass",
        "selected_width_days": selected,
        "selection_rule": cfg["selection_rule"],
        "roles": cfg["roles"],
        "selected": selected_entry,
        "evaluated": evaluated,
        "eligible_deployment_bin_registry_fingerprint": fp(selected_registry),
    }


def finish(result, code=0):
    result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return code


def main():
    result = {
        "schema": "eog.neon_forest_coyote_replication_2.gate1_time_geometry.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "deployment_profile": {},
        "time_gate": {},
        "structural_ladder": {},
        "response_firewall": dict(CONTRACT["response_firewall"]),
    }
    try:
        if GATE0["status"] != "gate0_pass_source_separation_and_response_independent_profiles":
            raise RuntimeError("Gate0 certificate is not passing")
        rows, srcmeta = load_deployments()
        cols = CONTRACT["deployment_source"]["exact_columns"]
        deployments = []
        formats = Counter()
        contexts = defaultdict(list)
        ids = set()
        for r in rows:
            did = str(r[cols["deployment_id"]]).strip()
            if not did or did in ids:
                raise RuntimeError(f"blank/duplicate deployment id: {did!r}")
            ids.add(did)
            start, sfmt = parse_date(r[cols["start_date"]])
            end, efmt = parse_date(r[cols["end_date"]])
            formats[sfmt] += 1
            formats[efmt] += 1
            if end <= start:
                raise RuntimeError(f"nonpositive active interval for {did}: {start}..{end}")
            start_year = int(str(r[cols["start_year"]]).strip())
            if start.year != start_year:
                raise RuntimeError(f"start_year disagrees with start_date for {did}: {start_year} != {start.year}")
            sub = str(r[cols["subproject_name"]]).strip()
            if not sub:
                raise RuntimeError(f"blank subproject for {did}")
            lat = float(str(r[cols["latitude"]]).strip())
            lon = float(str(r[cols["longitude"]]).strip())
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise RuntimeError(f"invalid coordinates for {did}: {(lat, lon)}")
            context = f"{sub}::{start_year}"
            d = {
                "deployment_id": did,
                "camera_name": str(r[cols["camera_name"]]).strip(),
                "subproject": sub,
                "start_year": start_year,
                "context": context,
                "latitude": lat,
                "longitude": lon,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "duration_days": float((end - start).days),
            }
            deployments.append(d)
            contexts[context].append({"id": did, "coord": (lat, lon)})

        durations = sorted(d["duration_days"] for d in deployments)
        sub_counts = Counter(d["subproject"] for d in deployments)
        context_counts = Counter(d["context"] for d in deployments)
        result["deployment_profile"] = {
            **srcmeta,
            "deployment_count": len(deployments),
            "subproject_count": len(sub_counts),
            "context_count": len(context_counts),
            "date_format_token_counts": dict(sorted(formats.items())),
            "duration_days_min": min(durations),
            "duration_days_median": durations[len(durations)//2],
            "duration_days_max": max(durations),
            "subproject_deployment_counts": dict(sorted(sub_counts.items())),
            "context_deployment_counts": dict(sorted(context_counts.items())),
            "registry_fingerprint": fp(sorted([
                {k: d[k] for k in ("deployment_id","subproject","start_year","context","latitude","longitude","start_date","end_date")}
                for d in deployments
            ], key=lambda x: x["deployment_id"])),
        }

        tg = time_gate(deployments)
        result["time_gate"] = tg
        if tg["status"] != "pass":
            result["status"] = tg["status"]
            result["reason"] = "No prospectively frozen deployment-relative bin width preserves initialization, calibration and four heldout units under the response-independent availability gate"
            return finish(result, 0)

        sg = structural_ladder(contexts)
        result["structural_ladder"] = sg
        if sg["status"] != "pass":
            result["status"] = sg["status"]
            result["reason"] = "Prospectively frozen within-subproject-year geometry did not produce the required distinct structural ladder"
            return finish(result, 0)

        result["status"] = "gate1_pass_response_independent_time_and_structure"
        result["reason"] = "Response-independent deployment dates selected the largest admissible relative-time bin and within-subproject-year geometry produced the frozen structural ladder; sequence response remained unopened"
        return finish(result, 0)
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
        return finish(result, 1)


if __name__ == "__main__":
    sys.exit(main())
