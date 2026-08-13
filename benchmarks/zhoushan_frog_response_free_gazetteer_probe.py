"""Query response-free public gazetteer candidates for the Zhoushan frog nodes.

This stage never opens the microsatellite data.  It does not automatically choose a
coordinate: it archives Nominatim/OpenStreetMap candidates inside the study-region
bounding box so the node-to-place mapping can be reviewed and frozen before genetic
response access.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

NODES: dict[str, tuple[str, ...]] = {
    "Guoju": ("Guoju", "Guoju Subdistrict"),
    "Xiepu": ("Xiepu",),
    "Yuanhua": ("Yuanhua", "Yuanhua Town"),
    "Meishan": ("Meishan", "Meishan Island"),
    "Fodu": ("Fodu", "Fodu Island"),
    "Liuheng": ("Liuheng", "Liuheng Island"),
    "Huni": ("Huni", "Huni Island"),
    "Xiashi": ("Xiashi", "Xiazhi", "Xiazhi Island"),
    "Mayi": ("Mayi", "Mayi Island"),
    "Taohua": ("Taohua", "Taohua Island"),
    "Dengbu": ("Dengbu", "Dengbu Island"),
    "Zhujiajian": ("Zhujiajian", "Zhujiajian Island"),
    "Putuoshan": ("Putuoshan", "Putuo Mountain"),
    "Zhoushan": ("Zhoushan Island", "Zhoushan"),
    "Damao": ("Damao", "Damao Island"),
    "Cezi": ("Cezi", "Cezi Island"),
    "Jintang": ("Jintang", "Jintang Island"),
    "Dapengshan": ("Dapengshan", "Dapengshan Island", "Depengshan"),
    "Changbai": ("Changbai", "Changbai Island"),
    "Xiushan": ("Xiushan", "Xiushan Island"),
    "Dayushan": ("Dayushan", "Dayushan Island"),
    "Daishan": ("Daishan Island", "Daishan"),
    "Dongji": ("Dongji", "Dongji Islands"),
    "Qushan": ("Qushan", "Qushan Island"),
    "Sijiao": ("Sijiao", "Sijiao Island"),
    "Shengshan": ("Shengshan", "Shengshan Island"),
    "Huaniao": ("Huaniao", "Huaniao Island"),
}

# Paper study region: 29°31′–31°04′ N, 121°30′–123°25′ E.  A small buffer
# is used for gazetteer search only; final coordinates must remain consistent with Fig. 1.
VIEWBOX = "121.0,31.3,123.7,29.2"  # left,top,right,bottom for Nominatim
BASE_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "EOG-v2-response-free-zhoushan-gazetteer/1.0 (research audit)"


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _query(text: str) -> tuple[str, list[dict[str, object]]]:
    parameters = {
        "q": text,
        "format": "jsonv2",
        "limit": "5",
        "addressdetails": "1",
        "namedetails": "1",
        "extratags": "1",
        "countrycodes": "cn",
        "viewbox": VIEWBOX,
        "bounded": "1",
    }
    url = BASE_URL + "?" + urlencode(parameters)
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "en"})
    with urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list):
        raise RuntimeError("Nominatim response is not a candidate list")
    return url, payload


def run() -> dict[str, object]:
    records: dict[str, object] = {}
    for node_index, (node, aliases) in enumerate(NODES.items()):
        alias_records = []
        seen_places: set[tuple[str, str, str]] = set()
        deduplicated = []
        for alias_index, alias in enumerate(aliases):
            if node_index or alias_index:
                time.sleep(1.1)
            query_text = f"{alias}, Zhejiang, China"
            url, candidates = _query(query_text)
            alias_records.append({"alias": alias, "query": query_text, "url": url, "n_candidates": len(candidates)})
            for candidate in candidates:
                key = (
                    str(candidate.get("osm_type", "")),
                    str(candidate.get("osm_id", "")),
                    str(candidate.get("place_id", "")),
                )
                if key in seen_places:
                    continue
                seen_places.add(key)
                deduplicated.append(candidate)
        records[node] = {
            "aliases": list(aliases),
            "queries": alias_records,
            "candidates": deduplicated,
        }

    result: dict[str, object] = {
        "status": "zhoushan-frog-response-free-gazetteer-candidate-probe",
        "source": "OpenStreetMap Nominatim public gazetteer",
        "n_nodes": len(NODES),
        "nodes": records,
        "viewbox": VIEWBOX,
        "genetic_response_accessed": False,
        "microsatellite_file_accessed": False,
        "coordinate_selection_performed": False,
        "next_gate": "review_candidates_against_study_figure_then_freeze_one_coordinate_per_node",
    }
    result["fingerprint"] = _canonical_sha256(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
