#!/usr/bin/env python3
"""Exploratory Glanville source-conditioned one-hop relaxation on real tables.

NO historical movement or founder inference. Archives must match frozen source SHA;
positive transitions are observed statuses, not certified colonisations. Only aggregate
results are archived; no individual patch, family, genotype or coordinate is exported.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import statistics
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile


class SourceStop(Exception):
    pass


def _str(v) -> str:
    return str(v if v is not None else "").strip()


def _number(v):
    try:
        out = float(_str(v))
        return out if math.isfinite(out) else None
    except (TypeError, ValueError, OverflowError):
        return None


def _year(v):
    n = _number(v)
    return int(n) if n is not None and n == int(n) else None


def _quantile(values, p):
    v = sorted(values)
    if not v:
        return None
    x = (len(v) - 1) * p
    lo = int(math.floor(x)); hi = int(math.ceil(x))
    return float(v[lo] * (hi - x) + v[hi] * (x - lo)) if lo != hi else float(v[lo])


def _download(src, folder):
    path = folder / src["filename"]
    sha = hashlib.sha256()
    size = 0
    req = urllib.request.Request(src["archive_url"], headers={
        "Accept": "*/*", "User-Agent": "EOG-frozen-Glanville-exploratory-analysis/1.0"
    })
    try:
        with urllib.request.urlopen(req, timeout=50) as response, path.open("wb") as out:
            for block in iter(lambda: response.read(1024 * 1024), b""):
                size += len(block)
                if size > src["max_bytes"]:
                    raise SourceStop("STOP_ARCHIVE_BYTE_BUDGET")
                sha.update(block)
                out.write(block)
    except urllib.error.HTTPError as exc:
        raise SourceStop("STOP_TRANSPORT_HTTP_" + str(exc.code) + "_" + src["tag"]) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise SourceStop("STOP_TRANSPORT_" + type(exc).__name__ + "_" + src["tag"]) from exc
    if sha.hexdigest() != src["sha256"]:
        raise SourceStop("STOP_SOURCE_SHA_MISMATCH_" + src["tag"])
    return path


def _rows(path, kind, member, sep):
    if kind == "zip":
        arc = zipfile.ZipFile(path)
        if member not in arc.namelist():
            arc.close(); raise SourceStop("STOP_MISSING_SOURCE_TABLE_" + member)
        raw = arc.open(member)
    else:
        arc = tarfile.open(path, "r:gz")
        try:
            raw = arc.extractfile(arc.getmember(member))
        except KeyError as exc:
            arc.close(); raise SourceStop("STOP_MISSING_SOURCE_TABLE_" + member) from exc
        if raw is None:
            arc.close(); raise SourceStop("STOP_NOT_REGULAR_FILE_" + member)
    with arc:
        with raw:
            with io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="") as text:
                first = text.readline()
                if first.lower().strip().startswith("sep="):
                    dialect_sep = first.strip()[4:] or sep
                    lines = iter(text)
                else:
                    dialect_sep = sep
                    lines = itertools.chain((first,), text)
                reader = csv.DictReader(lines, delimiter=dialect_sep)
                if not reader.fieldnames:
                    raise SourceStop("STOP_NO_HEADER_" + member)
                for row in reader:
                    yield row


def _load_tables(occ, geno):
    network = {}
    for row in _rows(occ, "zip", "data/patch_network.tsv", "\t"):
        patch = _str(row.get("patch")); x = _number(row.get("x")); y = _number(row.get("y"))
        if patch and x is not None and y is not None:
            network[patch] = (x, y)
    survey = {}
    source_count = 0
    for row in _rows(occ, "zip", "data/survey_data.tsv", "\t"):
        patch = _str(row.get("patch")); year = _year(row.get("year"))
        if patch and year is not None:
            source_count += 1
            key = (year, patch)
            if key in survey:
                raise SourceStop("STOP_SURVEY_DUPLICATE_PATCH_YEAR")
            survey[key] = (
                _number(row.get("population")),
                _number(row.get("plantago")),
                _number(row.get("veronica")),
            )
    genotype = {}
    gene_coord = defaultdict(list)
    for row in _rows(geno, "tar.gz", "master-input.csv", ","):
        ident = _str(row.get("ID")); year = _year(row.get("Year"))
        patch = _str(row.get("Patch")); region = _str(row.get("Region"))
        x = _number(row.get("Patch Centroid_X (ETRS-TM35FIN)"))
        y = _number(row.get("Patch Centroid_Y (ETRS-TM35FIN)"))
        if ident and year is not None:
            key = (year, ident)
            if key in genotype:
                raise SourceStop("STOP_GENOTYPE_DUPLICATE_ID_YEAR")
            genotype[key] = (patch, region)
        if patch and x is not None and y is not None:
            gene_coord[patch].append((x, y))
    families = {}
    for row in _rows(geno, "tar.gz", "master-output.csv", ","):
        ident = _str(row.get("ID")); year = _year(row.get("Year"))
        fam = _str(row.get("COLONY2 Family ID"))
        if ident and year is not None:
            key = (year, ident)
            if key in families:
                raise SourceStop("STOP_FAMILY_DUPLICATE_ID_YEAR")
            families[key] = fam
    return network, survey, genotype, gene_coord, families, source_count


def _check_geographic_contract(network, gene_coord, genotype, families, protocol):
    overlap = []
    for patch, pairs in gene_coord.items():
        if patch in network:
            gx = statistics.median(v[0] for v in pairs)
            gy = statistics.median(v[1] for v in pairs)
            xx, yy = network[patch]
            overlap.append(math.hypot(gx - xx, gy - yy))
    matched = set(genotype) & set(families)
    total = len(genotype)
    rate = len(matched) / total if total else 0.0
    result = {
        "genotype_individual_year_keys": total,
        "family_individual_year_keys": len(families),
        "individual_year_matched": len(matched),
        "individual_year_match_fraction": rate,
        "shared_coordinate_patch_count": len(overlap),
        "matched_patch_coordinate_residual_m_median": _quantile(overlap, 0.5),
        "matched_patch_coordinate_residual_m_p95": _quantile(overlap, 0.95),
        "projection_reference": "genetic input header declares ETRS-TM35FIN; occupancy network matching via numerical residual only",
    }
    check = protocol["genetic_coordinate_verification"]
    if (len(overlap) < check["minimum_paired_patches"]
        or result["matched_patch_coordinate_residual_m_median"] > check["median_max_m"]
        or result["matched_patch_coordinate_residual_m_p95"] > check["q95_max_m"]):
        raise SourceStop("STOP_CRS_NUMERICAL_CONCORDANCE_FAILED")
    if rate < protocol["family_id_minimum_match_fraction"]:
        raise SourceStop("STOP_FAMILY_ID_JOIN_COVERAGE")
    return result


def _family_summary(network, genotype, families, years):
    groups = defaultdict(set)
    joined = set(genotype) & set(families)
    for key in joined:
        year, _ = key
        patch, region = genotype[key]
        family = families[key]
        if year in years and patch in network and family and region:
            groups[(year, region, family)].add(patch)
    pair_distances = []
    multi = 0
    for patches in groups.values():
        if len(patches) >= 2:
            multi += 1
            for a, b in itertools.combinations(sorted(patches), 2):
                (x, y), (xx, yy) = network[a], network[b]
                if a != b:
                    pair_distances.append(math.hypot(x - xx, y - yy) / 1000.0)
    return {
        "family_year_region_groups_with_spatial_ids": len(groups),
        "reconstructed_family_groups_spanning_multiple_patches": multi,
        "undirected_cross_patch_pairs": len(pair_distances),
        "distance_km_median": _quantile(pair_distances, 0.5),
        "distance_km_q90": _quantile(pair_distances, 0.9),
        "distance_km_max": max(pair_distances) if pair_distances else None,
        "interpretation": "undirected same-year reconstructed sib-group patch separation, NOT source direction or colonization history",
    }


def _eligible_host(row):
    if row is None:
        return None
    pop, pl, ve = row
    if pl is None or ve is None or not 0 <= pl <= 3 or not 0 <= ve <= 3:
        return None
    return (pl, ve)


def _radius_for_year(year, policy, network, survey, delta_values):
    targets = []
    sources = []
    excluded = {"target_missing_tminus1": 0, "target_missing_host": 0, "target_missing_xy": 0,
                "source_missing_host_or_xy": 0}
    seen_sources = set()
    for (yy, patch), row in survey.items():
        if yy != year or row[0] is None or row[0] <= 0:
            continue
        prior = survey.get((year - 1, patch))
        if prior is None or prior[0] is None:
            excluded["target_missing_tminus1"] += 1
            continue
        if prior[0] != 0:
            continue
        host = _eligible_host(prior)
        if host is None:
            excluded["target_missing_host"] += 1
            continue
        if patch not in network:
            excluded["target_missing_xy"] += 1
            continue
        targets.append((patch, host, network[patch]))
    sy = (year - 1,) if policy == "previous_year_recorded_positive" else (year - 2, year - 1)
    for yy in sy:
        for (cy, patch), row in survey.items():
            if cy != yy or row[0] is None or row[0] <= 0:
                continue
            host = _eligible_host(row)
            if host is None or patch not in network:
                excluded["source_missing_host_or_xy"] += 1
                continue
            # Reuse last known eligible timepoint for a source in the two-year model.
            if patch in seen_sources:
                continue
            seen_sources.add(patch)
            sources.append((patch, host, network[patch]))
    table = []
    for delta in delta_values:
        per_target_min = []
        impossible_targets = 0
        for tp, host, (x, y) in targets:
            distances = []
            for sp, sh, (xx, yy) in sources:
                # Same-patch t-2 source may be allowed by declared alternate policy;
                # it expresses local recurrence, not an observed dispersal event.
                hgap = max(abs(host[0] - sh[0]), abs(host[1] - sh[1]))
                if hgap <= delta:
                    distances.append(math.hypot(x - xx, y - yy) / 1000.0)
            if distances:
                per_target_min.append(min(distances))
            else:
                impossible_targets += 1
        table.append({
            "host_gap_tolerance": delta,
            "targets_with_at_least_one_allowed_source": len(per_target_min),
            "targets_without_allowed_source": impossible_targets,
            "max_of_nearest_compatible_source_km": max(per_target_min) if impossible_targets == 0 and per_target_min else None,
            "median_nearest_compatible_source_km": _quantile(per_target_min, 0.5),
            "q90_nearest_compatible_source_km": _quantile(per_target_min, 0.9),
            "reference_nearest_distance_km": delta == max(delta_values),
        })
    feasible = [row for row in table if row["max_of_nearest_compatible_source_km"] is not None]
    frontier = []
    for point in feasible:
        dominated = any(
            other is not point and
            other["max_of_nearest_compatible_source_km"] <= point["max_of_nearest_compatible_source_km"] and
            other["host_gap_tolerance"] <= point["host_gap_tolerance"] and
            (other["max_of_nearest_compatible_source_km"] < point["max_of_nearest_compatible_source_km"] or
             other["host_gap_tolerance"] < point["host_gap_tolerance"])
            for other in feasible
        )
        if not dominated:
            frontier.append({
                "minimum_required_step_km": point["max_of_nearest_compatible_source_km"],
                "minimum_ordinal_host_tolerance": point["host_gap_tolerance"],
            })
    return {
        "year": year, "source_policy": policy,
        "eligible_newly_recorded_positive_targets": len(targets),
        "eligible_candidate_source_patches": len(sources),
        "exclusion_counts": excluded,
        "conditional_radius_by_host_tolerance": table,
        "pareto_minimum_absolute_limits": frontier,
        "status": "estimable" if frontier else "NON_ESTIMABLE_WITH_DECLARED_SOURCES",
    }


def run_analysis(protocol, output):
    result = {
        "schema_version": 1,
        "status": "STOP_UNSTARTED",
        "claim_boundary": "exploratory conditional recorded-positive support, not actual colonisation or dispersal",
        "source_shas": {}, "models_fit": 0, "EOG_WF_new_endpoints": 0,
    }
    try:
        with tempfile.TemporaryDirectory(prefix="eog_real_minrelax_") as d:
            path = Path(d)
            refs = {
                "schulz2019_occupancy": {
                    "archive_url": "https://zenodo.org/records/4987060/files/ECOG-04799.zip?download=1",
                    "filename": "ECOG-04799.zip",
                    "tag": "schulz2019_occupancy",
                    "sha256": protocol["source_evidence"]["2019_occupancy_sha256"],
                    "max_bytes": 5000000
                },
                "fountain2017_families": {
                    "archive_url": "https://zenodo.org/records/5010194/files/supplementary-data-COLONY2.tar.gz?download=1",
                    "filename": "supplementary-data-COLONY2.tar.gz",
                    "tag": "fountain2017_families",
                    "sha256": protocol["source_evidence"]["2017_family_sha256"],
                    "max_bytes": 30000000
                },
            }
            paths = {key: _download(v, path) for key,v in refs.items()}
            result["source_shas"] = {k:v["sha256"] for k,v in refs.items()}
            network, survey, genotype, gene_coord, families, n_survey = _load_tables(
                paths["schulz2019_occupancy"], paths["fountain2017_families"]
            )
            result["source_record_counts"] = {
                "survey": n_survey, "spatial_patches": len(network),
                "genotype_individual_years": len(genotype),
                "family_individual_years": len(families)
            }
            result["coordinate_family_join_qc"] = _check_geographic_contract(
                network, gene_coord, genotype, families, protocol
            )
            years = tuple(protocol["years"])
            result["reconstructed_family_spatial_summary"] = _family_summary(
                network, genotype, families, years
            )
            delta_values = tuple(protocol["environmental_threshold_grid"])
            policies = (protocol["primary_source_policy"], protocol["sensitivity_source_policy"])
            result["annual_minimum_relaxation"] = [
                _radius_for_year(year, policy, network, survey, delta_values)
                for year in years for policy in policies
            ]
            result["status"] = "EXPLORATORY_EMPIRICAL_MINRELAX_CONDITIONAL_ESTIMATES"
            result["barrier_axis"] = "NOT_ESTIMATED_WITHOUT_INDEPENDENT_BARRIER_DATA"
            result["historical_source_identity"] = "NOT_IDENTIFIED"
    except (SourceStop, ValueError, zipfile.BadZipFile, tarfile.TarError, csv.Error) as exc:
        result["status"] = str(exc) if isinstance(exc, SourceStop) else "STOP_RUNTIME_SOURCE_OR_SCHEMA"
        result["error_type"] = type(exc).__name__
    output.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    result["fingerprint_without_self_hash"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    output.write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "years": len(result.get("annual_minimum_relaxation", [])),
        "receipt": str(output),
    }, sort_keys=True))
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", type=Path, default=Path("validation/glanville_minrelax_empirical_v1/protocol_v1.json"))
    ap.add_argument("--output", type=Path, default=Path("results/glanville_minrelax_empirical_v1/result.json"))
    args = ap.parse_args()
    contract = json.loads(args.protocol.read_text(encoding="utf-8"))
    run_analysis(contract, args.output)


if __name__ == "__main__":
    main()
