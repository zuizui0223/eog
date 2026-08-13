"""Preflight the frozen Fiji focal genetic member without opening genetic contents.

The only archive operation performed here is ZIP central-directory inspection.  If the
frozen focal VCF member is absent, Fiji becomes non-estimable under the already frozen
focal-group contract.  This script never substitutes another EGPA group.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile


FROZEN_MANIFEST = Path("benchmarks/frozen/fiji_pheidole_response_free/manifest.json")
EXPECTED_PREDICTOR_MANIFEST_FINGERPRINT = "e1db628f61954a9b0a42692f9c3fb670192c882711956a08d144a97a23836b7c"
EXPECTED_ARCHIVE_SHA256 = "9a23543ad59d5f4de7e6f26cc91b75dc60f93c259744e640b8f6576fde89abc7"
FOCAL_EGPA = "EGPA0079"
EXPECTED_MEMBER = "dryad/VCFs/EGPA0079.filtered.vcf"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def preflight(archive: Path) -> dict[str, object]:
    if not FROZEN_MANIFEST.exists():
        raise RuntimeError("frozen Fiji response-free predictor manifest is missing")
    manifest = json.loads(FROZEN_MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("predictor_manifest_fingerprint") != EXPECTED_PREDICTOR_MANIFEST_FINGERPRINT:
        raise ValueError("frozen Fiji predictor manifest fingerprint drifted")
    if manifest.get("focal_egpa") != FOCAL_EGPA:
        raise ValueError("frozen Fiji focal EGPA drifted")
    if manifest.get("genetic_member_contents_accessed") is not False:
        raise ValueError("frozen Fiji predictor manifest no longer certifies response-free construction")

    archive_sha = _sha256(archive)
    if archive_sha != EXPECTED_ARCHIVE_SHA256:
        raise ValueError("Fiji archive SHA differs from the Stage-1/2 verified object")

    # ZIP-directory inspection only. Do not call handle.read/open on any archive member.
    with zipfile.ZipFile(archive, "r") as handle:
        member_names = sorted(info.filename for info in handle.infolist() if not info.is_dir())
    member_present = EXPECTED_MEMBER in member_names
    egpa_named_members = [name for name in member_names if FOCAL_EGPA.lower() in name.lower()]

    status = (
        "authorized_focal_genetic_member_present"
        if member_present
        else "non_estimable_focal_genetic_member_absent"
    )
    result: dict[str, object] = {
        "status": status,
        "focal_egpa": FOCAL_EGPA,
        "expected_genetic_member": EXPECTED_MEMBER,
        "expected_genetic_member_present": member_present,
        "focal_egpa_named_archive_members": egpa_named_members,
        "n_archive_members": len(member_names),
        "archive_sha256": archive_sha,
        "predictor_manifest_fingerprint": EXPECTED_PREDICTOR_MANIFEST_FINGERPRINT,
        "genetic_member_contents_accessed": False,
        "genetic_response_computed": False,
        "alternate_egpa_substitution_permitted": False,
        "claim_boundary": (
            "Only ZIP member names were inspected. No VCF/FST/WC/genotype member content was opened. "
            "If the frozen EGPA0079 VCF is absent, the Fiji candidate is non-estimable and no alternate "
            "EGPA group may replace it under this frozen validation attempt."
        ),
    }
    result["fingerprint"] = _canonical_sha256(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = preflight(args.archive)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
