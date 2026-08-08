"""Freeze the primary A-Islands native-species cohort before any model outcomes.

Primary status rule:
- species must already pass the count-based distribution screen;
- `Status_APC` must be exactly `native` for that standardized species;
- `introduced` is excluded from the primary cohort;
- source-list `Native` values are retained as audit metadata but are not used to
  override the Australian Plant Census status.

No SDM, EOG, topology, bridge, or held-out performance enters this rule.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def freeze(status_audit: Path) -> tuple[list[dict[str, str]], dict[str, object]]:
    with status_audit.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("taxon status audit is empty")
    required = {
        "species", "source_record_count", "native_values", "naturalised_values",
        "endemic_values", "status_apc_values", "family_values",
    }
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"taxon status audit missing columns: {', '.join(sorted(missing))}")

    allowed_status = {"native", "introduced"}
    unexpected = sorted({row["status_apc_values"] for row in rows} - allowed_status)
    if unexpected:
        raise ValueError(f"unexpected Status_APC values before freezing cohort: {unexpected}")

    output: list[dict[str, str]] = []
    counts = {"native": 0, "introduced": 0}
    for row in sorted(rows, key=lambda item: item["species"]):
        status = row["status_apc_values"]
        counts[status] += 1
        included = status == "native"
        output.append({
            "species": row["species"],
            "primary_cohort_included": "1" if included else "0",
            "primary_status_rule": "Status_APC==native",
            "status_apc": status,
            "source_record_count": row["source_record_count"],
            "source_list_native_values_audit": row["native_values"],
            "family_values_audit": row["family_values"],
            "exclusion_reason": "" if included else "Status_APC_introduced",
        })

    included_count = sum(int(row["primary_cohort_included"]) for row in output)
    summary = {
        "distribution_eligible_taxa": len(rows),
        "primary_native_taxa": included_count,
        "excluded_introduced_taxa": counts["introduced"],
        "status_apc_counts": counts,
        "primary_status_rule": "Status_APC == native",
        "source_list_native_field_role": "audit_only_not_a_primary_exclusion_rule",
        "family_field_role": "audit_only_not_a_primary_exclusion_rule",
        "scientific_boundary": (
            "taxon/status freeze before model outcomes; no SDM, EOG, topology, bridge, or held-out performance used"
        ),
    }
    return output, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status-audit", type=Path, required=True)
    parser.add_argument("--output-cohort", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    args = parser.parse_args()

    rows, summary = freeze(args.status_audit)
    args.output_cohort.parent.mkdir(parents=True, exist_ok=True)
    with args.output_cohort.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary["cohort_sha256"] = _sha256(args.output_cohort)
    args.output_summary.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
