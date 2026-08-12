"""Run the published Ryukyu binary-FST sensitivity from the archived pre-response artifact.

The response-free predictor files are not regenerated. Their byte identities and the
original workflow-artifact provenance are verified before the published Figure 2 response
is attached.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import benchmarks.ryukyu_published_binary_connectivity as sensitivity

FROZEN_DIR = Path("benchmarks/frozen/ryukyu_mangrove_response_free")
FROZEN_PREDICTOR_MANIFEST_FINGERPRINT = "8bef3ea334eb99610f04ac4eb38e411731b59649ac926f2b60278a732aad1449"
FROZEN_OPERATOR_FINGERPRINT = "61ba283a6d33cfd85fd3b187de88c47e154acd8da0c6c31082aca1c647219830"
FROZEN_CONNECTIVITY_FINGERPRINT = "d026ca7a6f4a948ee465ab14b7419cdddea97943886d03ebc18b2429a63bdcfe"
FROZEN_PREDICTORS_SHA256 = "b5484727b4e690ef880384408a7283964ede593a788b093c74777886bec9851f"
FROZEN_POPULATIONS_SHA256 = "0edd135771e8339074b456a311efd02202d0309d81b539206160bad212236fb4"
SOURCE_RUN = 31610691970
SOURCE_ARTIFACT = 9147048185
SOURCE_ARTIFACT_DIGEST = "sha256:23725655494ff7ba09fd764186a675e4f13190d92f0605e601d9b3cc4737a681"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate(figure: str | Path) -> dict[str, object]:
    predictors = FROZEN_DIR / "predictors.csv"
    populations = FROZEN_DIR / "populations.csv"
    manifest_path = FROZEN_DIR / "predictor_manifest.json"
    if _sha256(predictors) != FROZEN_PREDICTORS_SHA256:
        raise ValueError("archived pre-response Ryukyu predictor CSV drifted")
    if _sha256(populations) != FROZEN_POPULATIONS_SHA256:
        raise ValueError("archived pre-response Ryukyu population CSV drifted")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("predictor_manifest_fingerprint") != FROZEN_PREDICTOR_MANIFEST_FINGERPRINT:
        raise ValueError("archived pre-response Ryukyu predictor manifest drifted")
    if manifest.get("operator_fingerprint") != FROZEN_OPERATOR_FINGERPRINT:
        raise ValueError("archived pre-response Ryukyu operator fingerprint drifted")
    if manifest.get("connectivity_fingerprint") != FROZEN_CONNECTIVITY_FINGERPRINT:
        raise ValueError("archived pre-response Ryukyu connectivity fingerprint drifted")
    if manifest.get("genetic_response_attached") is not False:
        raise ValueError("archived Ryukyu predictor manifest is no longer response-free")

    original_expected = sensitivity.EXPECTED_PREDICTOR_MANIFEST_FINGERPRINT
    try:
        sensitivity.EXPECTED_PREDICTOR_MANIFEST_FINGERPRINT = FROZEN_PREDICTOR_MANIFEST_FINGERPRINT
        result = sensitivity.evaluate(figure, predictors, manifest_path)
    finally:
        sensitivity.EXPECTED_PREDICTOR_MANIFEST_FINGERPRINT = original_expected
    result["response_free_predictor_source"] = {
        "workflow_run": SOURCE_RUN,
        "artifact_id": SOURCE_ARTIFACT,
        "artifact_digest": SOURCE_ARTIFACT_DIGEST,
        "predictors_sha256": FROZEN_PREDICTORS_SHA256,
        "populations_sha256": FROZEN_POPULATIONS_SHA256,
        "predictor_manifest_fingerprint": FROZEN_PREDICTOR_MANIFEST_FINGERPRINT,
        "operator_fingerprint": FROZEN_OPERATOR_FINGERPRINT,
        "connectivity_fingerprint": FROZEN_CONNECTIVITY_FINGERPRINT,
        "regenerated_after_response_visible": False,
    }
    # Recompute the final fingerprint after attaching the frozen predictor provenance.
    payload = dict(result)
    payload.pop("fingerprint", None)
    result["fingerprint"] = sensitivity._canonical_sha256(payload)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--figure", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.figure)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
