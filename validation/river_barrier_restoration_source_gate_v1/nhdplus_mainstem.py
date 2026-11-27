"""One public, response-free NHDPlus HR named-river topology audit."""
import argparse
from collections import Counter, defaultdict, deque
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

HERE = Path(__file__).resolve().parent
SOURCE = "https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer/3"
FIELDS = ("nhdplusid", "gnis_id", "gnis_name", "fromnode", "tonode",
          "lengthkm", "flowdir", "hydroseq", "dnhydroseq", "reachcode")
QUERY = {"where": "gnis_name = 'Elwha River'", "outFields": ",".join(FIELDS),
         "returnGeometry": "false", "orderByFields": "nhdplusid ASC",
         "resultRecordCount": 2000, "f": "json"}
LIMIT = 4194304


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def exact_id(value, allow_zero=False):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("non-numeric network ID")
    if value != int(value) or not (int(not allow_zero) <= value <= 2**53-1):
        raise ValueError("non-exact or out-of-range network ID")
    return int(value)


def extract(obj):
    if not isinstance(obj, dict) or "error" in obj or obj.get("exceededTransferLimit"):
        raise ValueError("provider error or truncated query")
    features = obj.get("features")
    if not isinstance(features, list) or not 0 < len(features) < QUERY["resultRecordCount"]:
        raise ValueError("empty or potentially truncated network")
    edges = []
    for feature in features:
        attrs = feature["attributes"]
        lower = {k.lower(): v for k, v in attrs.items()}
        if len(lower) != len(attrs) or not set(FIELDS) <= lower.keys():
            raise ValueError("incomplete or ambiguous field schema")
        if lower["gnis_name"] != "Elwha River" or not isinstance(lower["gnis_id"], str) or not lower["gnis_id"].strip():
            raise ValueError("unexpected geographic name or ID")
        if exact_id(lower["flowdir"]) != 1:
            raise ValueError("unknown flow direction")
        a, b = exact_id(lower["fromnode"]), exact_id(lower["tonode"])
        if a == b:
            raise ValueError("self-loop")
        length = lower["lengthkm"]
        if type(length) not in (int, float) or not math.isfinite(length) or length <= 0:
            raise ValueError("invalid provider length")
        rc = lower["reachcode"]
        if not isinstance(rc, str) or not rc.strip():
            raise ValueError("missing provider reach code")
        edges.append({"nhdplusid": exact_id(lower["nhdplusid"]), "gnis_id": lower["gnis_id"],
                      "fromnode": a, "tonode": b, "lengthkm": length,
                      "hydroseq": exact_id(lower["hydroseq"]),
                      "dnhydroseq": exact_id(lower["dnhydroseq"], True), "reachcode": rc})
    edges.sort(key=lambda e: e["nhdplusid"])
    if len({e["nhdplusid"] for e in edges}) != len(edges) or len({e["hydroseq"] for e in edges}) != len(edges):
        raise ValueError("duplicate flowline/sequence ID")
    if len({e["gnis_id"] for e in edges}) != 1:
        raise ValueError("multiple named river identities")
    return summarize(edges)


def summarize(edges):
    adj, weak = defaultdict(list), defaultdict(set)
    indeg, outdeg = Counter(), Counter()
    by_seq = {e["hydroseq"]: e for e in edges}
    nodes = set()
    downstream_matches = downstream_mismatches = downstream_outside = downstream_end = 0
    for e in edges:
        a, b = e["fromnode"], e["tonode"]
        nodes.update((a, b))
        adj[a].append(b)
        weak[a].add(b)
        weak[b].add(a)
        indeg[b] += 1
        outdeg[a] += 1
        d = e["dnhydroseq"]
        if d in by_seq:
            other = by_seq[d]
            if other["fromnode"] == b and d < e["hydroseq"]:
                downstream_matches += 1
            else:
                downstream_mismatches += 1
        elif d == 0:
            downstream_end += 1
        else:
            downstream_outside += 1
    remaining, sizes = set(nodes), []
    while remaining:
        root = remaining.pop()
        component, todo = {root}, [root]
        while todo:
            a = todo.pop()
            for b in weak[a] - component:
                component.add(b)
                todo.append(b)
        remaining.difference_update(component)
        sizes.append(len(component))
    degree = {v: indeg[v] for v in nodes}
    queue = deque(sorted(v for v in nodes if not degree[v]))
    processed = 0
    while queue:
        a = queue.popleft()
        processed += 1
        for b in adj[a]:
            degree[b] -= 1
            if degree[b] == 0:
                queue.append(b)
    cycle = processed != len(nodes)
    stats = {"flowline_count": len(edges), "node_count": len(nodes),
             "weak_component_node_sizes": sorted(sizes, reverse=True),
             "branch_nodes": sum(outdeg[v] > 1 for v in nodes),
             "confluence_nodes": sum(indeg[v] > 1 for v in nodes),
             "within_selection_sources": sorted(v for v in nodes if indeg[v] == 0),
             "within_selection_sinks": sorted(v for v in nodes if outdeg[v] == 0),
             "directed_cycle": cycle, "sum_provider_length_km": math.fsum(e["lengthkm"] for e in edges),
             "downstream_sequence_matches": downstream_matches,
             "downstream_sequence_mismatches": downstream_mismatches,
             "downstream_sequence_outside_named_selection": downstream_outside,
             "downstream_sequence_zero": downstream_end}
    return {"status": ("HOLD_TOPOLOGY_INCONSISTENT" if cycle or downstream_mismatches
                       else "NAMED_HYDROGRAPHY_TOPOLOGY_ONLY"),
            "network": edges, "summary": stats,
            "survey_crosswalk_verified": False, "historical_network_verified": False,
            "fish_response_access_authorized": False, "ecological_scores": 0}


