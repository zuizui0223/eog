#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return value


def _get_path(value: dict[str, Any], dotted: str) -> Any:
    current: Any = value
    for key in dotted.split("."):
        if not isinstance(current, dict) or key not in current:
            raise KeyError(f"missing {dotted!r} at component {key!r}")
        current = current[key]
    return current


def _normalize_text(value: str) -> str:
    # Claim strings are semantic guards, not exact typography checks.
    return re.sub(r"\s+", "", value).lower()


def validate_claims(claim_path: Path) -> dict[str, Any]:
    claims = _read_json(claim_path)
    manuscript_path = ROOT / claims["manuscript"]
    manuscript = manuscript_path.read_text(encoding="utf-8")
    normalized_manuscript = _normalize_text(manuscript)

    failures: list[dict[str, Any]] = []
    checked_assertions = 0
    checked_strings = 0

    for source_claim in claims["source_claims"]:
        source_path = ROOT / source_claim["source"]
        source = _read_json(source_path)

        expected_fingerprint = source_claim["fingerprint"]
        observed_fingerprint = source.get("result_fingerprint")
        if observed_fingerprint != expected_fingerprint:
            failures.append(
                {
                    "claim_id": source_claim["id"],
                    "kind": "fingerprint_mismatch",
                    "expected": expected_fingerprint,
                    "observed": observed_fingerprint,
                }
            )

        for dotted, expected in source_claim["assertions"].items():
            checked_assertions += 1
            try:
                observed = _get_path(source, dotted)
            except KeyError as exc:
                failures.append(
                    {
                        "claim_id": source_claim["id"],
                        "kind": "missing_source_value",
                        "path": dotted,
                        "error": str(exc),
                    }
                )
                continue
            if observed != expected:
                failures.append(
                    {
                        "claim_id": source_claim["id"],
                        "kind": "source_value_mismatch",
                        "path": dotted,
                        "expected": expected,
                        "observed": observed,
                    }
                )

        for required in source_claim.get("required_manuscript_strings", []):
            checked_strings += 1
            if _normalize_text(required) not in normalized_manuscript:
                failures.append(
                    {
                        "claim_id": source_claim["id"],
                        "kind": "missing_manuscript_claim",
                        "required": required,
                    }
                )

    lower_manuscript = manuscript.lower()
    for phrase in claims.get("forbidden_unqualified_phrases", []):
        if phrase.lower() in lower_manuscript:
            failures.append(
                {
                    "kind": "forbidden_unqualified_phrase",
                    "phrase": phrase,
                }
            )

    payload = {
        "schema": "eog.bam_inverse_identifiability.manuscript_claim_check.v2",
        "claim_ledger": str(claim_path.relative_to(ROOT)),
        "manuscript": claims["manuscript"],
        "checked_source_claims": len(claims["source_claims"]),
        "checked_assertions": checked_assertions,
        "checked_manuscript_strings": checked_strings,
        "failure_count": len(failures),
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }
    fingerprint_payload = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    payload["fingerprint"] = hashlib.sha256(fingerprint_payload).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--claims",
        type=Path,
        default=ROOT / "manuscript/bam_identifiability/CLAIMS_MACHINE_V2.json",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    claims_path = args.claims.resolve()
    result = validate_claims(claims_path)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
