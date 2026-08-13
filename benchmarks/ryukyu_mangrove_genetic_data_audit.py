"""Audit the released Ryukyu microsatellite files without computing genetic structure.

This script may run only after the response-free geographic/current-flow/EOG predictors
have been frozen. It reports release schema, sample/population identifiers, missingness,
and marker-column structure. It deliberately does not compute FST, allele-frequency
contrasts, migration, clustering, heterozygosity, or any EOG validation score.
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


def _classify(values: list[str]) -> str:
    finite = [value.strip() for value in values if value.strip() not in {"", "NA", "NaN", "nan", ".", "-9"}]
    if not finite:
        return "all_missing"
    try:
        for value in finite:
            float(value)
        return "numeric"
    except ValueError:
        return "text"


def audit(genotype_csv: str | Path, readme: str | Path, predictor_manifest: str | Path) -> dict[str, object]:
    genotype_path = Path(genotype_csv)
    readme_path = Path(readme)
    predictor_manifest_path = Path(predictor_manifest)
    predictor = json.loads(predictor_manifest_path.read_text(encoding="utf-8"))
    if predictor.get("status") != "retrospective-external-response-not-attached":
        raise ValueError("Ryukyu response-free predictor manifest is not frozen before data audit")
    if predictor.get("genetic_response_attached") is not False:
        raise ValueError("Ryukyu predictor manifest already contains a genetic response")

    with genotype_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("Ryukyu genotype CSV has no header")
        fields = [str(value).strip() for value in reader.fieldnames]
        rows = [{key: ("" if value is None else value.strip()) for key, value in row.items()} for row in reader]
    if not rows:
        raise ValueError("Ryukyu genotype CSV has no rows")

    columns = {}
    for field in fields:
        values = [row.get(field, "") for row in rows]
        missing = sum(value in {"", "NA", "NaN", "nan", ".", "-9"} for value in values)
        distinct = sorted(set(value for value in values if value not in {"", "NA", "NaN", "nan", ".", "-9"}))
        columns[field] = {
            "type": _classify(values),
            "n_missing": int(missing),
            "n_distinct_nonmissing": int(len(distinct)),
            "example_values": distinct[:5] if _classify(values) == "text" else [],
        }

    lower = {field.lower(): field for field in fields}
    population_candidates = [
        field for field in fields
        if any(token in field.lower() for token in ("pop", "site", "location", "locality"))
    ]
    id_candidates = [
        field for field in fields
        if any(token in field.lower() for token in ("sample", "individual", "ind", "id"))
    ]

    # Paired microsatellite allele columns are only proposed from header naming patterns;
    # no allele frequencies or between-population statistics are computed here.
    allele_like = [
        field for field in fields
        if any(token in field.lower() for token in ("allele", "locus", "marker", "ssr"))
        or field.lower().endswith(('.1', '.2', '_1', '_2', 'a1', 'a2'))
    ]

    readme_text = readme_path.read_text(encoding="utf-8-sig", errors="replace")
    return {
        "status": "ryukyu-mangrove-genetic-release-schema-audit",
        "genetic_structure_computed": False,
        "fst_computed": False,
        "migration_computed": False,
        "clustering_computed": False,
        "predictor_manifest_fingerprint": predictor["predictor_manifest_fingerprint"],
        "predictor_operator_fingerprint": predictor["operator_fingerprint"],
        "predictor_connectivity_fingerprint": predictor["connectivity_fingerprint"],
        "genotype_file": genotype_path.name,
        "genotype_sha256": _sha256(genotype_path),
        "genotype_size_bytes": genotype_path.stat().st_size,
        "readme_file": readme_path.name,
        "readme_sha256": _sha256(readme_path),
        "readme_size_bytes": readme_path.stat().st_size,
        "readme_mentions_7_markers": "7" in readme_text and "marker" in readme_text.lower(),
        "readme_mentions_11_loci": "11" in readme_text and "loci" in readme_text.lower(),
        "n_rows": len(rows),
        "n_columns": len(fields),
        "column_names": fields,
        "columns": columns,
        "population_column_candidates": population_candidates,
        "sample_id_column_candidates": id_candidates,
        "allele_like_column_candidates": allele_like,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--genotypes", type=Path, required=True)
    parser.add_argument("--readme", type=Path, required=True)
    parser.add_argument("--predictor-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.genotypes, args.readme, args.predictor_manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
