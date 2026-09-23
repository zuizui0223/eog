"""Pre-content source classification firewall for prospective EOG-WF discovery.

Candidate discovery often exposes many adjacent files. A filename, path, or schema
description can already tell us that a file is likely biological response-bearing.
Those files must not be fetched merely to discover whether they are safe.

This module evaluates metadata-only descriptors before content retrieval. It is
conservative by design: unknown files are not automatically safe.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Literal, Sequence


DiscoveryClass = Literal[
    "safe_candidate",
    "response_bearing",
    "ambiguous_do_not_open",
]


_RESPONSE_TOKENS = {
    "observation",
    "observations",
    "occurrence",
    "occurrences",
    "capture",
    "captures",
    "detection",
    "detections",
    "encounter",
    "encounters",
    "species",
    "taxon",
    "taxa",
    "presence",
    "absence",
    "response",
    "outcome",
    "label",
    "labels",
}

_SAFE_TOKENS = {
    "deployment",
    "deployments",
    "site",
    "sites",
    "station",
    "stations",
    "location",
    "locations",
    "registry",
    "effort",
    "sampling",
    "sample",
    "samples",
    "covariate",
    "covariates",
    "environment",
    "environmental",
    "geometry",
    "coordinates",
}

_RESPONSE_SCHEMA_FIELDS = {
    "scientificname",
    "species",
    "taxon",
    "taxonkey",
    "occurrencestatus",
    "individualcount",
    "detection",
    "detected",
    "presence",
    "absence",
    "label",
    "outcome",
}

_SAFE_SCHEMA_FIELDS = {
    "site",
    "siteid",
    "station",
    "stationid",
    "locationid",
    "deploymentid",
    "deploymentstart",
    "deploymentend",
    "latitude",
    "longitude",
    "utmnorth",
    "utmeast",
    "utmzone",
    "samplingprotocol",
    "samplesizevalue",
    "samplesizeunit",
}


def _sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.split(r"[^a-z0-9]+", value.casefold())
        if token
    }


def _field_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


@dataclass(frozen=True)
class SourceDescriptor:
    source_id: str
    path_or_name: str
    declared_schema_fields: tuple[str, ...] = ()
    metadata_note: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("source_id must be non-empty str")
        if not isinstance(self.path_or_name, str) or not self.path_or_name.strip():
            raise ValueError("path_or_name must be non-empty str")
        if any(not isinstance(value, str) for value in self.declared_schema_fields):
            raise TypeError("declared_schema_fields must contain str values")
        if not isinstance(self.metadata_note, str):
            raise TypeError("metadata_note must be str")


@dataclass(frozen=True)
class DiscoveryClassification:
    source_id: str
    classification: DiscoveryClass
    content_open_allowed: bool
    response_indicators: tuple[str, ...]
    safe_indicators: tuple[str, ...]
    reason: str
    fingerprint: str


def classify_source_descriptor(
    descriptor: SourceDescriptor,
) -> DiscoveryClassification:
    """Classify one source from metadata only, before any content retrieval."""

    name_tokens = _tokens(descriptor.path_or_name)
    note_tokens = _tokens(descriptor.metadata_note)
    all_text_tokens = name_tokens | note_tokens
    fields = {_field_token(value) for value in descriptor.declared_schema_fields}

    response_indicators = sorted(
        {f"text:{token}" for token in all_text_tokens & _RESPONSE_TOKENS}
        | {f"field:{field}" for field in fields & _RESPONSE_SCHEMA_FIELDS}
    )
    safe_indicators = sorted(
        {f"text:{token}" for token in all_text_tokens & _SAFE_TOKENS}
        | {f"field:{field}" for field in fields & _SAFE_SCHEMA_FIELDS}
    )

    if response_indicators:
        classification: DiscoveryClass = "response_bearing"
        allowed = False
        reason = (
            "metadata contains biological response indicators; content retrieval is "
            "forbidden before response authorization"
        )
    elif safe_indicators:
        classification = "safe_candidate"
        allowed = True
        reason = (
            "metadata contains only recognized response-independent registry/effort "
            "indicators and no response indicator"
        )
    else:
        classification = "ambiguous_do_not_open"
        allowed = False
        reason = (
            "metadata does not establish that the source is response-independent; "
            "do not retrieve content during prospective discovery"
        )

    payload = {
        "source_id": descriptor.source_id,
        "path_or_name": descriptor.path_or_name,
        "declared_schema_fields": list(descriptor.declared_schema_fields),
        "metadata_note": descriptor.metadata_note,
        "classification": classification,
        "content_open_allowed": allowed,
        "response_indicators": response_indicators,
        "safe_indicators": safe_indicators,
        "reason": reason,
    }
    return DiscoveryClassification(
        source_id=descriptor.source_id,
        classification=classification,
        content_open_allowed=allowed,
        response_indicators=tuple(response_indicators),
        safe_indicators=tuple(safe_indicators),
        reason=reason,
        fingerprint=_sha256(payload),
    )


def classify_discovery_batch(
    descriptors: Sequence[SourceDescriptor],
) -> tuple[DiscoveryClassification, ...]:
    values = tuple(descriptors)
    ids = [value.source_id for value in values]
    if len(ids) != len(set(ids)):
        raise ValueError("source descriptor IDs must be unique")
    return tuple(
        classify_source_descriptor(value)
        for value in sorted(values, key=lambda item: item.source_id)
    )
