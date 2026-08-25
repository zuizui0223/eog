from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "build" / "replication_2_source_screen"
BUILD.mkdir(parents=True, exist_ok=True)
OUT = BUILD / "sciencebase_camera_metadata_screen.json"

QUERIES = [
    "camera trap",
    "camera-trap",
    "remote camera wildlife",
    "trail camera wildlife",
    "camera mammal monitoring",
]
GEOM = re.compile(r"(site|location|station|deployment|camera|coordinate|sampling|sample|effort|occasion|survey)", re.I)
RESP = re.compile(r"(detect|observation|capture|encounter|event|occurrence|species|record|image|sequence)", re.I)
TERRESTRIAL = re.compile(r"(mammal|wildlife|camera|terrestrial|forest|woodland|desert|grassland|prairie|ungulate|carnivore|amphib|reptile)", re.I)
AQUATIC_ONLY = re.compile(r"(marine|ocean|fish|river|stream|lake|estuar|seal|whale|dolphin)", re.I)


def get_json(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "EOG-replication-source-screen/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return json.loads(raw), len(raw)


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def slim_file(f):
    return {
        "name": f.get("name"),
        "title": f.get("title"),
        "size": f.get("size"),
        "contentType": f.get("contentType"),
        "checksum": f.get("checksum"),
    }


def collect_files(item: dict):
    files = [slim_file(f) for f in (item.get("files") or []) if isinstance(f, dict)]
    return files


def item_text(item: dict):
    parts = [item.get("title") or "", item.get("summary") or "", item.get("body") or ""]
    return " ".join(str(x) for x in parts)


def score_candidate(item: dict, files: list[dict]):
    names = [str(f.get("name") or f.get("title") or "") for f in files]
    geom = [n for n in names if GEOM.search(n)]
    resp = [n for n in names if RESP.search(n)]
    distinct = bool(geom and resp and set(geom) != set(resp))
    text = item_text(item)
    terrestrial = bool(TERRESTRIAL.search(text)) and not bool(AQUATIC_ONLY.search(text))
    csvish = sum(1 for n in names if re.search(r"\.(csv|tsv|txt|xlsx?)$", n, re.I))
    score = (8 if distinct else 0) + (4 if terrestrial else 0) + min(csvish, 5) + min(len(files), 5) / 10
    return score, geom, resp, terrestrial, csvish


def main():
    inspected_search_bytes = 0
    ids = {}
    search_counts = []
    for q in QUERIES:
        url = "https://www.sciencebase.gov/catalog/items?" + urllib.parse.urlencode({"q": q, "format": "json", "max": 100})
        obj, n = get_json(url)
        inspected_search_bytes += n
        items = obj.get("items") or obj.get("results") or []
        search_counts.append({"query": q, "count": len(items), "metadata_bytes": n})
        for x in items:
            iid = x.get("id")
            if iid:
                ids[str(iid)] = x.get("title")

    candidates = []
    item_metadata_requests = 0
    child_metadata_requests = 0
    for iid in sorted(ids):
        try:
            item, _ = get_json(f"https://www.sciencebase.gov/catalog/item/{iid}?format=json")
        except Exception as exc:
            candidates.append({"item_id": iid, "title": ids[iid], "metadata_error": f"{type(exc).__name__}: {exc}"})
            continue
        item_metadata_requests += 1
        files = collect_files(item)
        child_summaries = []
        if not files:
            try:
                children, _ = get_json("https://www.sciencebase.gov/catalog/items?" + urllib.parse.urlencode({"parentId": iid, "format": "json", "max": 100}))
                child_metadata_requests += 1
                for ch in children.get("items") or []:
                    cid = ch.get("id")
                    if not cid:
                        continue
                    try:
                        full, _ = get_json(f"https://www.sciencebase.gov/catalog/item/{cid}?format=json")
                        item_metadata_requests += 1
                    except Exception:
                        continue
                    cfiles = collect_files(full)
                    if cfiles:
                        child_summaries.append({"item_id": str(cid), "title": full.get("title"), "files": cfiles})
                        files.extend(cfiles)
            except Exception:
                pass
        score, geom, resp, terrestrial, csvish = score_candidate(item, files)
        if score >= 8 or (geom and resp):
            candidates.append({
                "item_id": iid,
                "title": item.get("title"),
                "summary": (item.get("summary") or "")[:1000],
                "score": score,
                "terrestrial_signal": terrestrial,
                "csvish_file_count": csvish,
                "geometry_effort_filename_hits": sorted(set(geom)),
                "response_filename_hits": sorted(set(resp)),
                "files": files,
                "child_items_with_files": child_summaries,
                "doi_identifiers": [x for x in (item.get("identifiers") or []) if "doi" in str(x).lower()],
            })
    candidates.sort(key=lambda x: (-float(x.get("score", -1)), str(x.get("title") or "")))
    result = {
        "schema": "eog.replication_2_source_screen.sciencebase_camera_metadata.v1",
        "status": "metadata_screen_complete",
        "search_queries": search_counts,
        "unique_item_ids": len(ids),
        "item_metadata_requests": item_metadata_requests,
        "child_search_metadata_requests": child_metadata_requests,
        "file_payload_requests": 0,
        "file_payload_bytes_opened": 0,
        "candidate_count": len(candidates),
        "candidates": candidates[:40],
    }
    result["fingerprint"] = hashlib.sha256(canon(result)).hexdigest()
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps({"status": result["status"], "candidate_count": result["candidate_count"], "top": [{"item_id": c.get("item_id"), "title": c.get("title"), "score": c.get("score"), "geom": c.get("geometry_effort_filename_hits"), "resp": c.get("response_filename_hits")} for c in candidates[:15]], "file_payload_requests": 0, "fingerprint": result["fingerprint"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
