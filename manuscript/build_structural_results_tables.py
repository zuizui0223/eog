#!/usr/bin/env python3
"""Build structural-manuscript results tables from frozen evidence."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manuscript/result_tables/result_table_manifest.json"
OUT = ROOT / "manuscript/result_tables"


class TableContractError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TableContractError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected object in {path}")
    return value


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def recursive_key_values(value: Any, key: str) -> list[Any]:
    found: list[Any] = []
    if isinstance(value, dict):
        for current_key, current_value in value.items():
            if current_key == key:
                found.append(current_value)
            found.extend(recursive_key_values(current_value, key))
    elif isinstance(value, list):
        for item in value:
            found.extend(recursive_key_values(item, key))
    return found


def fmt(value: str | float | int | None, digits: int = 6) -> str:
    if value is None or value == "":
        return ""
    return f"{float(value):.{digits}f}"


def classify(effect: float, low: float, high: float, *, favourable_high: bool) -> str:
    if low <= 0.0 <= high:
        return "uncertain"
    if favourable_high:
        return "favourable" if effect > 0.0 else "adverse"
    return "favourable" if effect < 0.0 else "adverse"


def validate_inputs(manifest: dict[str, Any]) -> dict[str, Any]:
    require(manifest.get("schema_version") == "eog_structural_results_tables_v2", "unexpected table schema")
    inputs = manifest["inputs"]
    for name in ("aislands_mode_estimates", "aislands_applicability", "tanzania_aggregate_contrasts"):
        path = ROOT / inputs[name]["path"]
        require(path.is_file(), f"missing frozen input: {path}")
        require(sha256(path) == inputs[name]["sha256"], f"frozen input SHA changed: {name}")

    ais_primary = load_json(ROOT / inputs["aislands_primary_expected"]["path"])
    require(
        ais_primary.get("species_output_sha256") == inputs["aislands_primary_expected"]["expected_species_output_sha256"],
        "A-Islands primary species fingerprint changed",
    )
    ais_strong = load_json(ROOT / inputs["aislands_strong_reference"]["path"])
    require(
        ais_strong.get("result_fingerprint") == inputs["aislands_strong_reference"]["result_fingerprint"],
        "A-Islands strong-reference result fingerprint changed",
    )
    require(ais_strong.get("status") == "first_and_only_authoritative_island_isolation_adequacy_execution", "unexpected A-Islands strong-reference status")
    ais_qa = load_json(ROOT / inputs["aislands_strong_reference_qa"]["path"])
    require(
        ais_qa.get("source_result_fingerprint") == inputs["aislands_strong_reference_qa"]["source_result_fingerprint"],
        "A-Islands strong-reference QA fingerprint changed",
    )

    tanzania = load_json(ROOT / inputs["tanzania_expected"]["path"])
    fingerprints = recursive_key_values(tanzania, "result_fingerprint")
    require(inputs["tanzania_expected"]["result_fingerprint"] in fingerprints, "Tanzania result fingerprint changed")
    return {"aislands_primary": ais_primary, "aislands_strong": ais_strong, "aislands_qa": ais_qa, "tanzania": tanzania}


def build_table3(manifest: dict[str, Any], evidence: dict[str, Any]) -> list[dict[str, str]]:
    inputs = manifest["inputs"]
    mode_rows = {row["quantity"]: row for row in read_csv(ROOT / inputs["aislands_mode_estimates"]["path"])}
    ais_primary = evidence["aislands_primary"]
    combined = mode_rows["combined"]
    require(abs(float(combined["effect"]) - float(ais_primary["overall_conditional_concordance"])) < 1e-12, "A-Islands primary effect mismatch")
    require(abs(float(combined["ci_low"]) - float(ais_primary["bootstrap_95_ci"][0])) < 1e-12, "A-Islands primary lower CI mismatch")
    require(abs(float(combined["ci_high"]) - float(ais_primary["bootstrap_95_ci"][1])) < 1e-12, "A-Islands primary upper CI mismatch")

    rows: list[dict[str, str]] = []
    for quantity in manifest["table_3"]["aislands_rows"]:
        src = mode_rows[quantity]
        effect = float(src["effect"])
        low = float(src["ci_low"])
        high = float(src["ci_high"])
        null = float(src["null_value"])
        shifted_low, shifted_high = low - null, high - null
        interpretation = "favourable" if shifted_low > 0 else "uncertain" if shifted_low <= 0 <= shifted_high else "adverse"
        rows.append({
            "system": "A-Islands",
            "analysis": src["label"],
            "metric": "conditional concordance",
            "effect_definition": "higher than 0.5 favours added structural ordering information",
            "n_species": src["n_species"],
            "n_matched": "",
            "effect": fmt(effect),
            "ci_low": fmt(low),
            "ci_high": fmt(high),
            "null_value": fmt(null),
            "sign_flip_p": fmt(ais_primary["sign_flip_two_sided_p"], 8) if quantity == "combined" else "",
            "interpretation": interpretation,
        })

    ais_strong = evidence["aislands_strong"]
    strong_metrics = {
        "log_loss": (
            ais_strong["primary"]["species_macro_mean"],
            ais_strong["primary"]["bootstrap_95_ci"],
            ais_strong["primary"]["sign_flip_two_sided_p"],
            "log loss difference",
        ),
        "brier": (
            ais_strong["secondary"]["species_macro_mean"],
            ais_strong["secondary"]["bootstrap_95_ci"],
            ais_strong["secondary"]["sign_flip_two_sided_p"],
            "Brier difference",
        ),
    }
    for metric in manifest["table_3"]["aislands_strong_reference_metrics"]:
        effect, ci, p_value, label = strong_metrics[metric]
        effect = float(effect)
        low, high = map(float, ci)
        rows.append({
            "system": "A-Islands",
            "analysis": "Prospective strong island reference | C vs R3",
            "metric": label,
            "effect_definition": "candidate C minus frozen R3 reference; negative favours EOG",
            "n_species": str(ais_strong["taxa_estimable"]),
            "n_matched": str(ais_strong["heldout_predictions"]),
            "effect": fmt(effect),
            "ci_low": fmt(low),
            "ci_high": fmt(high),
            "null_value": fmt(0.0),
            "sign_flip_p": fmt(p_value, 8),
            "interpretation": classify(effect, low, high, favourable_high=False),
        })

    tanzania = evidence["tanzania"]
    expected_projection = tanzania["expected_projection"]
    expected_contrasts = expected_projection["contrasts"]
    aggregate = {row["contrast_key"]: row for row in read_csv(ROOT / inputs["tanzania_aggregate_contrasts"]["path"])}
    for key in manifest["table_3"]["tanzania_contrasts"]:
        require(key in expected_contrasts and key in aggregate, f"missing Tanzania contrast {key}")
        expected = expected_contrasts[key]
        agg = aggregate[key]
        require(abs(float(agg["effect"]) - float(expected["macro_mean_species_log_loss_difference"])) < 1e-9, f"Tanzania aggregate mismatch: {key}")
        label = agg["label"]
        metrics = {
            "log_loss": (expected["macro_mean_species_log_loss_difference"], expected["log_loss_bootstrap_ci95"], expected["log_loss_sign_flip_p_value"]),
            "brier": (expected["macro_mean_species_brier_difference"], expected["brier_bootstrap_ci95"], expected["brier_sign_flip_p_value"]),
        }
        for metric in manifest["table_3"]["tanzania_metrics"]:
            effect, ci, p_value = metrics[metric]
            effect = float(effect)
            low, high = map(float, ci)
            rows.append({
                "system": "Tanzania",
                "analysis": label,
                "metric": "log loss difference" if metric == "log_loss" else "Brier difference",
                "effect_definition": "candidate minus current-flow reference; negative favours EOG",
                "n_species": str(expected["n_species"]),
                "n_matched": str(expected["n_matched"]),
                "effect": fmt(effect),
                "ci_low": fmt(low),
                "ci_high": fmt(high),
                "null_value": fmt(0.0),
                "sign_flip_p": fmt(p_value, 8),
                "interpretation": classify(effect, low, high, favourable_high=False),
            })
    return rows


def build_applicability(manifest: dict[str, Any], evidence: dict[str, Any]) -> list[dict[str, str]]:
    inputs = manifest["inputs"]
    rows: list[dict[str, str]] = []
    for src in read_csv(ROOT / inputs["aislands_applicability"]["path"]):
        rows.append({"system": "A-Islands", "analysis": src["analysis"], "partition": src["fold"], "status": src["status"], "count": src["count"]})
    strong = evidence["aislands_strong"]
    rows.extend([
        {"system": "A-Islands", "analysis": "isolation_adequacy_C_vs_R3", "partition": "ALL", "status": "evaluable_folds", "count": str(strong["folds_evaluable"])},
        {"system": "A-Islands", "analysis": "isolation_adequacy_C_vs_R3", "partition": "ALL", "status": "insufficient_training_class_count_5_5", "count": str(strong["failure_counts"]["insufficient_training_class_count_5_5"])},
    ])
    contrasts = evidence["tanzania"]["expected_projection"]["contrasts"]
    for key in manifest["table_3"]["tanzania_contrasts"]:
        src = contrasts[key]
        rows.extend([
            {"system": "Tanzania", "analysis": key, "partition": "ALL", "status": "matched", "count": str(src["n_matched"])},
            {"system": "Tanzania", "analysis": key, "partition": "ALL", "status": "invalid", "count": str(src["n_invalid_rows"])},
        ])
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    require(bool(rows), f"refusing to write empty table: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[dict[str, str]], fields: Iterable[str]) -> str:
    fields = list(fields)
    head = "| " + " | ".join(fields) + " |"
    rule = "| " + " | ".join("---" for _ in fields) + " |"
    body = ["| " + " | ".join(row[field].replace("|", "\\|") for field in fields) + " |" for row in rows]
    return "\n".join([head, rule, *body])


def build() -> dict[str, Any]:
    manifest = load_json(MANIFEST)
    evidence = validate_inputs(manifest)
    table3 = build_table3(manifest, evidence)
    applicability = build_applicability(manifest, evidence)
    table3_path = OUT / "table_3_main_sensitivity_results.csv"
    applicability_path = OUT / "table_s1_applicability_accounting.csv"
    write_csv(table3_path, table3)
    write_csv(applicability_path, applicability)

    md = [
        "# Frozen structural results tables",
        "",
        "These tables are generated from frozen original A-Islands, prospective A-Islands strong-reference, and Tanzania evidence. They are not manually transcribed and do not refit any benchmark.",
        "",
        "## Table 3. Main and predeclared sensitivity results",
        "",
        markdown_table(table3, ["system", "analysis", "metric", "n_species", "n_matched", "effect", "ci_low", "ci_high", "null_value", "sign_flip_p", "interpretation"]),
        "",
        "The original A-Islands rows use conditional concordance with null 0.5. The prospective A-Islands strong-reference and Tanzania rows use candidate-minus-reference predictive-loss differences with null 0; negative values favour adding EOG. These endpoints are not a common effect-size scale.",
        "",
        "## Table S1. Predeclared non-estimability accounting",
        "",
        markdown_table(applicability, ["system", "analysis", "partition", "status", "count"]),
        "",
        "### Claim boundaries",
        "",
        *[f"- {claim}" for claim in manifest["claim_boundaries"]],
        "",
    ]
    md_path = OUT / "structural_results_tables.md"
    md_path.write_text("\n".join(md), encoding="utf-8")
    metadata = {
        "schema_version": manifest["schema_version"],
        "table_3_rows": len(table3),
        "applicability_rows": len(applicability),
        "outputs": {
            table3_path.name: sha256(table3_path),
            applicability_path.name: sha256(applicability_path),
            md_path.name: sha256(md_path),
        },
        "tanzania_result_fingerprint": manifest["inputs"]["tanzania_expected"]["result_fingerprint"],
        "aislands_species_output_sha256": manifest["inputs"]["aislands_primary_expected"]["expected_species_output_sha256"],
        "aislands_strong_reference_result_fingerprint": manifest["inputs"]["aislands_strong_reference"]["result_fingerprint"],
    }
    metadata_path = OUT / "structural_results_tables_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metadata


def main() -> int:
    print(json.dumps(build(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
