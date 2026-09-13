from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import urllib.request

from eog.v2.predictive_complementarity import PredictiveComplementarityDeclaration

from runner_core import (
    CONVENTIONAL_FEATURE_NAMES,
    build_prepared_rows,
    canonical_sha256,
    exact_count_gate,
    fit_and_score,
)

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "full_freeze_spec.json").read_text(encoding="utf-8"))
FINALIZER = json.loads((HERE / "pre_response_finalize_certificate.json").read_text(encoding="utf-8"))
GATE0 = json.loads((HERE / "gate0_certificate.json").read_text(encoding="utf-8"))
GATE1 = json.loads((HERE / "gate1_certificate.json").read_text(encoding="utf-8"))
GATE2 = json.loads((HERE / "gate2_header_certificate.json").read_text(encoding="utf-8"))
FOCAL = json.loads((HERE / "focal_species_selection_certificate.json").read_text(encoding="utf-8"))
OUT = Path("build/louisiana_marsh_bird_replication_1/terminal_result.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

AUDIT = {
    "sciencebase_metadata_requests": 0,
    "sciencebase_metadata_bytes_opened": 0,
    "response_independent_payload_requests": 0,
    "response_independent_payload_bytes_opened": 0,
    "selected_response_payload_requests": 0,
    "selected_response_payload_bytes_opened": 0,
    "selected_response_rows_seen": 0,
    "selected_response_rows_opened": False,
    "selected_response_values_opened": False,
    "unselected_species_payload_requests": 0,
    "unselected_species_payload_bytes_opened": 0,
    "exact_count_gate_executed": False,
    "model_fits": 0,
    "primary_outer_units_scored": 0,
}


class TerminalStop(RuntimeError):
    pass


def canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def emit(status: str, reason: str, *, exit_code: int = 0, **extra: object) -> None:
    payload = {
        "schema": "eog.louisiana_marsh_bird_once_only_terminal.v1",
        "attempt_id": FREEZE["attempt_id"],
        "status": status,
        "reason": reason,
        "audit": dict(AUDIT),
        **extra,
    }
    payload["fingerprint"] = canonical_json_sha256(payload)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if exit_code:
        raise SystemExit(exit_code)


def stop(status: str, reason: str, **extra: object) -> None:
    emit(status, reason, exit_code=3, **extra)


def verify_static_contracts() -> None:
    if FINALIZER["status"] != "full_freeze_machine_validated_response_rows_still_closed":
        raise TerminalStop("pre-response finalizer certificate is not PASS")
    if FINALIZER["full_freeze_spec_sha256"] != canonical_json_sha256(FREEZE):
        raise TerminalStop("full freeze canonical fingerprint mismatch")
    if FINALIZER["header_certificate_fingerprint"] != GATE2["result_fingerprint"]:
        raise TerminalStop("header certificate fingerprint mismatch")
    if GATE0["gate0_fingerprint"] != "5ce556acd5b119a7b451a3b8cca0fdb254ded2461014c1e2e8388abdaf6802cf":
        raise TerminalStop("Gate0 certificate drift")
    if GATE1["gate1_fingerprint"] != "4f3dd443ba06bbd0d2bd8a47ead538700522df4df58eb58d2afd8577e3428586":
        raise TerminalStop("Gate1 certificate drift")
    if FOCAL["selected_species"]["selected_response_file"] != "KIRA.csv":
        raise TerminalStop("focal species response file drift")
    if tuple(FREEZE["comparators"]["conventional_feature_names"]) != CONVENTIONAL_FEATURE_NAMES:
        raise TerminalStop("runner conventional features differ from full freeze")
    if FREEZE["layer_b_representation"]["representation_name"] != "symmetric_world_support_summary_v1":
        raise TerminalStop("Layer-B representation drift")


def get_item() -> dict:
    item_id = FREEZE["source_identity"]["sciencebase_item_id"]
    req = urllib.request.Request(
        f"https://www.sciencebase.gov/catalog/item/{item_id}?format=json",
        headers={"User-Agent": "EOG-Louisiana-KIRA-Outcome/1.0", "Accept": "application/json"},
    )
    AUDIT["sciencebase_metadata_requests"] += 1
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read(5_000_001)
        status = int(getattr(response, "status", 200))
    AUDIT["sciencebase_metadata_bytes_opened"] += len(body)
    if status != 200 or len(body) > 5_000_000:
        raise TerminalStop(f"ScienceBase metadata transport failure: status={status}, bytes={len(body)}")
    observed = hashlib.sha256(body).hexdigest()
    expected = FREEZE["source_identity"]["sciencebase_item_metadata_sha256"]
    if observed != expected:
        raise TerminalStop(f"ScienceBase metadata fingerprint changed: {observed} != {expected}")
    return json.loads(body.decode("utf-8"))


def file_map(item: dict) -> dict[str, dict]:
    files = {str(row.get("name") or ""): row for row in (item.get("files") or [])}
    expected = {
        FREEZE["source_identity"]["sites_file"][0]: FREEZE["source_identity"]["sites_file"],
        FREEZE["source_identity"]["samples_file"][0]: FREEZE["source_identity"]["samples_file"],
        FREEZE["source_identity"]["response_file"][0]: FREEZE["source_identity"]["response_file"],
    }
    for name, identity in expected.items():
        if name not in files:
            raise TerminalStop(f"frozen source asset missing: {name}")
        row = files[name]
        checksum = row.get("checksum") or {}
        if isinstance(checksum, dict):
            md5 = str(checksum.get("value") or checksum.get("checksum") or "")
        else:
            md5 = str(checksum)
        size = int(row.get("size") or 0)
        if md5 != str(identity[1]) or size != int(identity[2]):
            raise TerminalStop(f"source asset identity drift for {name}: md5={md5}, size={size}")
    return files


def download_response_independent(files: dict[str, dict], identity: list[object]) -> bytes:
    name, md5, expected_bytes = str(identity[0]), str(identity[1]), int(identity[2])
    url = files[name].get("downloadUri") or files[name].get("url")
    if not url:
        raise TerminalStop(f"no download URI for {name}")
    req = urllib.request.Request(
        str(url),
        headers={"User-Agent": "EOG-Louisiana-KIRA-Outcome/1.0", "Accept-Encoding": "identity"},
    )
    AUDIT["response_independent_payload_requests"] += 1
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read(expected_bytes + 1)
        status = int(getattr(response, "status", 200))
    AUDIT["response_independent_payload_bytes_opened"] += len(body)
    if status != 200 or len(body) != expected_bytes:
        raise TerminalStop(f"{name} transport/size mismatch: status={status}, bytes={len(body)}")
    observed_md5 = hashlib.md5(body).hexdigest()
    if observed_md5 != md5:
        raise TerminalStop(f"{name} MD5 mismatch: {observed_md5} != {md5}")
    return body


def parse_response_independent_tables(
    sites_payload: bytes,
    samples_payload: bytes,
) -> tuple[
    tuple[str, ...],
    dict[str, tuple[float, float]],
    dict[str, str],
    dict[str, str],
    dict[int, dict[str, object]],
]:
    sites_rows = list(csv.reader(io.StringIO(sites_payload.decode("utf-8-sig"))))
    samples_rows = list(csv.reader(io.StringIO(samples_payload.decode("utf-8-sig"))))
    if not sites_rows or sites_rows[0] != ["Site", "Latitude", "Longitude", "Marsh", "Habitat"]:
        raise TerminalStop("Sites.csv physical schema drift")
    if not samples_rows or samples_rows[0] != ["Sample Period", "Date", "Precipitation", "MinAirTemp"]:
        raise TerminalStop("Samples.csv physical schema drift")
    site_data = sites_rows[1:]
    sample_data = samples_rows[1:]
    if len(site_data) != 33 or len(sample_data) != 20:
        raise TerminalStop("Sites/Samples row-count drift")
    if canonical_sha256({"header": sites_rows[0], "rows": site_data}) != GATE0["sites"]["table_fingerprint"]:
        raise TerminalStop("Sites.csv table fingerprint drift")
    if canonical_sha256({"header": samples_rows[0], "rows": sample_data}) != GATE0["samples"]["table_fingerprint"]:
        raise TerminalStop("Samples.csv table fingerprint drift")

    sites = tuple(row[0].strip() for row in site_data)
    if len(set(sites)) != 33 or any(not site for site in sites):
        raise TerminalStop("invalid frozen site registry")
    coordinates = {row[0].strip(): (float(row[1]), float(row[2])) for row in site_data}
    marsh = {row[0].strip(): row[3].strip() for row in site_data}
    habitat = {row[0].strip(): row[4].strip() for row in site_data}
    samples: dict[int, dict[str, object]] = {}
    for row in sample_data:
        period = int(row[0])
        raw_date = row[1].strip()
        month, day, year = (int(value) for value in raw_date.split("/"))
        date_text = f"{year:04d}-{month:02d}-{day:02d}"
        samples[period] = {
            "date": date_text,
            "precipitation": float(row[2]),
            "min_air_temp": float(row[3]),
        }
    if set(samples) != set(range(1, 21)):
        raise TerminalStop("Samples.csv period registry drift")
    return sites, coordinates, marsh, habitat, samples


def full_response_get(files: dict[str, dict]) -> bytes:
    identity = FREEZE["source_identity"]["response_file"]
    name, md5, expected_bytes = str(identity[0]), str(identity[1]), int(identity[2])
    row = files[name]
    url = row.get("downloadUri") or row.get("url")
    if not url:
        raise TerminalStop("KIRA.csv has no download URI")
    req = urllib.request.Request(
        str(url),
        headers={"User-Agent": "EOG-Louisiana-KIRA-Outcome/1.0", "Accept-Encoding": "identity"},
    )
    AUDIT["selected_response_payload_requests"] += 1
    with urllib.request.urlopen(req, timeout=60) as response:
        status = int(getattr(response, "status", 200))
        content_length_raw = response.headers.get("Content-Length")
        if content_length_raw and int(content_length_raw) != expected_bytes:
            raise TerminalStop(
                f"KIRA.csv Content-Length mismatch: {content_length_raw} != {expected_bytes}"
            )
        body = response.read(expected_bytes + 1)
    AUDIT["selected_response_payload_bytes_opened"] += len(body)
    if status != 200 or len(body) != expected_bytes:
        raise TerminalStop(f"KIRA.csv transport/size mismatch: status={status}, bytes={len(body)}")
    observed_md5 = hashlib.md5(body).hexdigest()
    if observed_md5 != md5:
        raise TerminalStop(f"KIRA.csv streamed MD5 mismatch: {observed_md5} != {md5}")
    AUDIT["selected_response_rows_opened"] = True
    AUDIT["selected_response_values_opened"] = True
    return body


def parse_response(payload: bytes, frozen_sites: tuple[str, ...]) -> dict[tuple[int, str], int]:
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise TerminalStop(f"KIRA.csv UTF-8 decode failure: {exc}") from exc
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        raise TerminalStop("KIRA.csv empty")
    expected_header = FREEZE["response_identity"]["physical_header"]
    if rows[0] != expected_header:
        raise TerminalStop(f"KIRA.csv physical header drift: {rows[0]}")
    data = rows[1:]
    AUDIT["selected_response_rows_seen"] = len(data)
    if len(data) != 33:
        raise TerminalStop(f"KIRA.csv row count mismatch: {len(data)} != 33")
    if any(len(row) != 21 for row in data):
        raise TerminalStop("KIRA.csv row width differs from frozen 21-column schema")

    site_rows: dict[str, list[str]] = {}
    for row in data:
        site = row[0].strip()
        if not site or site in site_rows:
            raise TerminalStop(f"KIRA.csv duplicate/empty site row: {site!r}")
        site_rows[site] = row
    if set(site_rows) != set(frozen_sites):
        raise TerminalStop(
            f"KIRA.csv site registry mismatch: missing={sorted(set(frozen_sites)-set(site_rows))}, "
            f"unexpected={sorted(set(site_rows)-set(frozen_sites))}"
        )

    unavailable = set(FREEZE["response_semantics"]["unavailable_tokens_case_sensitive"])
    labels: dict[tuple[int, str], int] = {}
    for site in frozen_sites:
        row = site_rows[site]
        for period in range(1, 21):
            token = row[period].strip()
            if token == "1":
                labels[(period, site)] = 1
            elif token == "0":
                labels[(period, site)] = 0
            elif token in unavailable:
                continue
            else:
                raise TerminalStop(
                    f"unexpected KIRA response token at site={site}, period={period}: {token!r}"
                )
    return labels


def complementarity_declaration() -> PredictiveComplementarityDeclaration:
    metrics = FREEZE["metrics_decision"]
    return PredictiveComplementarityDeclaration(
        metric_name=metrics["primary_metric"],
        lower_is_better=metrics["lower_is_better"],
        expected_outer_unit_count=metrics["primary_outer_unit_count"],
        favorable_min_augmented_wins=metrics["favorable_min_augmented_wins"],
        adverse_min_baseline_wins=metrics["adverse_min_baseline_wins"],
        learner_fit_fingerprint=FINALIZER["learner_fit_fingerprint"],
        response_endpoint_fingerprint=FINALIZER["response_endpoint_fingerprint"],
        split_fingerprint=FINALIZER["split_fingerprint"],
        external_feature_fingerprint=FINALIZER["external_feature_fingerprint"],
        eog_feature_fingerprint=FINALIZER["eog_feature_fingerprint"],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre-response-only", action="store_true")
    args = parser.parse_args()
    try:
        verify_static_contracts()
        item = get_item()
        files = file_map(item)
        sites_payload = download_response_independent(files, FREEZE["source_identity"]["sites_file"])
        samples_payload = download_response_independent(files, FREEZE["source_identity"]["samples_file"])
        sites, coordinates, marsh, habitat, samples = parse_response_independent_tables(
            sites_payload, samples_payload
        )
        if canonical_sha256(list(sites)) == "":
            raise TerminalStop("impossible site registry fingerprint")
        # Gate1 certificates bind the geometry/registry generated from these exact table bytes.
        if len(sites) != GATE1["site_registry"]["site_count"]:
            raise TerminalStop("Gate1 site count mismatch")
        declaration = complementarity_declaration()
        if declaration.fingerprint != FINALIZER["predictive_complementarity_declaration_fingerprint"]:
            raise TerminalStop("paired declaration fingerprint drift")

        if args.pre_response_only:
            emit(
                "pre_response_boundary_pass",
                "all production checks completed through the boundary immediately before the sole full KIRA.csv GET",
                row_access_authorized=False,
                full_freeze_spec_sha256=FINALIZER["full_freeze_spec_sha256"],
                declaration_fingerprint=declaration.fingerprint,
                site_count=len(sites),
                sample_count=len(samples),
            )
            return

        response_payload = full_response_get(files)
        labels = parse_response(response_payload, sites)

        temporal = FREEZE["temporal_split"]
        count = exact_count_gate(
            labels,
            calibration_periods=temporal["scored_calibration_sample_periods"],
            heldout_periods=temporal["heldout_sample_periods_chronological"],
            primary_outer_units=temporal["heldout_sample_periods_chronological"],
            minima=FREEZE["count_gate"],
        )
        AUDIT["exact_count_gate_executed"] = True
        count_payload = {
            "calibration_events": count.calibration_events,
            "calibration_non_events": count.calibration_non_events,
            "heldout_events": count.heldout_events,
            "heldout_non_events": count.heldout_non_events,
            "primary_outer_units_with_both_classes": count.primary_outer_units_with_both_classes,
            "passed": count.passed,
        }
        if not count.passed:
            stop(
                "terminal_non_estimable_exact_count_gate",
                "frozen exact King Rail count gate failed; zero scientific model fits/scores",
                count_gate=count_payload,
            )

        features = build_prepared_rows(
            sites=sites,
            site_coordinates=coordinates,
            site_marsh=marsh,
            site_habitat=habitat,
            samples=samples,
            chronological_periods=temporal["chronological_sample_period_order"],
            initialization_period=temporal["initialization_only_sample_period"],
            labels=labels,
            thresholds=FREEZE["world_scale"]["geometry_thresholds_km"],
            structural_gate_fingerprint=FREEZE["structural_adequacy"]["gate1_fingerprint"],
        )
        score = fit_and_score(
            rows=features.rows,
            calibration_periods=temporal["scored_calibration_sample_periods"],
            heldout_periods=temporal["heldout_sample_periods_chronological"],
            rf_hyperparameters=FREEZE["preprocessing_model_fit"]["hyperparameters"],
            complementarity_declaration=declaration,
            probability_clip=FREEZE["metrics_decision"]["probability_clip"],
            tie_tolerance=FREEZE["metrics_decision"]["tie_tolerance"],
        )
        AUDIT["model_fits"] = int(score["model_fit_count"])
        AUDIT["primary_outer_units_scored"] = int(score["heldout_outer_units_scored"])
        emit(
            score["status"],
            "frozen fresh paired King Rail endpoint completed without post-response redesign",
            count_gate=count_payload,
            prepared_row_count=len(features.rows),
            final_surviving_world_ids=list(features.final_surviving_world_ids),
            local_worlds_eliminated=list(features.local_worlds_eliminated),
            paired_result=score,
            full_response_md5=hashlib.md5(response_payload).hexdigest(),
            raw_response_persisted=False,
        )
    except TerminalStop as exc:
        if AUDIT["selected_response_rows_opened"]:
            stop("terminal_post_response_contract_failure", str(exc))
        else:
            stop("terminal_pre_response_execution_stop", str(exc))
    except Exception as exc:
        if AUDIT["selected_response_rows_opened"]:
            stop("terminal_post_response_execution_failure", f"{type(exc).__name__}: {exc}")
        else:
            stop("terminal_pre_response_execution_stop", f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
