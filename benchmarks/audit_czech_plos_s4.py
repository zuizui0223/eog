#!/usr/bin/env python3
"""Pre-outcome structural audit of the Czech dry-grassland PLOS S4 table.

This script intentionally inspects only source integrity and table structure. It never
computes species eligibility, fits local support, constructs EOG graphs, or evaluates
species outcomes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import urllib.request
from pathlib import Path

PLOS_S4_URLS = [
    "https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0223826.s011&type=supplementary",
    "https://journals.plos.org/plosone/article/file?type=supplementary&id=info:doi/10.1371/journal.pone.0223826.s011",
]


def _fetch() -> tuple[bytes, str]:
    last = None
    for url in PLOS_S4_URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "eog-preoutcome-audit/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
                ctype = r.headers.get("content-type", "")
            if len(data) < 100 or b"<html" in data[:500].lower():
                raise RuntimeError(f"non-data response ({len(data)} bytes, {ctype})")
            return data, url
        except Exception as exc:  # pragma: no cover - network dependent
            last = exc
    raise RuntimeError(f"could not retrieve PLOS S4 from frozen URLs: {last}")


def _detect_delimiter(text: str) -> str:
    sample = "\n".join(text.splitlines()[:20])
    try:
        return csv.Sniffer().sniff(sample, delimiters="\t;,|").delimiter
    except csv.Error:
        return "\t"


def _classify(headers: list[str]) -> dict[str, list[str]]:
    groups = {k: [] for k in ["patch_id", "coordinates", "pairwise_geometry", "abiotic", "landscape", "diversity_outcomes"]}
    for h in headers:
        x = re.sub(r"[^a-z0-9]+", "_", h.lower()).strip("_")
        if re.search(r"(^|_)(patch|site|id)($|_)", x):
            groups["patch_id"].append(h)
        if re.search(r"(^|_)(x|y|lon|long|longitude|lat|latitude|easting|northing|coord)($|_)", x):
            groups["coordinates"].append(h)
        if re.search(r"distance|dist_|adjacency|neighbor|neighbour|edge", x):
            groups["pairwise_geometry"].append(h)
        if re.search(r"slope|irradi|solar|twi|wetness|elev|abiotic", x):
            groups["abiotic"].append(h)
        if re.search(r"area|isol|age|histor|present|1954|1980|1843", x):
            groups["landscape"].append(h)
        if re.search(r"divers|richness|phylo|functional|species_number|sd$|fd$|pd$", x):
            groups["diversity_outcomes"].append(h)
    return groups


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    p.add_argument("--input", help="Optional already-downloaded S4 TXT; network is skipped")
    args = p.parse_args()

    if args.input:
        data = Path(args.input).read_bytes()
        source = str(Path(args.input))
    else:
        data, source = _fetch()

    text = data.decode("utf-8-sig", errors="replace")
    delim = _detect_delimiter(text)
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    if not rows:
        raise RuntimeError("S4 table is empty")
    headers = [c.strip() for c in rows[0]]
    n_data_rows = sum(1 for r in rows[1:] if any(c.strip() for c in r))
    groups = _classify(headers)

    geometry_gate = bool(groups["coordinates"] or groups["pairwise_geometry"])
    manifest = {
        "status": "preoutcome_schema_audit",
        "source": source,
        "doi": "10.1371/journal.pone.0223826.s011",
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "delimiter_repr": repr(delim),
        "n_columns": len(headers),
        "n_data_rows": n_data_rows,
        "expected_published_patches": 272,
        "headers": headers,
        "structural_column_groups": groups,
        "full_eog_geometry_gate": "pass" if geometry_gate else "fail",
        "geometry_rule": "coordinates or explicit pairwise geometry required; scalar isolation alone does not pass",
        "scientific_boundary": "schema only; no species filtering, support fit, graph construction, or EOG outcome",
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