def self_test():
    def row(i, a, b, hs, ds):
        return {"attributes": dict(zip(FIELDS, (i, "fixture", "Elwha River", a, b, 1.25, 1, hs, ds, "fixture_code")))}
    obj = {"features": [row(1, 100, 101, 40, 30), row(2, 101, 102, 30, 20),
                        row(3, 103, 104, 10, 0)]}
    r = extract(obj)
    assert r["summary"]["weak_component_node_sizes"] == [3, 2]
    assert r["summary"]["downstream_sequence_matches"] == 1
    assert r["summary"]["downstream_sequence_outside_named_selection"] == 1
    assert r["summary"]["sum_provider_length_km"] == 3.75
    assert not r["survey_crosswalk_verified"]
    assert extract({"features": [row(1, 100, 101, 40, 30),
                                 row(2, 105, 102, 30, 0)]})["status"] == "HOLD_TOPOLOGY_INCONSISTENT"
    assert extract({"features": [row(1, 100, 101, 40, 0),
                                 row(2, 101, 100, 30, 0)]})["summary"]["directed_cycle"]
    for invalid in ({"features": obj["features"], "exceededTransferLimit": True},
                    {"features": [obj["features"][0]]*2},
                    {"features": []}, {"error": {"code": 400}}):
        try:
            extract(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid network accepted")
    print("Offline hydrography fixtures passed.")


def run():
    p = json.loads((HERE / "nhdplus_mainstem_protocol.json").read_text(encoding="utf-8"))
    if (p["status"] != "FROZEN_BEFORE_HYDROGRAPHY_QUERY" or p["source"] != SOURCE
            or p["query"] != QUERY or p["request"] != {"max_ci_attempts": 1,
                 "redirects": False, "timeout_seconds": 30, "max_bytes": LIMIT}):
        raise ValueError("frozen query contract changed")
    url = SOURCE + "/query?" + urlencode(QUERY)
    receipt = {"source": SOURCE, "query": QUERY, "request_attempts": 1,
               "fish_response_payloads_opened": 0, "fish_response_rows_parsed": 0,
               "ecological_scores": 0, "survey_crosswalk_verified": False}
    try:
        request = Request(url, headers={"Accept": "application/json",
                                       "User-Agent": "EOG-public-hydrography-audit/1.0"})
        with build_opener(NoRedirect()).open(request, timeout=30) as response:
            receipt["http_status"] = response.status
            if response.geturl() != url or response.headers.get_content_type() not in (
                    "application/json", "text/plain"):
                raise ValueError("unexpected endpoint/content type")
            raw = response.read(LIMIT+1)
            if len(raw) > LIMIT:
                raise ValueError("provider response too large")
        receipt.update({"response_bytes": len(raw),
                        "raw_sha256": hashlib.sha256(raw).hexdigest()})
        receipt.update(extract(json.loads(raw)))
    except Exception as exc:
        receipt.update({"status": "HOLD_HYDROGRAPHY_REQUEST_OR_SCHEMA_FAILED",
                        "error_type": type(exc).__name__,
                        "http_error_code": getattr(exc, "code", None)})
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    if args.self_test:
        self_test()
    else:
        if args.output is None:
            p.error("--output required")
        result = run()
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(result["status"])
