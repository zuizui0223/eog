#!/usr/bin/env python3
"""Fail-closed, METADATA-ONLY EOG external validation gate for Lepanthes.

This module must never fetch, deserialize or inspect lepa_all.csv or any biological
response row. It reads only the previously frozen public-catalog JSON description.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = (
    ROOT / "validation" / "eog_virtual_world_ecology_synthesis_v1"
    / "lepanthes_pre_response_catalog_v1.json"
)

EXPECTED_YEARS = {
    "1999": 1, "2000": 2, "2001": 2, "2002": 3, "2003": 1,
    "2004": 2, "2005": 2, "2006": 1, "2007": 2, "2008": 1,
}
EXPECTED_DISAGREEMENTS = {
    "horizontal_coordinate_x": ("x.coord.", "x.coord"),
    "horizontal_coordinate_y": ("y.coord.", "y.coord"),
    "vertical_coordinate": ("z.coordinate", "z.coord"),
    "survey_2004_visit_2": ("X7104", "X71704"),
}
KNOWN_VISIT_ORDER = [
    "X70199", "X20100", "X80100", "X10101", "X60101",
    "X10102", "X60102", "X120202", "X61003", "X12404",
    "X7104", "X12205", "X91705", "X72406", "X20307",
    "X61507", "X10208",
]
PENDING_GATES = (
    "PHYSICAL_VERSION_DIGEST_PINNED",
    "PHYSICAL_CSV_HEADER_INDEPENDENTLY_VERIFIED",
    "COLUMN_DICTIONARY_CONFLICTS_RESOLVED",
    "DISTINCT_RESPONSE_INDEPENDENT_PATCH_REGISTRY_VERIFIED",
    "PATCH_AND_VISIT_MISSINGNESS_SEMANTICS_VERIFIED",
    "DETECTION_PROCESS_INDEPENDENTLY_QUALIFIED",
    "SOURCE_LOSS_OR_TURNOVER_EVENT_INDEPENDENTLY_DEFINED",
)
# No inference or response-access scripts are imported, called or even accepted.
PROHIBITED_AUTHORIZATIONS = (
    "REAL_RESPONSE_OPENING_AUTHORIZED",
    "focal_csv_downloaded_in_this_audit",
    "observed_biological_rows_opened_in_this_audit",
    "response_rows_opened_in_this_audit",
    "response_row_scoring_authorized",
)


def audit_metadata_only(path: Path = DEFAULT_CATALOG) -> dict:
    raw = path.read_bytes()
    catalog = json.loads(raw.decode("utf-8"))
    if catalog["schema"] != "eog.lepanthes.pre_response_metadata_catalog.v1":
        raise ValueError("Unknown frozen metadata audit schema")

    src = catalog["sources"]
    dryad = src["dryad"]
    ecodata = src["ecodata"]
    primary = src["primary_paper"]
    contract = catalog["metadata_contract"]
    targets = catalog["target_and_comparator"]
    gates = catalog["current_gates"]
    decision = catalog["decision_rules"]

    if dryad["doi"] != "10.5061/dryad.9p8cz8wc6" or dryad["advertised_file"] != "lepa_all.csv":
        raise ValueError("Unexpected data source, must not retarget this frozen audit")
    if primary["doi"] != "10.1111/1365-2745.13361":
        raise ValueError("Unexpected comparator publication")
    if primary["main_models_compared"] != 290 or primary["patches_reported"] != 975:
        raise ValueError("Source-paper identity mismatch")
    if contract["first_year"] != 1999 or contract["last_year"] != 2008:
        raise ValueError("Historical survey period changed")
    if dryad["file_count_advertised"] != 1:
        raise ValueError("Published file inventory changed; requires fresh audit")

    c1 = dryad["dictionary_column_names"]
    c2 = ecodata["dictionary_column_names"]
    if len(c1) != 23 or len(c2) != 23 or len(set(c1)) != 23 or len(set(c2)) != 23:
        raise ValueError("Public 23-column dictionaries changed")
    visits = contract["dryad_visit_sequence"]
    if len(visits) != 17 or [v["column"] for v in visits] != KNOWN_VISIT_ORDER:
        raise ValueError("Frozen visit column sequence changed")
    if c1[5:-1] != KNOWN_VISIT_ORDER:
        raise ValueError("Dryad dictionary no longer matches visit sequence")
    if c1[0] != "UID" or c1[-1] != "Total_Moss_area":
        raise ValueError("Response-free patch ID and area definition changed")

    years = Counter(str(v["year"]) for v in visits)
    if dict(years) != EXPECTED_YEARS or contract["survey_count_per_year"] != EXPECTED_YEARS:
        raise ValueError("Year-by-year 17-visit inventory changed")
    if contract["one_visit_years"] != [1999, 2003, 2006, 2008]:
        raise ValueError("Single-visit year list changed")

    conflicts = contract["dictionary_conflicts"]
    observed = {
        x["semantic_field"]: (x["dryad"], x["ecodata"]) for x in conflicts
    }
    if observed != EXPECTED_DISAGREEMENTS:
        raise ValueError("Public dictionary disagreement is not independently resolved")
    expected_changed_positions = {
        (c1.index(dryad_name), c2.index(other_name))
        for dryad_name, other_name in EXPECTED_DISAGREEMENTS.values()
    }
    if len(expected_changed_positions) != 4:
        raise ValueError("Aliased columns are not four independent schema positions")
    mismatch_indices = {i for i, (a, z) in enumerate(zip(c1, c2)) if a != z}
    if mismatch_indices != {a for a, b in expected_changed_positions if a == b}:
        raise ValueError("Additional undocumented dictionary conflicts")

    if contract["allow_silent_alias_normalization"]:
        raise ValueError("Silent name repair invalidates response-blind audit")
    if contract["actual_csv_header_authorized_to_be_inferred_from_dictionary"]:
        raise ValueError("Dictionary is not a physical CSV header witness")
    if contract["separate_response_independent_patch_registry_verified"]:
        raise ValueError("A new independent registry requires a fresh qualification protocol")
    if src["dryad"]["publicly_advertised_physical_sha256"] is not None:
        raise ValueError("New checksum evidence requires a new versioned audit")
    if src["dryad"]["version_id_independently_verified"] is not None:
        raise ValueError("New Dryad version ID evidence requires new versioned audit")
    if src["dryad"]["physical_header_independently_verified"]:
        raise ValueError("Header qualification is not licensed by this metadata-only contract")

    # All permissions to consume the focal biological response remain false.
    if gates["DOI_AND_ADVERTISED_FILE_IDENTIFIED"] is not True:
        raise ValueError("DOI/file metadata identity unexpectedly lost")
    if gates["PRIOR_PUBLICATION_COMPARATOR_SPECIFIED"] is not True:
        raise ValueError("Strong published comparator may not be omitted")
    for name in PENDING_GATES + ("REAL_RESPONSE_OPENING_AUTHORIZED",):
        if gates[name] is not False:
            raise ValueError(f"Gate {name} cannot pass within this metadata-only contract")
    if any(dryad[name] is not False for name in
           ("downloaded_in_this_audit", "observed_biological_rows_opened_in_this_audit")):
        raise ValueError("Biological data accessed: cease metadata-only audit")
    if ecodata["response_rows_opened_in_this_audit"] is not False:
        raise ValueError("Derived response rows accessed: cease metadata-only audit")
    if targets["response_row_scoring_authorized"] is not False:
        raise ValueError("No model score may be computed from this metadata")
    if targets["new_ecological_source_loss_event_verified"] is not False:
        raise ValueError("Do not infer actual patch removal from dictionary fields")
    if targets["heldout_split_frozen"] is not False:
        raise ValueError("No validation split is qualified before source/observation gates")
    if decision["status"] != "STOP_WITHIN_DECLARED_PRE_RESPONSE_GATE":
        raise ValueError("Frozen stop status was retrospectively reclassified")
    if decision["terminal_code"] != "STOP_REGISTRY_SCHEMA_AND_DETECTION_UNQUALIFIED":
        raise ValueError("Frozen terminal code changed")
    if decision["no_new_biological_result"] is not True:
        raise ValueError("Cannot promote metadata screen to new biological evidence")

    return {
        "schema": "eog.lepanthes.response_blind_metadata_gate_receipt.v1",
        "status": decision["status"],
        "terminal_code": decision["terminal_code"],
        "catalog_sha256": hashlib.sha256(raw).hexdigest(),
        "doi": dryad["doi"],
        "published_reference": primary["doi"],
        "published_model_count": primary["main_models_compared"],
        "advertised_files": dryad["file_count_advertised"],
        "advertised_patches": primary["patches_reported"],
        "dictionary_columns": len(c1),
        "survey_columns": len(visits),
        "survey_per_year": dict(years),
        "column_conflict_fields": sorted(observed),
        "physical_header_verified": False,
        "physical_file_sha256_verified": False,
        "separate_patch_registry_verified": False,
        "independent_detection_calibration_verified": False,
        "source_loss_event_verified": False,
        "focal_response_rows_opened_by_this_script": False,
        "model_fits_performed_by_this_script": 0,
        "prediction_scores_calculated_by_this_script": 0,
        "unmet_gate_ids": list(PENDING_GATES),
        "conclusion": (
            "This retrospective source is NOT qualified for prospective source-loss "
            "inference under the declared EOG pre-response evidence contract. "
            "This is not a negative ecological result."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit_metadata_only(args.catalog)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({"status": result["status"], "terminal_code": result["terminal_code"],
                      "catalog_sha256": result["catalog_sha256"]}))


if __name__ == "__main__":
    main()
