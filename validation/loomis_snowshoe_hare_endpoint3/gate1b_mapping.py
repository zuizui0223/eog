from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence


REQUIRED_DEPLOYMENT_ROLES = (
    "site_id",
    "camera_id",
    "latitude",
    "longitude",
    "deployment_start",
    "deployment_end",
)
EXPECTED_DEPLOYMENT_KEYS = (
    "deployment_2022.csv",
    "deployment_2023.csv",
    "deployment_2024.csv",
)
CAMERA_INFO_KEY = "camera_info_new.csv"


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class Stage1BMappingResult:
    valid: bool
    reason: str
    normalized_mapping: dict[str, str]
    fingerprint: str


def validate_stage1b_mapping(
    *,
    headers: Mapping[str, Sequence[str]],
    deployment_mapping: Mapping[str, str],
    camera_info_join_field: str | None = None,
) -> Stage1BMappingResult:
    """Validate an exact mapping using Stage1A header names only.

    This function never consumes deployment rows.  It requires one identical physical
    field mapping across all three deployment-year headers.  Campaign/year is supplied
    by the already-frozen file identity, not inferred from row values.
    """

    missing_files = [key for key in (*EXPECTED_DEPLOYMENT_KEYS, CAMERA_INFO_KEY) if key not in headers]
    if missing_files:
        raise ValueError(f"missing Stage1A header evidence: {missing_files}")

    header_sets: dict[str, tuple[str, ...]] = {}
    for key, columns in headers.items():
        if not isinstance(key, str) or not key:
            raise TypeError("header keys must be non-empty strings")
        vals = tuple(columns)
        if not vals or any(not isinstance(v, str) or not v for v in vals):
            raise ValueError(f"invalid header columns for {key}")
        if len(vals) != len(set(vals)):
            raise ValueError(f"duplicate header columns for {key}")
        header_sets[key] = vals

    if tuple(deployment_mapping.keys()) != REQUIRED_DEPLOYMENT_ROLES:
        raise ValueError(
            "deployment_mapping keys must exactly follow REQUIRED_DEPLOYMENT_ROLES order"
        )
    normalized: dict[str, str] = {}
    for role in REQUIRED_DEPLOYMENT_ROLES:
        field = deployment_mapping[role]
        if not isinstance(field, str) or not field:
            raise ValueError(f"mapping for {role} must be non-empty string")
        normalized[role] = field

    mapped_fields = tuple(normalized.values())
    if len(set(mapped_fields)) != len(mapped_fields):
        raise ValueError("deployment roles must map to distinct physical columns")

    for key in EXPECTED_DEPLOYMENT_KEYS:
        columns = set(header_sets[key])
        missing = [field for field in mapped_fields if field not in columns]
        if missing:
            payload = {
                "valid": False,
                "reason": f"{key} lacks mapped fields: {missing}",
                "normalized_mapping": normalized,
            }
            return Stage1BMappingResult(False, payload["reason"], normalized, _canonical_sha256(payload))

    if camera_info_join_field is not None:
        if not isinstance(camera_info_join_field, str) or not camera_info_join_field:
            raise ValueError("camera_info_join_field must be non-empty string or None")
        if camera_info_join_field not in set(header_sets[CAMERA_INFO_KEY]):
            payload = {
                "valid": False,
                "reason": "camera_info_join_field is absent from camera_info_new.csv header",
                "normalized_mapping": normalized,
                "camera_info_join_field": camera_info_join_field,
            }
            return Stage1BMappingResult(False, payload["reason"], normalized, _canonical_sha256(payload))
        if normalized["camera_id"] != camera_info_join_field:
            payload = {
                "valid": False,
                "reason": "camera_info join must use the same physical camera-id field",
                "normalized_mapping": normalized,
                "camera_info_join_field": camera_info_join_field,
            }
            return Stage1BMappingResult(False, payload["reason"], normalized, _canonical_sha256(payload))

    payload = {
        "valid": True,
        "reason": "exact header-only mapping is present in all three deployment headers",
        "normalized_mapping": normalized,
        "campaign_year_source": "frozen deployment filename identity",
        "camera_info_join_field": camera_info_join_field,
    }
    return Stage1BMappingResult(True, payload["reason"], normalized, _canonical_sha256(payload))
