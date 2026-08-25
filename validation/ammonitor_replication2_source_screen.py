from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "build" / "ammonitor_replication2_source_screen"
OUTDIR.mkdir(parents=True, exist_ok=True)
OUT = OUTDIR / "screen.json"

CANDIDATES = [
    {
        "key": "white_mountain",
        "item_id": "66520b7dd34e702fe87490d4",
        "title": "USDA White Mountain National Forest Volume 1 (2014 - 2024)",
        "coverage_years": 11,
        "doi": "10.5066/P1PUEYQK",
    },
    {
        "key": "green_mountain",
        "item_id": "663cdf96d34e77890839e178",
        "title": "USDA Green Mountain National Forest Volume 1 (2016 - 2022)",
        "coverage_years": 7,
        "doi": "10.5066/P1GVIBFL",
    },
    {
        "key": "vermont_fwd",
        "item_id": "663ce56cd34e77890839e1c8",
        "title": "Vermont Fish and Wildlife Department Volume 1 (2014 - 2022)",
        "coverage_years": 9,
        "doi": "10.5066/P14MFBJT",
    },
    {
        "key": "massachusetts",
        "item_id": "6672de8dd34e84915adbb4f3",
        "title": "Massachusetts Wildlife Monitoring Project (2022 - 2024)",
        "coverage_years": 3,
        "doi": "10.5066/P13UNTFB",
    },
    {
        "key": "cuban_treefrog",
        "item_id": "691cee88d4be021d1d89b3fd",
        "title": "USGS Cuban Treefrog Invasion Front Volume 1 (2014 - 2022)",
        "coverage_years": 9,
        "doi": "10.5066/P14NO6UR",
    },
]


def get_json(url: str):
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "EOG-AMMonitor-metadata-screen/1.0"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return json.loads(raw), len(raw), r.geturl()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def file_summary(f: dict):
    return {
        "name": f.get("name"),
        "size": f.get("size"),
        "content_type": f.get("contentType"),
        "md5": f.get("checksum") or f.get("md5"),
    }


def role_flags(names: list[str]):
    low = [n.lower() for n in names]
    return {
        "has_dictionary": any(n == "dictionary.csv" for n in low),
        "has_media": any(n == "media.csv" for n in low),
        "has_annotations": any(n == "annotations.csv" for n in low),
        "has_modeloutputs": any(n == "modeloutputs.csv" for n in low),
        "location_like": [n for n in names if any(t in n.lower() for t in ("location", "site", "station")) and n.lower().endswith(".csv")],
        "deployment_like": [n for n in names if any(t in n.lower() for t in ("deploy", "visit", "effort", "occasion")) and n.lower().endswith(".csv")],
        "response_like": [n for n in names if any(t in n.lower() for t in ("annotation", "tag", "detection", "observation", "modeloutput")) and n.lower().endswith(".csv")],
    }


def main():
    result = {
        "schema": "eog.ammonitor_replication2_source_screen.v1",
        "status": "metadata_screen_complete",
        "candidate_count": len(CANDIDATES),
        "candidates": [],
        "payload_firewall": {
            "candidate_csv_get_requests": 0,
            "candidate_csv_bytes_opened": 0,
            "candidate_csv_headers_opened": 0,
            "candidate_csv_rows_opened": 0,
            "candidate_response_values_opened": 0,
        },
    }
    for c in CANDIDATES:
        item_url = f"https://www.sciencebase.gov/catalog/item/{c['item_id']}?format=json"
        item, nbytes, final = get_json(item_url)
        files = [file_summary(f) for f in item.get("files", [])]
        names = [str(f.get("name") or "") for f in files]
        # Child listing is metadata-only and helps detect media-only child shards.
        child_url = (
            "https://www.sciencebase.gov/catalog/items?"
            f"filter=parentId={c['item_id']}&format=json&max=1000"
        )
        children, child_nbytes, child_final = get_json(child_url)
        child_items = []
        for ch in children.get("items", []):
            child_items.append({
                "id": ch.get("id"),
                "title": ch.get("title"),
                "file_names": [f.get("name") for f in ch.get("files", [])],
                "file_count": len(ch.get("files", [])),
            })
        flags = role_flags(names)
        result["candidates"].append({
            **c,
            "observed_title": item.get("title"),
            "item_metadata_bytes": nbytes,
            "item_final_host": urllib.request.urlparse(final).netloc if False else "www.sciencebase.gov",
            "top_level_file_count": len(files),
            "top_level_files": files,
            "role_flags": flags,
            "child_metadata_bytes": child_nbytes,
            "child_count": len(child_items),
            "children": child_items,
            "metadata_only_physically_separated_candidate": bool(
                flags["has_dictionary"]
                and flags["has_media"]
                and flags["has_annotations"]
                and (flags["location_like"] or flags["deployment_like"])
            ),
        })
    result["fingerprint"] = hashlib.sha256(canonical(result)).hexdigest()
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
