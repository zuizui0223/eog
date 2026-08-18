#!/usr/bin/env python3
"""Run the frozen Hydrilla Gate 0 with Dryad linked-version metadata support.

Dryad's versions response can identify a version through ``version``/``versionNumber``
and a linked ``/versions/<id>`` URL rather than a top-level numeric ``id``.  The first
bundle run stopped before any source-data row because the generic parser required a
numeric ID on the record itself.  This wrapper changes only that metadata adapter and
then invokes the unchanged Gate-0 implementation.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import sys
from typing import Any


MODULE_PATH = Path(__file__).with_name("run_hydrilla_gate0_bundle.py")
SPEC = importlib.util.spec_from_file_location("hydrilla_gate0_bundle", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load Hydrilla Gate-0 implementation")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def choose_version(payload: dict[str, Any]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for values in MODULE.nested_lists(payload):
        if not values or not all(isinstance(item, dict) for item in values):
            continue
        for item in values:
            if any(key in item for key in ("versionNumber", "version", "id", "versionId")):
                candidates.append(item)
    if not candidates:
        raise ValueError("Dryad versions API returned no recognizable version records")

    def key(item: dict[str, Any]) -> tuple[int, int]:
        raw_version = item.get("versionNumber", item.get("version", 0))
        try:
            version_number = int(raw_version)
        except Exception:
            version_number = 0
        status = str(item.get("status", "")).lower()
        published = 1 if status in {"published", "submitted"} else 0
        return published, version_number

    return max(candidates, key=key)


def resolve_version_id(version: dict[str, Any]) -> int:
    for key in ("id", "versionId"):
        if version.get(key) is not None:
            return int(version[key])
    links = version.get("_links", {})
    if isinstance(links, dict):
        for entry in links.values():
            href = entry.get("href") if isinstance(entry, dict) else entry
            if not href:
                continue
            match = re.search(r"/versions/(\d+)(?:/|$)", str(href))
            if match:
                return int(match.group(1))
    raise ValueError("unable to resolve numeric Dryad version ID from linked metadata")


MODULE.choose_version = choose_version
MODULE.resolve_version_id = resolve_version_id
MODULE.main()
