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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "portal_merriams_kangaroo_rat_third_fresh"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "gate0_response_free.json"

EXPECTED_HEADERS = {
    "trapping": ["day", "month", "year", "period", "plot", "sampled", "effort", "qcflag"],
    "moon_dates": ["newmoonnumber", "newmoondate", "period", "censusdate"],
    "geometry": ["gps_num", "plot", "type", "number", "east", "north", "elev", "hor_error", "vert_error", "flag", "notes"],
    "plot_history": ["year", "month", "plot", "treatment", "resourcetreatment", "anttreatment"],
}


class GateStop(RuntimeError):
    def __init__(self, status: str, reason: str):
        super().__init__(reason)
        self.status = status
        self.reason = reason


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def fp(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def git_blob_sha1(raw: bytes):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def response_firewall():
    return {
        "response_payload_requests": 0,
        "response_payload_bytes_opened": 0,
        "response_header_bytes_opened": 0,
        "response_rows_opened": False,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }


def base_result():
    return {
        "schema": "eog.portal_merriams_kangaroo_rat_third_fresh.gate0_response_free.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "source_contract_fingerprint": fp(CONTRACT),
        "upstream": CONTRACT["upstream"],
        "source_profiles": {},
        "species": {},
        "registry": {},
        "geometry": {},
        "temporal": {},
        "treatment_linkage": {},
        "response_firewall": response_firewall(),
    }


def write(result):
    result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


def stop(status: str, reason: str):
    raise GateStop(status, reason)


def get_allowed_bytes(role: str):
    if role not in CONTRACT["gate0"]["allowed_payloads"]:
        raise RuntimeError(f"role is not Gate0-authorized: {role}")
    if role == "forbidden_response":
        raise RuntimeError("forbidden response path cannot be opened at Gate0")
    spec = CONTRACT["files"][role]
    url = CONTRACT["upstream"]["raw_prefix"] + urllib.parse.quote(spec["path"], safe="/")
    req = urllib.request.Request(
        url,
        headers={"Accept": "text/plain,text/csv,*/*;q=0.1", "User-Agent": "EOG-Portal-response-free-gate0/1.0"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        raw = r.read()
        final_url = r.geturl()
        ctype = r.headers.get("Content-Type")
    if len(raw) != int(spec["size"]):
        stop("stop_response_independent_source_identity_mismatch", f"{role} byte size {len(raw)} != {spec['size']}")
    actual_blob = git_blob_sha1(raw)
    if actual_blob != spec["git_blob"]:
        stop("stop_response_independent_source_identity_mismatch", f"{role} Git blob {actual_blob} != {spec['git_blob']}")
    return raw, {
        "path": spec["path"],
        "expected_size": int(spec["size"]),
        "bytes_opened": len(raw),
        "verified_git_blob": actual_blob,
        "final_host": urllib.parse.urlparse(final_url).netloc,
        "content_type": ctype,
    }


def decode_utf8(raw: bytes, role: str):
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        stop("stop_response_independent_source_encoding_mismatch", f"{role} is not UTF-8/UTF-8-SIG: {exc}")


def csv_rows(raw: bytes, role: str, exact_header=None):
    text = decode_utf8(raw, role)
    reader = csv.DictReader(io.StringIO(text))
    header = list(reader.fieldnames or [])
    if not header:
        stop("stop_response_independent_source_schema_mismatch", f"{role} has no header")
    if exact_header is not None and header != list(exact_header):
        stop("stop_response_independent_source_schema_mismatch", f"{role} header {header} != frozen {list(exact_header)}")
    return header, list(reader)


def as_int(value, label):
    s = str(value if value is not None else "").strip()
    if not s:
        stop("stop_response_independent_source_value_mismatch", f"blank integer field {label}")
    try:
        x = float(s)
    except ValueError:
        stop("stop_response_independent_source_value_mismatch", f"non-numeric integer field {label}: {s!r}")
    if not x.is_integer():
        stop("stop_response_independent_source_value_mismatch", f"non-integer field {label}: {s!r}")
    return int(x)


def as_float(value, label):
    s = str(value if value is not None else "").strip()
    if not s:
        stop("stop_response_independent_source_value_mismatch", f"blank numeric field {label}")
    try:
        x = float(s)
    except ValueError:
        stop("stop_response_independent_source_value_mismatch", f"non-numeric field {label}: {s!r}")
    if not math.isfinite(x):
        stop("stop_response_independent_source_value_mismatch", f"non-finite field {label}: {s!r}")
    return x


def lcc_fraction(n, edges):
    parent = list(range(n))
    size = [1] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]

    for a, b in edges:
        union(a, b)
    return max(size[find(i)] for i in range(n)) / n


def structural_ladder(centroids):
    plots = sorted(centroids)
    pairs = []
    for i in range(len(plots)):
        for j in range(i + 1, len(plots)):
            a, b = plots[i], plots[j]
            ax, ay = centroids[a]
            bx, by = centroids[b]
            d = math.hypot(ax - bx, ay - by) / 1000.0
            if d <= 0:
                stop("stop_geometry_registry_not_reproduced", f"non-positive centroid distance between plots {a} and {b}")
            pairs.append((d, i, j))
    distances = sorted({d for d, _, _ in pairs})
    targets = [float(x) for x in CONTRACT["geometry_rule"]["lcc_targets"]]
    thresholds = []
    achieved = []
    for target in targets:
        chosen = None
        chosen_frac = None
        for t in distances:
            edges = [(i, j) for d, i, j in pairs if d <= t]
            frac = lcc_fraction(len(plots), edges)
            if frac >= target:
                chosen = t
                chosen_frac = frac
                break
        if chosen is None:
            stop("stop_structural_scales_insufficient", f"no structural threshold reaches LCC target {target}")
        thresholds.append(chosen)
        achieved.append(chosen_frac)
    distinct = len(set(thresholds))
    if distinct < int(CONTRACT["geometry_rule"]["minimum_distinct_positive_structural_thresholds"]):
        stop("stop_structural_scales_insufficient", f"only {distinct} distinct positive thresholds: {thresholds}")
    return {
        "targets": targets,
        "thresholds_km": thresholds,
        "achieved_lcc_fractions": achieved,
        "distinct_positive_thresholds": distinct,
        "pair_count": len(pairs),
        "fingerprint": fp({"plots": plots, "thresholds_km": thresholds, "targets": targets}),
    }


def main():
    result = base_result()
    try:
        raw = {}
        for role in CONTRACT["gate0"]["allowed_payloads"]:
            raw[role], result["source_profiles"][role] = get_allowed_bytes(role)

        # Documentation anchors: these are response-independent and protect the
        # surveyed-negative / fixed-plot interpretation from silent drift.
        methods_text = decode_utf8(raw["methods"], "methods")
        readme_text = decode_utf8(raw["rodent_readme"], "rodent_readme")
        if "24 experimental plots" not in methods_text or "49 permanent trapping stations" not in methods_text:
            stop("stop_response_independent_documentation_mismatch", "Portal methods no longer contain the frozen 24-plot / 49-station anchors")
        if "differentiate real zeros from missing data" not in readme_text:
            stop("stop_response_independent_documentation_mismatch", "Portal rodent README no longer contains the frozen real-zero/missing-data anchor")

        trapping_header, trapping_rows = csv_rows(raw["trapping"], "trapping", EXPECTED_HEADERS["trapping"])
        species_header, species_rows = csv_rows(raw["species"], "species")
        moon_header, moon_rows = csv_rows(raw["moon_dates"], "moon_dates", EXPECTED_HEADERS["moon_dates"])
        geometry_header, geometry_rows = csv_rows(raw["geometry"], "geometry", EXPECTED_HEADERS["geometry"])
        plot_header, plot_rows = csv_rows(raw["plot_history"], "plot_history", EXPECTED_HEADERS["plot_history"])
        treatment_header, treatment_rows = csv_rows(raw["treatment_registry"], "treatment_registry")

        # Species freeze.
        missing_species_cols = [c for c in CONTRACT["files"]["species"]["required_columns"] if c not in species_header]
        if missing_species_cols:
            stop("stop_species_registry_not_reproduced", f"species registry missing columns {missing_species_cols}")
        dm = [r for r in species_rows if (r.get("speciescode") or "").strip() == CONTRACT["focal_species"]["speciescode"]]
        if len(dm) != 1:
            stop("stop_species_registry_not_reproduced", f"DM species registry row count is {len(dm)}")
        dm = dm[0]
        if (dm.get("scientificname") or "").strip() != CONTRACT["focal_species"]["scientificname"]:
            stop("stop_species_registry_not_reproduced", "DM scientific name mismatch")
        for field, expected in CONTRACT["focal_species"]["required_registry_flags"].items():
            if as_int(dm.get(field), f"species.{field}") != int(expected):
                stop("stop_species_registry_not_reproduced", f"DM flag {field} mismatch")
        result["species"] = {
            "speciescode": "DM",
            "scientificname": CONTRACT["focal_species"]["scientificname"],
            "commonname": (dm.get("commonname") or "").strip(),
            "registry_row_fingerprint": fp({k: dm.get(k) for k in CONTRACT["files"]["species"]["required_columns"]}),
        }

        # Fixed 24-plot geometry from all stake coordinates; stake number labels
        # are intentionally not used as a uniqueness key.
        required_plots = set(int(x) for x in CONTRACT["analysis_registry"]["required_plot_ids"])
        stake_by_plot = defaultdict(list)
        for idx, r in enumerate(geometry_rows, start=2):
            if (r.get("type") or "").strip() != CONTRACT["geometry_rule"]["selected_type_token"]:
                continue
            plot = as_int(r.get("plot"), f"geometry row {idx} plot")
            if plot not in required_plots:
                continue
            east = as_float(r.get("east"), f"geometry row {idx} east")
            north = as_float(r.get("north"), f"geometry row {idx} north")
            stake_by_plot[plot].append((east, north))
        if set(stake_by_plot) != required_plots:
            stop("stop_geometry_registry_not_reproduced", f"stake geometry plots {sorted(stake_by_plot)} != frozen 1..24")
        centroids = {}
        stake_counts = {}
        for plot in sorted(required_plots):
            pts = stake_by_plot[plot]
            unique_pts = set(pts)
            if len(pts) != int(CONTRACT["geometry_rule"]["required_coordinate_rows_per_plot"]):
                stop("stop_geometry_registry_not_reproduced", f"plot {plot} has {len(pts)} stake coordinate rows, expected 49")
            if len(unique_pts) != int(CONTRACT["geometry_rule"]["required_unique_coordinate_pairs_per_plot"]):
                stop("stop_geometry_registry_not_reproduced", f"plot {plot} has {len(unique_pts)} unique stake coordinates, expected 49")
            centroids[plot] = (sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts))
            stake_counts[plot] = len(pts)
        ladder = structural_ladder(centroids)
        result["geometry"] = {
            "plot_count": len(centroids),
            "stake_rows_per_plot": {str(k): v for k, v in stake_counts.items()},
            "centroid_registry_fingerprint": fp([
                {"plot": p, "east": centroids[p][0], "north": centroids[p][1]} for p in sorted(centroids)
            ]),
            "structural_ladder": ladder,
        }

        # Trapping eligibility and surveyed-negative universe. Parse all rows
        # fail-closed; only the frozen eligibility rule determines inclusion.
        eligible = []
        all_trapping_plots = set()
        for idx, r in enumerate(trapping_rows, start=2):
            day = as_int(r.get("day"), f"trapping row {idx} day")
            month = as_int(r.get("month"), f"trapping row {idx} month")
            year = as_int(r.get("year"), f"trapping row {idx} year")
            period = as_int(r.get("period"), f"trapping row {idx} period")
            plot = as_int(r.get("plot"), f"trapping row {idx} plot")
            sampled = as_int(r.get("sampled"), f"trapping row {idx} sampled")
            effort = as_int(r.get("effort"), f"trapping row {idx} effort")
            qcflag = as_int(r.get("qcflag"), f"trapping row {idx} qcflag")
            all_trapping_plots.add(plot)
            if period > 0 and sampled == 1 and effort > 0 and qcflag == 1:
                eligible.append({
                    "day": day, "month": month, "year": year, "period": period,
                    "plot": plot, "effort": effort,
                })
        if not required_plots.issubset(all_trapping_plots):
            stop("stop_analysis_registry_not_reproduced", "not all 24 frozen plots occur in trapping table")
        keys = [(r["plot"], r["period"]) for r in eligible]
        if len(keys) != len(set(keys)):
            counts = Counter(keys)
            dup = [k for k, n in counts.items() if n > 1][:10]
            stop("stop_temporal_registry_not_reproduced", f"eligible trapping has duplicate plot-period keys: {dup}")

        # Moon calendar is an independent mapping from census period to a
        # continuous new-moon index; every selected positive period must exist.
        moon_by_period = {}
        for idx, r in enumerate(moon_rows, start=2):
            p = as_int(r.get("period"), f"moon row {idx} period")
            if p <= 0:
                continue
            if p in moon_by_period:
                stop("stop_temporal_registry_not_reproduced", f"duplicate positive period {p} in moon calendar")
            moon_by_period[p] = {
                "newmoonnumber": as_int(r.get("newmoonnumber"), f"moon row {idx} newmoonnumber"),
                "newmoondate": (r.get("newmoondate") or "").strip(),
                "censusdate": (r.get("censusdate") or "").strip(),
            }

        by_year = defaultdict(list)
        for r in eligible:
            by_year[r["year"]].append(r)
        complete_years = []
        year_profiles = {}
        min_per_plot = int(CONTRACT["temporal_window_rule"]["calendar_year_complete_if"]["minimum_eligible_periods_per_plot"])
        min_distinct = int(CONTRACT["temporal_window_rule"]["calendar_year_complete_if"]["minimum_distinct_positive_periods_in_year"])
        for year in sorted(by_year):
            yr = by_year[year]
            plot_periods = defaultdict(set)
            for r in yr:
                plot_periods[r["plot"]].add(r["period"])
            distinct_periods = sorted({r["period"] for r in yr})
            counts_per_plot = {p: len(plot_periods.get(p, set())) for p in sorted(required_plots)}
            is_complete = (
                set(plot_periods) == required_plots
                and min(counts_per_plot.values()) >= min_per_plot
                and len(distinct_periods) >= min_distinct
            )
            year_profiles[year] = {
                "eligible_plot_periods": len(yr),
                "distinct_periods": len(distinct_periods),
                "minimum_eligible_periods_per_plot": min(counts_per_plot.values()),
                "maximum_eligible_periods_per_plot": max(counts_per_plot.values()),
                "complete": is_complete,
            }
            if is_complete:
                complete_years.append(year)

        complete_set = set(complete_years)
        blocks = []
        if complete_years:
            for start in range(min(complete_years), max(complete_years) - 9):
                block = list(range(start, start + 11))
                if all(y in complete_set for y in block):
                    blocks.append(block)
        if not blocks:
            stop("stop_temporal_window_not_reproduced", "no 11-consecutive-year response-independent complete block exists")
        selected_years = max(blocks, key=lambda x: x[-1])
        selected_rows = [r for r in eligible if r["year"] in set(selected_years)]
        selected_periods = sorted({r["period"] for r in selected_rows})
        missing_moon = [p for p in selected_periods if p not in moon_by_period]
        if missing_moon:
            stop("stop_temporal_registry_not_reproduced", f"selected periods missing from moon calendar: {missing_moon[:10]}")

        # Plot/treatment history must independently cover every selected
        # plot-period at its actual trapping year/month.
        if plot_header != EXPECTED_HEADERS["plot_history"]:
            stop("stop_treatment_linkage_not_reproduced", f"plot history header mismatch: {plot_header}")
        plot_history = {}
        for idx, r in enumerate(plot_rows, start=2):
            key = (
                as_int(r.get("year"), f"plot history row {idx} year"),
                as_int(r.get("month"), f"plot history row {idx} month"),
                as_int(r.get("plot"), f"plot history row {idx} plot"),
            )
            if key in plot_history:
                stop("stop_treatment_linkage_not_reproduced", f"duplicate plot-history key {key}")
            plot_history[key] = r
        missing_history = []
        for r in selected_rows:
            key = (r["year"], r["month"], r["plot"])
            hist = plot_history.get(key)
            if hist is None or not (hist.get("treatment") or "").strip():
                missing_history.append(key)
        if missing_history:
            stop("stop_treatment_linkage_not_reproduced", f"selected eligible rows lack plot treatment history: {missing_history[:10]}")
        if treatment_header[:2] != ["plot", "term"]:
            stop("stop_treatment_linkage_not_reproduced", f"treatment registry prefix {treatment_header[:2]} != ['plot','term']")
        treatment_plots = [as_int(r.get("plot"), f"treatment registry plot") for r in treatment_rows]
        if set(treatment_plots) != required_plots or len(treatment_plots) != 24:
            stop("stop_treatment_linkage_not_reproduced", "treatment registry does not contain exactly one row for plots 1..24")

        role_by_year = {selected_years[0]: "initialization_only_not_scored"}
        role_by_year.update({y: "calibration" for y in selected_years[1:6]})
        role_by_year.update({y: "primary_heldout_outer_year" for y in selected_years[6:11]})
        selected_counts = Counter(r["year"] for r in selected_rows)
        selected_units = sorted((r["plot"], r["period"]) for r in selected_rows)
        result["registry"] = {
            "plot_count": 24,
            "plot_ids": sorted(required_plots),
            "analysis_registry_fingerprint": fp({
                "plots": sorted(required_plots),
                "centroids": [{"plot": p, "east": centroids[p][0], "north": centroids[p][1]} for p in sorted(centroids)],
            }),
        }
        result["temporal"] = {
            "eligible_plot_periods_all_qc_regular": len(eligible),
            "complete_years": complete_years,
            "selected_years": selected_years,
            "year_roles": {str(k): v for k, v in role_by_year.items()},
            "selected_eligible_plot_periods": len(selected_rows),
            "selected_eligible_plot_periods_by_year": {str(y): selected_counts[y] for y in selected_years},
            "selected_distinct_period_count": len(selected_periods),
            "selected_period_min": min(selected_periods),
            "selected_period_max": max(selected_periods),
            "selected_unit_registry_fingerprint": fp(selected_units),
            "year_profiles_for_selected_block": {str(y): year_profiles[y] for y in selected_years},
            "moon_calendar_linkage_pass": True,
        }
        result["treatment_linkage"] = {
            "selected_plot_period_rows_with_history": len(selected_rows),
            "missing_history_count": 0,
            "treatment_registry_plot_count": 24,
            "plot_history_linkage_pass": True,
            "fingerprint": fp([
                {
                    "year": r["year"], "month": r["month"], "plot": r["plot"],
                    "treatment": plot_history[(r["year"], r["month"], r["plot"])]["treatment"],
                }
                for r in sorted(selected_rows, key=lambda x: (x["period"], x["plot"]))
            ]),
        }

        result["status"] = "gate0_pass_response_free_registry_effort_time_geometry_and_treatment"
        result["reason"] = "Frozen PortalData response-independent sources reproduce the 24-plot registry, DM species identity, surveyed-negative effort semantics, latest 11-year complete window, plot treatment linkage, and >=3 structural scales while Portal_rodent.csv remains unopened"
        write(result)
        return 0
    except GateStop as exc:
        result["status"] = exc.status
        result["reason"] = exc.reason
        write(result)
        return 0
    except Exception as exc:
        result["status"] = "engineering_failure_pre_response"
        result["reason"] = f"{type(exc).__name__}: {exc}"
        write(result)
        return 1


if __name__ == "__main__":
    sys.exit(main())
