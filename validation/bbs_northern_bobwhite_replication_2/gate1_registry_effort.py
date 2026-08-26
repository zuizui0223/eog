from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "bbs_northern_bobwhite_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "gate1_registry_effort_contract.json").read_text())
SOURCE = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "gate1_registry_effort.json"


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fp(o):
    return hashlib.sha256(canon(o)).hexdigest()


def get_json(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "EOG-BBS-Gate1/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def get_bytes(url: str):
    req = urllib.request.Request(url, headers={"Accept": "text/csv,application/octet-stream,*/*;q=0.5", "User-Agent": "EOG-BBS-Gate1/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read(), r.geturl(), r.headers.get("Content-Type")


def checksum_md5(f: dict):
    c = f.get("checksum")
    if isinstance(c, dict):
        t = str(c.get("type") or c.get("algorithm") or "").lower()
        v = str(c.get("value") or c.get("checksum") or "").lower()
        if t and t != "md5":
            raise RuntimeError(f"unexpected checksum type {t} for {f.get('name')}")
        return v
    s = str(c or "")
    if ":" in s:
        a, b = s.split(":", 1)
        if a.lower() != "md5":
            raise RuntimeError(f"unexpected checksum type {a} for {f.get('name')}")
        return b.lower()
    return s.lower()


def decode_csv(raw: bytes, label: str):
    text = None
    enc = None
    for candidate in ("utf-8-sig", "cp1252"):
        try:
            text = raw.decode(candidate)
            enc = candidate
            break
        except UnicodeDecodeError:
            pass
    if text is None:
        raise RuntimeError(f"cannot decode {label}")
    sample = text[:65536]
    try:
        delim = csv.Sniffer().sniff(sample, delimiters=",;\t").delimiter
    except csv.Error:
        delim = ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    header = list(reader.fieldnames or [])
    if not header:
        raise RuntimeError(f"{label} has no header")
    rows = list(reader)
    return header, rows, enc, delim


def norm(s: str):
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())


def resolve_semantics(header: list[str], aliases: dict[str, list[str]], required: set[str]):
    hmap = defaultdict(list)
    for h in header:
        hmap[norm(h)].append(h)
    resolved = {}
    for semantic, options in aliases.items():
        hits = []
        for a in options:
            hits.extend(hmap.get(norm(a), []))
        hits = list(dict.fromkeys(hits))
        if len(hits) > 1:
            raise RuntimeError(f"ambiguous semantic {semantic}: {hits}")
        if len(hits) == 1:
            resolved[semantic] = hits[0]
        elif semantic in required:
            raise RuntimeError(f"missing required semantic {semantic}; header={header}")
    return resolved


def intval(v, label):
    s = str(v or "").strip()
    if not s:
        raise RuntimeError(f"blank integer {label}")
    try:
        return int(float(s))
    except ValueError as exc:
        raise RuntimeError(f"invalid integer {label}={s!r}") from exc


def floatval(v, label):
    s = str(v or "").strip()
    if not s:
        raise RuntimeError(f"blank float {label}")
    try:
        return float(s)
    except ValueError as exc:
        raise RuntimeError(f"invalid float {label}={s!r}") from exc


def main():
    result = {
        "schema": "eog.bbs_northern_bobwhite_replication_2.gate1_registry_effort.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "files": {},
        "routes": {},
        "weather": {},
        "analysis_registry": {},
        "species_registry": {},
        "response_firewall": dict(CONTRACT["response_firewall"]),
    }
    try:
        item = get_json(SOURCE["source"]["metadata_item_url"])
        file_map = {str(f.get("name")): f for f in (item.get("files") or []) if isinstance(f, dict)}
        payloads = {}
        for name, spec in CONTRACT["allowed_payloads"].items():
            f = file_map.get(name)
            if f is None:
                raise RuntimeError(f"allowed file absent from ScienceBase metadata: {name}")
            size = int(f.get("size"))
            md5 = checksum_md5(f)
            if size != int(spec["size"]) or md5 != spec["md5"]:
                raise RuntimeError(f"metadata identity mismatch for {name}: size={size}, md5={md5}")
            uri = f.get("downloadUri") or f.get("url")
            if not uri:
                raise RuntimeError(f"no individual download URI for allowed file {name}")
            raw, final_url, ctype = get_bytes(uri)
            if len(raw) != int(spec["size"]):
                raise RuntimeError(f"byte-size mismatch for {name}: {len(raw)} != {spec['size']}")
            actual = hashlib.md5(raw).hexdigest()
            if actual != spec["md5"]:
                raise RuntimeError(f"MD5 mismatch for {name}: {actual} != {spec['md5']}")
            header, rows, enc, delim = decode_csv(raw, name)
            payloads[name] = (header, rows)
            result["files"][name] = {
                "size": len(raw), "md5": actual, "encoding": enc, "delimiter": delim,
                "header": header, "row_count": len(rows), "content_type": ctype,
                "final_download_host": urllib.request.urlparse(final_url).netloc if False else final_url.split('/')[2],
            }

        route_header, route_rows = payloads["Routes.csv"]
        weather_header, weather_rows = payloads["Weather.csv"]
        species_header, species_rows = payloads["SpeciesList.csv"]

        rsem = resolve_semantics(route_header, CONTRACT["semantic_aliases"]["routes"], {"country_num", "state_num", "route", "latitude", "longitude"})
        wsem = resolve_semantics(weather_header, CONTRACT["semantic_aliases"]["weather"], {"country_num", "state_num", "route", "year", "quality_current_id", "run_type"})
        ssem = resolve_semantics(species_header, CONTRACT["semantic_aliases"]["species"], {"aou", "english"})

        usa = int(CONTRACT["eligibility"]["usa_country_num"])
        route_by_key = {}
        duplicate_route_keys = []
        for r in route_rows:
            key = (intval(r.get(rsem["country_num"]), "route.country"), intval(r.get(rsem["state_num"]), "route.state"), intval(r.get(rsem["route"]), "route.route"))
            if key in route_by_key:
                duplicate_route_keys.append(key)
                continue
            lat = floatval(r.get(rsem["latitude"]), f"latitude {key}")
            lon = floatval(r.get(rsem["longitude"]), f"longitude {key}")
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise RuntimeError(f"out-of-range coordinates for {key}: {(lat, lon)}")
            route_by_key[key] = {"latitude": lat, "longitude": lon, "raw": r}
        if duplicate_route_keys:
            result["status"] = "stop_route_registry_nonunique"
            result["reason"] = f"Routes.csv contains duplicate route keys; first={duplicate_route_keys[:5]}"
            result["routes"] = {"semantic_columns": rsem, "row_count": len(route_rows), "duplicate_key_count": len(duplicate_route_keys)}
            result["fingerprint"] = fp({k:v for k,v in result.items() if k != "fingerprint"})
            OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n"); print(json.dumps(result, indent=2, sort_keys=True)); return 0

        usa_routes = {k:v for k,v in route_by_key.items() if k[0] == usa}
        modeled_years = set(map(int, CONTRACT["eligibility"]["modeled_years"]))
        run_type = int(CONTRACT["eligibility"]["acceptable_run_type"])
        qid = int(CONTRACT["eligibility"]["acceptable_quality_current_id"])
        eligible_by_route = defaultdict(set)
        eligible_rows = 0
        missing_route_keys = []
        duplicate_route_year = []
        seen_route_year = set()
        year_counts = Counter()
        for w in weather_rows:
            country = intval(w.get(wsem["country_num"]), "weather.country")
            year = intval(w.get(wsem["year"]), "weather.year")
            if country != usa or year not in modeled_years:
                continue
            if intval(w.get(wsem["run_type"]), "weather.RunType") != run_type:
                continue
            if intval(w.get(wsem["quality_current_id"]), "weather.QualityCurrentID") != qid:
                continue
            key = (country, intval(w.get(wsem["state_num"]), "weather.state"), intval(w.get(wsem["route"]), "weather.route"))
            if key not in usa_routes:
                missing_route_keys.append((key, year))
                continue
            ky = (key, year)
            if ky in seen_route_year:
                duplicate_route_year.append((key, year))
                continue
            seen_route_year.add(ky)
            eligible_by_route[key].add(year)
            year_counts[year] += 1
            eligible_rows += 1

        if missing_route_keys:
            result["status"] = "stop_weather_route_registry_mismatch"
            result["reason"] = f"quality-valid Weather rows do not map to Routes.csv; first={missing_route_keys[:5]}"
        elif duplicate_route_year:
            result["status"] = "stop_duplicate_quality_valid_route_year"
            result["reason"] = f"multiple quality-valid Weather rows exist for the same route-year; first={duplicate_route_year[:5]}"
        else:
            cal = set(map(int, CONTRACT["eligibility"]["calibration_years"]))
            hold = set(map(int, CONTRACT["eligibility"]["heldout_years"]))
            min_cal = int(CONTRACT["eligibility"]["minimum_quality_valid_calibration_years_per_route"])
            min_hold = int(CONTRACT["eligibility"]["minimum_quality_valid_heldout_years_per_route"])
            analysis_keys = sorted(k for k, ys in eligible_by_route.items() if len(ys & cal) >= min_cal and len(ys & hold) >= min_hold)
            if len(analysis_keys) < int(CONTRACT["eligibility"]["minimum_analysis_routes"]):
                result["status"] = "stop_insufficient_repeated_analysis_routes"
                result["reason"] = f"only {len(analysis_keys)} routes meet the frozen effort-only repeated-route rule"
            else:
                result["status"] = "gate1_pass_response_independent_registry_effort_and_species"
                result["reason"] = "exact Routes/Weather/SpeciesList payloads reproduced a large response-independent U.S. repeated-route universe under frozen RunType/Quality rules"

            reg = [{"country_num":k[0],"state_num":k[1],"route":k[2],"latitude":usa_routes[k]["latitude"],"longitude":usa_routes[k]["longitude"],"years":sorted(eligible_by_route[k])} for k in analysis_keys]
            result["analysis_registry"] = {
                "route_count": len(analysis_keys),
                "minimum_rule": {"calibration_years": min_cal, "heldout_years": min_hold},
                "registry_fingerprint": fp(reg),
                "quality_valid_route_years_in_analysis": sum(len(eligible_by_route[k]) for k in analysis_keys),
                "year_counts_in_analysis": dict(sorted(Counter(y for k in analysis_keys for y in eligible_by_route[k]).items())),
                "initialization_present_routes": sum(1 for k in analysis_keys if int(CONTRACT["eligibility"]["initialization_year"]) in eligible_by_route[k]),
            }

        target_common = CONTRACT["focal_species"]["common_name"].strip().lower()
        target_sci = CONTRACT["focal_species"]["scientific_name"].strip().lower()
        matches = []
        for row in species_rows:
            english = str(row.get(ssem["english"]) or "").strip()
            genus = str(row.get(ssem.get("genus", "")) or "").strip() if ssem.get("genus") else ""
            species = str(row.get(ssem.get("species", "")) or "").strip() if ssem.get("species") else ""
            sci = str(row.get(ssem.get("scientific_name", "")) or "").strip() if ssem.get("scientific_name") else ""
            combined = (sci or (genus + " " + species).strip()).lower()
            if english.lower() == target_common or combined == target_sci:
                matches.append({"aou": str(row.get(ssem["aou"]) or "").strip(), "english": english, "scientific": sci or (genus + " " + species).strip()})
        if len(matches) != 1:
            if not result["status"].startswith("stop_"):
                result["status"] = "stop_focal_species_registry_not_unique"
                result["reason"] = f"Northern Bobwhite registry match count={len(matches)}"
        result["species_registry"] = {"semantic_columns": ssem, "match_count": len(matches), "matches": matches}
        result["routes"] = {
            "semantic_columns": rsem, "row_count": len(route_rows), "unique_route_count": len(route_by_key), "usa_route_count": len(usa_routes),
            "usa_registry_fingerprint": fp(sorted([{"key":k,"lat":v["latitude"],"lon":v["longitude"]} for k,v in usa_routes.items()], key=lambda x:x["key"])),
        }
        result["weather"] = {
            "semantic_columns": wsem, "row_count": len(weather_rows), "quality_valid_modeled_route_year_count": eligible_rows,
            "quality_valid_year_counts_before_repeated_filter": dict(sorted(year_counts.items())),
            "duplicate_quality_valid_route_year_count": len(duplicate_route_year), "missing_route_key_count": len(missing_route_keys),
            "quality_rule": {"country_num":usa,"run_type":run_type,"quality_current_id":qid,"modeled_years":sorted(modeled_years)},
        }
        result["fingerprint"] = fp({k:v for k,v in result.items() if k != "fingerprint"})
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
        result["fingerprint"] = fp({k:v for k,v in result.items() if k != "fingerprint"})
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
