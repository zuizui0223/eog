"""Frozen one-time scorer for the SW Finland strict-source EOG v2 benchmark.

Everything in ``_verify_strict_freezes`` is response-free.  The first permitted access to
released ``outcome`` values occurs only when ``score_strict_finland`` delegates to the
already-frozen Finland scorer after all raw, feature, row, operator, contract, and syntax
identities have been reverified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import benchmarks.finland_colonization_score as base_score
from benchmarks.finland_csv_format_adapter import (
    detect_csv_format,
    fixed_dict_reader_delimiter,
)

STRICT_BUNDLE_SCHEMA = "eog_v2_finland_strict_source_response_free_bundle_v1"
STRICT_RESULT_SCHEMA = "eog_v2_finland_strict_source_empirical_result_v1"
FEATURE_FREEZE_SCHEMA = "eog_v2_finland_strict_source_feature_freeze_v1"
FORMAT_SCHEMA = "eog_v2_finland_csv_format_v1"

DEFAULT_FEATURE_FREEZE = Path(
    "benchmarks/frozen/finland_strict_source_cohort/feature_freeze.json"
)
DEFAULT_FORMAT_MANIFEST = Path(
    "benchmarks/frozen/finland_strict_source_cohort/csv_format_manifest.json"
)
STRICT_CONTRACT = Path("docs/eog_v2_finland_strict_source_cohort_contract.md")
STRICT_SPECIES = Path(
    "benchmarks/frozen/finland_strict_source_cohort/exact_complement_species.txt"
)

EXPECTED_RAW_SHA256 = "72b631033ef36210ee19b151dc4f6569760262d68f70b9ce6de6c8a11afeb957"
EXPECTED_FEATURES_SHA256 = "60d4c982e2c533a40e2ba375f371386c5b21c91c937de70d6c3c8f096a705745"
EXPECTED_FEATURE_BUNDLE_FINGERPRINT = (
    "24590e53c511330e99992e4399b711b85ce160a54a5bbc01364790f30982301b"
)
EXPECTED_STRICT_ADMISSION_FINGERPRINT = (
    "2244d242c4e74d4376c7a92a9a55f2143cffe44ad6e015ff548328813cb297a6"
)
EXPECTED_STRICT_SPECIES_SHA256 = (
    "e218f94e5facd4ed330a80b0fead0012b31fd5cb7b7b026f2ee0ff326277b2bc"
)
EXPECTED_STRICT_CONTRACT_SHA256 = (
    "143cc88223b7abe60ae53f4934b0d921a8d70a990a4ba503f41947799c5568d1"
)
EXPECTED_SOURCE_IDENTIFIABILITY_FINGERPRINT = (
    "06f38cb7a5d1321c5dde4072ee0c1329f52de05a55fed353909b342e3f4e2afd"
)
EXPECTED_FREEZE_FINGERPRINT = (
    "18fbb39306f0d2947ebe1e4ac2f56cd1b01ddc5bf93ba2988c3e808d48f8d5af"
)
EXPECTED_FREEZE_RUN = 31689131928
EXPECTED_FREEZE_ARTIFACT = 9176686695
EXPECTED_FREEZE_ARTIFACT_DIGEST = (
    "sha256:9a2a0b78ab5000698f97f6e3371c6548c3c95a04c93744a9b571f6ce7f62c758"
)


def _sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _verify_freeze_record(path: str | Path) -> dict[str, object]:
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    if record.get("schema") != FEATURE_FREEZE_SCHEMA:
        raise ValueError("unsupported Finland strict feature-freeze record")
    observed = str(record.get("fingerprint", ""))
    payload = dict(record)
    payload.pop("fingerprint", None)
    if _canonical_sha256(payload) != observed or observed != EXPECTED_FREEZE_FINGERPRINT:
        raise ValueError("Finland strict feature-freeze record fingerprint mismatch")
    required = {
        "workflow_run": EXPECTED_FREEZE_RUN,
        "artifact_id": EXPECTED_FREEZE_ARTIFACT,
        "artifact_digest": EXPECTED_FREEZE_ARTIFACT_DIGEST,
        "raw_sha256": EXPECTED_RAW_SHA256,
        "features_sha256": EXPECTED_FEATURES_SHA256,
        "feature_bundle_fingerprint": EXPECTED_FEATURE_BUNDLE_FINGERPRINT,
        "strict_admission_fingerprint": EXPECTED_STRICT_ADMISSION_FINGERPRINT,
        "strict_species_list_sha256": EXPECTED_STRICT_SPECIES_SHA256,
        "strict_cohort_contract_sha256": EXPECTED_STRICT_CONTRACT_SHA256,
        "source_identifiability_fingerprint": EXPECTED_SOURCE_IDENTIFIABILITY_FINGERPRINT,
        "n_sourceful_species": 180,
        "n_analysis_species_response_free": 180,
        "n_analysis_rows_response_free": 74700,
        "outcome_values_accessed": False,
    }
    for key, expected in required.items():
        if record.get(key) != expected:
            raise ValueError(f"Finland strict feature-freeze drift: {key}")
    return record


def _verify_format_manifest(
    raw_path: Path,
    format_manifest_path: str | Path,
) -> tuple[dict[str, object], dict[str, object]]:
    frozen = json.loads(Path(format_manifest_path).read_text(encoding="utf-8"))
    if frozen.get("schema") != FORMAT_SCHEMA:
        raise ValueError("unsupported Finland frozen CSV format schema")
    if frozen.get("outcome_values_accessed") is not False:
        raise ValueError("Finland CSV format freeze is not response-free")
    if frozen.get("raw_sha256") != EXPECTED_RAW_SHA256:
        raise ValueError("Finland CSV format freeze raw identity drifted")
    observed = detect_csv_format(raw_path)
    for key in (
        "delimiter",
        "delimiter_codepoint",
        "n_fields",
        "field_names",
        "header_sha256",
        "binary_recoding",
        "outcome_column_exists",
    ):
        if observed.get(key) != frozen.get(key):
            raise ValueError(f"Finland CSV syntax drift after response-free freeze: {key}")
    return frozen, observed


def _verify_strict_freezes(
    raw_path: str | Path,
    bundle_path: str | Path,
    manifest_path: str | Path,
    *,
    feature_freeze_path: str | Path = DEFAULT_FEATURE_FREEZE,
    format_manifest_path: str | Path = DEFAULT_FORMAT_MANIFEST,
) -> tuple[dict[str, object], dict[str, object]]:
    raw = Path(raw_path)
    bundle = Path(bundle_path)
    manifest_file = Path(manifest_path)

    freeze = _verify_freeze_record(feature_freeze_path)
    if _sha256_file(raw) != EXPECTED_RAW_SHA256:
        raise ValueError("Finland strict raw SHA-256 mismatch")
    if _sha256_file(bundle) != EXPECTED_FEATURES_SHA256:
        raise ValueError("Finland strict response-free feature bytes drifted")
    if _sha256_file(STRICT_SPECIES) != EXPECTED_STRICT_SPECIES_SHA256:
        raise ValueError("Finland strict species list drifted")
    if _sha256_file(STRICT_CONTRACT) != EXPECTED_STRICT_CONTRACT_SHA256:
        raise ValueError("Finland strict cohort contract changed after feature freeze")

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if manifest.get("schema") != STRICT_BUNDLE_SCHEMA:
        raise ValueError("unsupported Finland strict feature-bundle schema")
    exact = {
        "raw_sha256": EXPECTED_RAW_SHA256,
        "feature_bundle_fingerprint": EXPECTED_FEATURE_BUNDLE_FINGERPRINT,
        "strict_admission_fingerprint": EXPECTED_STRICT_ADMISSION_FINGERPRINT,
        "strict_species_list_sha256": EXPECTED_STRICT_SPECIES_SHA256,
        "strict_cohort_contract_sha256": EXPECTED_STRICT_CONTRACT_SHA256,
        "source_identifiability_fingerprint": EXPECTED_SOURCE_IDENTIFIABILITY_FINGERPRINT,
        "n_islands": 471,
        "n_sourceful_species": 180,
        "n_species_analysis_response_free": 180,
        "n_rows_analysis_response_free": 74700,
        "outcome_values_accessed": False,
    }
    for key, expected in exact.items():
        if manifest.get(key) != expected:
            raise ValueError(f"Finland strict feature manifest drift: {key}")
    if freeze["feature_bundle_fingerprint"] != manifest["feature_bundle_fingerprint"]:
        raise ValueError("Finland feature-freeze/manifest fingerprint disagreement")

    frozen_format, _ = _verify_format_manifest(raw, format_manifest_path)

    # Reuse the original scientific bundle verifier without weakening any of its checks.
    previous_schema = base_score.EXPECTED_SCHEMA
    base_score.EXPECTED_SCHEMA = STRICT_BUNDLE_SCHEMA
    try:
        verified_manifest, _ = base_score._verify_manifest_and_bundle(
            raw, bundle, manifest_file
        )
    finally:
        base_score.EXPECTED_SCHEMA = previous_schema
    if verified_manifest.get("feature_bundle_fingerprint") != EXPECTED_FEATURE_BUNDLE_FINGERPRINT:
        raise ValueError("Finland strict base verifier returned unexpected feature fingerprint")

    audit = {
        "schema": "eog_v2_finland_strict_source_scoring_preflight_v1",
        "status": "response-free-scoring-preflight-passed",
        "raw_sha256": EXPECTED_RAW_SHA256,
        "features_sha256": EXPECTED_FEATURES_SHA256,
        "feature_bundle_fingerprint": EXPECTED_FEATURE_BUNDLE_FINGERPRINT,
        "strict_admission_fingerprint": EXPECTED_STRICT_ADMISSION_FINGERPRINT,
        "strict_species_list_sha256": EXPECTED_STRICT_SPECIES_SHA256,
        "strict_cohort_contract_sha256": EXPECTED_STRICT_CONTRACT_SHA256,
        "format_header_sha256": frozen_format["header_sha256"],
        "format_delimiter": frozen_format["delimiter"],
        "freeze_workflow_run": EXPECTED_FREEZE_RUN,
        "freeze_artifact_id": EXPECTED_FREEZE_ARTIFACT,
        "freeze_artifact_digest": EXPECTED_FREEZE_ARTIFACT_DIGEST,
        "outcome_values_accessed": False,
    }
    audit["fingerprint"] = _canonical_sha256(audit)
    return frozen_format, audit


def score_strict_finland(
    raw_path: str | Path,
    bundle_path: str | Path,
    manifest_path: str | Path,
    *,
    feature_freeze_path: str | Path = DEFAULT_FEATURE_FREEZE,
    format_manifest_path: str | Path = DEFAULT_FORMAT_MANIFEST,
) -> dict[str, object]:
    frozen_format, preflight = _verify_strict_freezes(
        raw_path,
        bundle_path,
        manifest_path,
        feature_freeze_path=feature_freeze_path,
        format_manifest_path=format_manifest_path,
    )

    # FIRST RESPONSE ACCESS: base_score._read_outcomes is reached only inside this call.
    previous_schema = base_score.EXPECTED_SCHEMA
    base_score.EXPECTED_SCHEMA = STRICT_BUNDLE_SCHEMA
    try:
        with fixed_dict_reader_delimiter(str(frozen_format["delimiter"])):
            result = base_score.score_finland(raw_path, bundle_path, manifest_path)
    finally:
        base_score.EXPECTED_SCHEMA = previous_schema

    result = dict(result)
    result["schema"] = STRICT_RESULT_SCHEMA
    result["strict_source_feature_freeze"] = {
        "workflow_run": EXPECTED_FREEZE_RUN,
        "artifact_id": EXPECTED_FREEZE_ARTIFACT,
        "artifact_digest": EXPECTED_FREEZE_ARTIFACT_DIGEST,
        "features_sha256": EXPECTED_FEATURES_SHA256,
        "feature_bundle_fingerprint": EXPECTED_FEATURE_BUNDLE_FINGERPRINT,
        "strict_species_list_sha256": EXPECTED_STRICT_SPECIES_SHA256,
        "strict_cohort_contract_sha256": EXPECTED_STRICT_CONTRACT_SHA256,
    }
    result["response_free_preflight_fingerprint"] = preflight["fingerprint"]
    result.pop("result_fingerprint", None)
    result["result_fingerprint"] = _canonical_sha256(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--feature-freeze", type=Path, default=DEFAULT_FEATURE_FREEZE)
    parser.add_argument("--format-manifest", type=Path, default=DEFAULT_FORMAT_MANIFEST)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()

    if args.preflight_only:
        _, payload = _verify_strict_freezes(
            args.input,
            args.bundle,
            args.manifest,
            feature_freeze_path=args.feature_freeze,
            format_manifest_path=args.format_manifest,
        )
    else:
        payload = score_strict_finland(
            args.input,
            args.bundle,
            args.manifest,
            feature_freeze_path=args.feature_freeze,
            format_manifest_path=args.format_manifest,
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
