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
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import benchmarks.ryukyu_published_binary_connectivity as sensitivity

FROZEN_DIR = Path("benchmarks/frozen/ryukyu_mangrove_response_free")
FROZEN_PREDICTOR_MANIFEST_FINGERPRINT = "8bef3ea33d24f1f124aab5e023cbfac087f74b2e5584546b9da50adaf2de7d31"
FROZEN_OPERATOR_FINGERPRINT = "61b4794914976bd1ac5687fd814a2d2878d397a2feac02314031feb68c249e35"
FROZEN_CONNECTIVITY_FINGERPRINT = "d0261069e634cb21068a45ff59c5bb891ce573ec9a6d01e75308b7b8e2215c38"
FROZEN_PREDICTORS_SHA256 = "b5485e42c8c884bf31f3d8b76fd71db04a93c377bc9836f085a4c65b6f62aa7f"
FROZEN_POPULATIONS_SHA256 = "6de60475209e49927c68d2467bdac253a0e2777c39a9f4df49dde4832ee3495e"
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
    if manifest.get("populations_csv_sha256") != FROZEN_POPULATIONS_SHA256:
        raise ValueError("archived pre-response Ryukyu manifest/population SHA disagreement")
    if manifest.get("predictors_csv_sha256") != FROZEN_PREDICTORS_SHA256:
        raise ValueError("archived pre-response Ryukyu manifest/predictor SHA disagreement")
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
