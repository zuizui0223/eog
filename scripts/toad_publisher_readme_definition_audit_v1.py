#!/usr/bin/env python3
"""Source-locked original Dryad README audit after a toad geo-QC scientific STOP.

Only the public 2,102-byte RTF README is parsed. The 18,702-byte CSV is
SHA256 verified but NEVER decoded, iterated into rows, analyzed or uploaded.
Source-only output cannot authorize the stopped biological/geo MRR test.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import urllib.error
import zipfile
from typing import Any

from scripts.eog_independent_movement_source_gate_v2 import _version_zip

PROTOCOL = Path("validation/toad_release_distance_publisher_readme_v1/protocol_v1.json")
V2_SOURCE_GATE = Path("validation/independent_movement_source_gate_v2/protocol_v2.json")
V1_SOURCE_GATE = Path("validation/independent_movement_source_gate_v1/protocol_v1.json")

TOKEN = re.compile(
    r"\\([a-zA-Z]+)(-?\d+)? ?|\\'([0-9a-fA-F]{2})|\\([^a-zA-Z])|([{}])|([^\\{}]+)",
    re.DOTALL,
)
NON_CONTENT_DESTINATIONS = frozenset({
    "fonttbl", "colortbl", "stylesheet", "info", "pict", "object",
    "header", "footer", "generator", "listtable", "listoverridetable"
})


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def rtf_plaintext(raw: bytes) -> str:
    """Minimal deterministic RTF 1.x parser; fails on binary or bad bracket nesting.

    State is an ignorable-group flag and unicode fallback length; document
    styling is not retained. This is not an HTML/browser renderer.
    """
    if not raw.startswith(b"{\\rtf"):
        raise ValueError("STOP_SOURCE_README_NOT_RTF")
    if b"\x00" in raw:
        raise ValueError("STOP_RTF_NUL_CONTENT")
    text = raw.decode("cp1252")
    out: list[str] = []
    stack: list[tuple[bool,int]] = []
    ignorable = False
    pending_star = False
    fallback_chars = 1
    ignore_next_plain = 0
    for m in TOKEN.finditer(text):
        word, arg, hexesc, escaped, brace, literal = m.groups()
        if brace == "{":
            stack.append((ignorable, fallback_chars))
            pending_star = False
        elif brace == "}":
            if not stack:
                raise ValueError("STOP_RTF_UNBALANCED")
            ignorable, fallback_chars = stack.pop()
            pending_star = False
        elif word is not None:
            if pending_star or word in NON_CONTENT_DESTINATIONS:
                ignorable = True
                pending_star = False
            if word == "uc" and arg is not None:
                fallback_chars = int(arg)
            elif not ignorable and word in ("par", "line"):
                out.append("\n")
            elif not ignorable and word == "tab":
                out.append("\t")
            elif not ignorable and word == "u" and arg is not None:
                codepoint = int(arg)
                if codepoint < 0:
                    codepoint += 65536
                out.append(chr(codepoint))
                ignore_next_plain = fallback_chars
        elif hexesc is not None:
            if not ignorable:
                if ignore_next_plain:
                    ignore_next_plain -= 1
                else:
                    out.append(bytes([int(hexesc, 16)]).decode("cp1252"))
        elif escaped is not None:
            if escaped == "*":
                pending_star = True
            elif not ignorable and escaped in ("{", "}", "\\"):
                if ignore_next_plain:
                    ignore_next_plain -= 1
                else:
                    out.append(escaped)
            elif not ignorable and escaped == "~":
                out.append(" ")
            elif not ignorable and escaped == "-":
                out.append("-")
        elif literal is not None and not ignorable:
            if ignore_next_plain:
                skip = min(len(literal), ignore_next_plain)
                literal = literal[skip:]
                ignore_next_plain -= skip
            if literal:
                out.append(literal)
    if stack:
        raise ValueError("STOP_RTF_UNBALANCED")
    plaintext = "".join(out).replace("\r", "\n")
    lines = [re.sub(r"\s+", " ", line).strip() for line in plaintext.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def verify_readme_bytes(archive_bytes: bytes, expected_files: list[dict[str, Any]]) -> bytes:
    """Verify byte identity of BOTH publication members, decode ONLY README."""
    expected = {f["name"]: f for f in expected_files}
    if set(expected) != {"README_file.rtf", "Jreidini_and_Green_homing_toads_2021.csv"}:
        raise ValueError("STOP_README_SOURCE_FILESET_CHANGED")
    if not zipfile.is_zipfile(io.BytesIO(archive_bytes)):
        raise ValueError("STOP_SOURCE_ZIP_UNREADABLE")
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as z:
        infos = [entry for entry in z.infolist() if not entry.is_dir()]
        if len(infos) != len(expected):
            raise ValueError("STOP_SOURCE_ZIP_MEMBER_COUNT_CHANGED")
        mapped: dict[str, zipfile.ZipInfo] = {}
        for entry in infos:
            p = entry.filename.replace("\\", "/")
            if p.startswith("/") or ".." in p.split("/"):
                raise ValueError("STOP_ZIP_UNSAFE_MEMBER")
            name = PurePosixPath(p).name
            if name in mapped or name not in expected:
                raise ValueError("STOP_ZIP_MEMBER_IDENTITY")
            mapped[name] = entry
        if set(mapped) != set(expected):
            raise ValueError("STOP_PUBLISHER_MEMBER_SET_DIFFERENT")
        original_readme: bytes | None = None
        for name, entry in mapped.items():
            # Exactly one small public CSV is read as uninterpreted bytes for hashing;
            # no CSV parser/decoder/record access is performed.
            raw = z.read(entry)
            ident = expected[name]
            if len(raw) != ident["bytes"] or sha(raw) != ident["sha256"]:
                raise ValueError("STOP_ORIGINAL_PUBLISHER_MEMBER_HASH_MISMATCH")
            if name == "README_file.rtf":
                original_readme = raw
        if original_readme is None:
            raise ValueError("STOP_README_ABSENT")
        return original_readme


def _documentation_receipt(readme: bytes, spec: dict[str, Any]) -> dict[str, Any]:
    text = rtf_plaintext(readme)
    if not text or len(text) > 3500:
        raise ValueError("STOP_UNEXPECTED_README_PLAINTEXT_SIZE")
    # README is source documentation, not animal movement values.
    # A source text presence check does not assert that any biological column
    # was actually defined; semantic conclusion requires manual audit.
    lines = text.splitlines()
    relevant_terms = ["release", "capture", "final", "distance", "east", "north", "control", "coordinate", "utm"]
    line_terms = [
        {"line_no": n+1, "keywords": sorted(term for term in relevant_terms if term in line.lower())}
        for n, line in enumerate(lines) if any(term in line.lower() for term in relevant_terms)
    ]
    return {
        "schema":"eog.toad_publisher_readme_definitions_v1.source_only_receipt",
        "status":"AUTHENTICATED_PUBLISHER_README_DOCUMENT_RETRIEVED_NOT_MOVEMENT_SCORE",
        "source_doi":spec["source"]["doi"],
        "source_publisher_version":spec["source"]["version_id"],
        "readme_name":"README_file.rtf",
        "readme_sha256":sha(readme),
        "readme_bytes":len(readme),
        "document_plaintext_sha256":sha(text.encode("utf-8")),
        "document_plaintext":text,
        "line_keyword_index":line_terms,
        "doc_lines":len(lines),
        "biological_data_rows_decoded":0,
        "field_outcomes_scored":0,
        "new_EOG_WF_endpoints":0,
        "parent_original_scientific_stop":spec["parent_stop"]["status"],
        "original_STOP_overridden":False,
        "manual_semantic_review_required":True,
        "source_claim_boundary":"Dryad publisher README alone, independent biological distance/movement not calculated"
    }


def run(spec: dict[str, Any]) -> dict[str, Any]:
    if spec.get("status") != "FROZEN_BEFORE_README_CONTENT_RETRIEVAL":
        raise ValueError("STOP_PROTOCOL_NOT_FROZEN")
    transport = json.loads(V2_SOURCE_GATE.read_text(encoding="utf-8"))
    limits = json.loads(V1_SOURCE_GATE.read_text(encoding="utf-8"))["resource_limits"]
    s = spec["source"]
    expected_url=f"https://datadryad.org/api/v2/versions/{s['version_id']}/download"
    if s["official_download_url"] != expected_url:
        raise ValueError("STOP_SOURCE_VERSION_URL_DRIFT")
    publisher_to = next(x for x in transport["sources"] if x["id"] == "toad_jreidini_green_2022")
    if int(publisher_to["version_id"]) != s["version_id"]:
        raise ValueError("STOP_ARCHIVED_VERSION_CHANGED")
    if sorted((x["name"],x["sha256"],x["size"]) for x in publisher_to["expected"]) != sorted(
        (x["name"],x["sha256"],x["bytes"]) for x in s["files"]
    ):
        raise ValueError("STOP_PUBLISHER_MEMBER_SOURCE_DRIFT")
    zip_bytes, _ = _version_zip(s["official_download_url"], limits, transport["exact_trusted_redirect_contract"])
    readme = verify_readme_bytes(zip_bytes, s["files"])
    del zip_bytes
    return _documentation_receipt(readme, spec)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=PROTOCOL)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    spec = json.loads(options.protocol.read_text(encoding="utf-8"))
    try:
        result = run(spec)
    except (ValueError, OSError, urllib.error.URLError, zipfile.BadZipFile) as exc:
        status = str(exc) if str(exc).startswith("STOP_") else "STOP_SOURCE_DOCUMENT_TRANSFER"
        result = {
            "status":status,
            "error_type":type(exc).__name__,
            "parent_original_scientific_stop":spec["parent_stop"]["status"],
            "original_STOP_overridden":False,
            "biological_data_rows_decoded":0,
            "field_outcomes_scored":0,
            "new_EOG_WF_endpoints":0
        }
    canonical = json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    result["sha256_without_self"] = sha(canonical.encode("utf-8"))
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    # Public README is not the raw CSV or a row outcome; log the document only.
    print(json.dumps({"status":result["status"],"doc_lines":result.get("doc_lines"),
        "readme_sha256":result.get("readme_sha256"),
        "full_receipt_sha256_without_self":result["sha256_without_self"],
        "parent_stop":result["parent_original_scientific_stop"]},sort_keys=True))
    if "document_plaintext" in result:
        print("BEGIN_AUTHENTICATED_PUBLISHER_README_DOCUMENT")
        print(result["document_plaintext"])
        print("END_AUTHENTICATED_PUBLISHER_README_DOCUMENT")


if __name__ == "__main__":
    main()
