from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "mount_st_helens_lupine_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "gate0_descriptor_only.json"
UA = "EOG-Mount-St-Helens-descriptor-only/2.0"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fp(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(s).strip().lower()).strip("_")


def get_bytes(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/csv,text/plain,*/*;q=0.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read(5_000_001)
        final = r.geturl()
        ctype = r.headers.get("Content-Type")
    if len(raw) > 5_000_000:
        raise RuntimeError(f"descriptor payload exceeded 5 MB bound: {url}")
    return raw, final, ctype


def row_has_any_value(row: dict) -> bool:
    return any(
        str(v).strip() != ""
        for k, v in row.items()
        if k is not None and v is not None
    )


def decode_csv(raw: bytes, label: str):
    text = None
    enc = None
    for candidate in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = raw.decode(candidate)
            enc = candidate
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise RuntimeError(f"cannot decode {label}")
    sample = text[:65536]
    try:
        delim = csv.Sniffer().sniff(sample, delimiters=",;\t").delimiter
    except csv.Error:
        delim = ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    header = list(reader.fieldnames or [])
    raw_rows = list(reader)
    if not header:
        raise RuntimeError(f"{label} has no header")
    # Audited source-hygiene rule: remove only rows for which every parsed field is blank.
    # This rule was fixed after the descriptor-only diagnostic proved that the plot CSV's
    # 96 DictReader rows comprise 92 unique data rows plus four fully blank physical rows.
    rows = [row for row in raw_rows if row_has_any_value(row)]
    return header, rows, enc, delim, len(raw_rows), len(raw_rows) - len(rows)


def resolve_column(header, aliases, label):
    by_norm = {norm(c): c for c in header}
    hits = []
    for alias in aliases:
        if alias in by_norm:
            hits.append(by_norm[alias])
    hits = list(dict.fromkeys(hits))
    if len(hits) != 1:
        raise RuntimeError(f"{label}: expected exactly one prospective alias hit, got {hits}; header={header}")
    return hits[0]


def to_int(v, label):
    s = str(v).strip()
    if not re.fullmatch(r"[+-]?\d+(?:\.0+)?", s):
        raise RuntimeError(f"non-integer {label}: {s!r}")
    return int(float(s))


def to_float(v, label):
    s = str(v).strip().replace(" ", "")
    try:
        return float(s)
    except ValueError as exc:
        raise RuntimeError(f"non-numeric {label}: {s!r}") from exc


def haversine(a, b, radius):
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * radius * math.asin(min(1.0, math.sqrt(h)))


class UF:
    def __init__(self, n):
        self.p = list(range(n))
        self.s = [1] * n
        self.max_size = 1 if n else 0

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b:
            return
        if self.s[a] < self.s[b]:
            a, b = b, a
        self.p[b] = a
        self.s[a] += self.s[b]
        if self.s[a] > self.max_size:
            self.max_size = self.s[a]


def lcc_thresholds(coords, targets, radius):
    n = len(coords)
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine(coords[i], coords[j], radius)
            if d > 0:
                edges.append((d, i, j))
    edges.sort(key=lambda x: x[0])
    uf = UF(n)
    out = {}
    ti = 0
    targets = sorted(float(x) for x in targets)
    idx = 0
    while idx < len(edges) and ti < len(targets):
        d = edges[idx][0]
        while idx < len(edges) and abs(edges[idx][0] - d) <= 1e-12:
            _, a, b = edges[idx]
            uf.union(a, b)
            idx += 1
        while ti < len(targets):
            required = math.ceil(targets[ti] * n - 1e-12)
            if uf.max_size >= required:
                out[str(targets[ti])] = d
                ti += 1
            else:
                break
    if ti < len(targets):
        raise RuntimeError(f"could not attain all LCC targets; attained={out}")
    return out, len(edges)


def main():
    c = CONTRACT
    firewall = dict(c["response_firewall"])
    result = {
        "schema": "eog.mount_st_helens_lupine_replication_2.gate0_descriptor_only.v2",
        "attempt_id": c["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "plot_descriptor": {},
        "species_descriptor": {},
        "availability": {},
        "focal_species": {},
        "geometry": {},
        "response_firewall": firewall,
    }
    try:
        plot_raw, plot_final, plot_type = get_bytes(c["archive"]["plot_descriptor_url"])
        species_raw, species_final, species_type = get_bytes(c["archive"]["species_descriptor_url"])
        ph, prows, penc, pdelim, plot_raw_count, plot_blank_excluded = decode_csv(plot_raw, "plot descriptor")
        sh, srows, senc, sdelim, species_raw_count, species_blank_excluded = decode_csv(species_raw, "species descriptor")

        result["plot_descriptor"] = {
            "url": c["archive"]["plot_descriptor_url"],
            "final_url": plot_final,
            "bytes": len(plot_raw),
            "sha256": hashlib.sha256(plot_raw).hexdigest(),
            "content_type": plot_type,
            "encoding": penc,
            "delimiter": pdelim,
            "header": ph,
            "raw_dictreader_row_count": plot_raw_count,
            "fully_blank_rows_excluded_by_audited_hygiene_rule": plot_blank_excluded,
            "row_count": len(prows),
        }
        result["species_descriptor"] = {
            "url": c["archive"]["species_descriptor_url"],
            "final_url": species_final,
            "bytes": len(species_raw),
            "sha256": hashlib.sha256(species_raw).hexdigest(),
            "content_type": species_type,
            "encoding": senc,
            "delimiter": sdelim,
            "header": sh,
            "raw_dictreader_row_count": species_raw_count,
            "fully_blank_rows_excluded_by_audited_hygiene_rule": species_blank_excluded,
            "row_count": len(srows),
        }

        if len(prows) != int(c["archive"]["published_plot_descriptor_rows"]):
            result["status"] = "stop_plot_descriptor_row_count_not_reproduced_after_blank_row_hygiene"
            result["reason"] = f"observed {len(prows)} nonblank plot rows, expected {c['archive']['published_plot_descriptor_rows']}"
            return finish(result)
        if len(srows) != int(c["archive"]["published_species_descriptor_rows"]):
            result["status"] = "stop_species_descriptor_row_count_not_reproduced_after_blank_row_hygiene"
            result["reason"] = f"observed {len(srows)} nonblank species rows, expected {c['archive']['published_species_descriptor_rows']}"
            return finish(result)

        plot_code_col = resolve_column(ph, ["plot_code", "plotcode", "plot_id", "plotid"], "plot code")
        first_col = resolve_column(ph, ["first_year", "firstyear", "first_year_sampled", "firstyearsampled", "first_sample_year"], "first sampled year")
        last_col = resolve_column(ph, ["last_year", "lastyear", "last_year_sampled", "lastyearsampled", "last_sample_year"], "last sampled year")
        lon_col = resolve_column(ph, ["longitude", "long", "lon", "decimal_longitude"], "longitude")
        lat_col = resolve_column(ph, ["latitude", "lat", "decimal_latitude"], "latitude")

        parsed = []
        for r in prows:
            code = str(r.get(plot_code_col, "")).strip()
            if not code:
                raise RuntimeError("blank plot code in nonblank descriptor row")
            first = to_int(r.get(first_col), f"{code} first year")
            last = to_int(r.get(last_col), f"{code} last year")
            if first < 1900 or last > 2100 or last < first:
                raise RuntimeError(f"invalid sampled-year interval for {code}: {first}..{last}")
            lon = to_float(r.get(lon_col), f"{code} longitude")
            lat = to_float(r.get(lat_col), f"{code} latitude")
            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                raise RuntimeError(f"invalid coordinates for {code}: {lat}, {lon}")
            parsed.append({"plot_code": code, "first_year": first, "last_year": last, "longitude": lon, "latitude": lat})

        codes = [x["plot_code"] for x in parsed]
        if len(set(codes)) != len(codes):
            result["status"] = "stop_plot_code_not_unique"
            result["reason"] = "plot descriptor contains duplicate plot codes"
            return finish(result)

        eligibility_count = sum(x["last_year"] - x["first_year"] + 1 for x in parsed)
        result["availability"] = {
            "rule": "each integer calendar year from first_year through last_year inclusive is eligible for that plot",
            "implied_plot_year_count": eligibility_count,
            "published_plot_year_count": int(c["archive"]["published_plot_year_rows"]),
            "first_year_min": min(x["first_year"] for x in parsed),
            "last_year_max": max(x["last_year"] for x in parsed),
            "continuous_rule_exactly_reproduces_published_count": eligibility_count == int(c["archive"]["published_plot_year_rows"]),
        }
        if eligibility_count != int(c["archive"]["published_plot_year_rows"]):
            result["status"] = "stop_descriptor_continuous_availability_does_not_reproduce_published_plot_year_count"
            result["reason"] = f"descriptor-implied count {eligibility_count} != published {c['archive']['published_plot_year_rows']}; biological plot-year files remain forbidden for repair"
            return finish(result)

        latin_cols = [col for col in sh if ("species" in norm(col) and "authority" in norm(col))]
        if not latin_cols:
            latin_cols = [col for col in sh if norm(col) in {"species", "scientific_name", "taxon"}]
        if len(latin_cols) != 1:
            raise RuntimeError(f"cannot prospectively resolve unique species-name column: {latin_cols}; header={sh}")
        latin_col = latin_cols[0]
        raw_code_col = resolve_column(sh, ["raw_code", "rawcode", "species_code", "speciescode"], "raw species code")
        focal_rows = [r for r in srows if "lupinus" in str(r.get(latin_col, "")).casefold() and "lepidus" in str(r.get(latin_col, "")).casefold()]
        if len(focal_rows) != 1:
            result["status"] = "stop_focal_species_descriptor_not_unique"
            result["reason"] = f"found {len(focal_rows)} descriptor rows containing Lupinus + lepidus"
            return finish(result)
        focal = focal_rows[0]
        raw_code = str(focal.get(raw_code_col, "")).strip()
        if not raw_code:
            result["status"] = "stop_focal_raw_code_blank"
            result["reason"] = "unique Lupinus lepidus descriptor row has blank raw response code"
            return finish(result)
        result["focal_species"] = {
            "frozen_scientific_name": c["focal_species"]["scientific_name"],
            "archive_taxon_text": str(focal.get(latin_col, "")).strip(),
            "raw_response_column_code": raw_code,
            "species_name_column": latin_col,
            "raw_code_column": raw_code_col,
        }

        coords = [(x["latitude"], x["longitude"]) for x in parsed]
        thresholds, edge_count = lcc_thresholds(coords, c["gate0"]["structural_lcc_targets"], float(c["gate0"]["haversine_radius_km"]))
        distinct = sorted({round(float(v), 12) for v in thresholds.values() if float(v) > 0})
        result["geometry"] = {
            "registry_fingerprint": fp(sorted(parsed, key=lambda x: x["plot_code"])),
            "plot_count": len(parsed),
            "pairwise_positive_edge_count": edge_count,
            "lcc_thresholds_km": thresholds,
            "distinct_positive_thresholds_km": distinct,
            "distinct_positive_threshold_count": len(distinct),
            "haversine_radius_km": c["gate0"]["haversine_radius_km"],
        }
        if len(distinct) < int(c["gate0"]["require_distinct_positive_structural_scales"]):
            result["status"] = "stop_insufficient_distinct_structural_scales"
            result["reason"] = f"only {len(distinct)} distinct positive structural thresholds"
            return finish(result)

        result["status"] = "gate0_pass_descriptor_registry_availability_focal_code_and_geometry"
        result["reason"] = "audited blank-row hygiene leaves exactly 92 response-independent plots; descriptors reproduce the published plot-year availability count, resolve the frozen Lupinus code and provide >=3 spatial scales; target response and structural-summary plot-year files remain unopened"
        return finish(result)
    except Exception as exc:
        result["status"] = "engineering_failure_pre_response"
        result["reason"] = f"{type(exc).__name__}: {exc}"
        return finish(result, rc=1)


def finish(result, rc=0):
    result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return rc


if __name__ == "__main__":
    sys.exit(main())
