"""Purely synthetic exercise of the 2025-only offline first-line gate."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
sys.path.insert(0, str(ROOT / "scripts"))
from extract_helgeland_2025_parent_recruit_firstline_v1 import extract_2025
from extract_helgeland_verified_firstline_v1 import prepare_write_paths


def sources(tmp_path):
    contract = json.loads((BASE / "helgeland_parent_recruit_2025_sourceonly_v1.json").read_text())
    metadata = copy.deepcopy(json.loads(
        (BASE / "helgeland_source_metadata_frozen_v1.json").read_text()))
    root = tmp_path / "local-source"
    folder = root / "fitness_2025"
    folder.mkdir(parents=True)
    declarations = {}
    for name, role in contract["expected_headers"].items():
        simulated_data = ("\t".join(role["required_exact"]) + "\n" +
                          "\t".join(["secret_synthetic_bird_value"] * len(role["required_exact"]))
                          + "\n").encode("utf-8")
        (folder / name).write_bytes(simulated_data)
        pinned = next(f for f in metadata["inventories"]["fitness_2025"]["files"]
                      if f["name"] == name)
        pinned["size_bytes"] = len(simulated_data)
        pinned["source_declared_sha256"] = hashlib.sha256(simulated_data).hexdigest()
        declarations[name] = "TAB"
    return root, contract, metadata, declarations


def test_four_file_2025_only_header_gate_keeps_scientific_hold(tmp_path):
    root, contract, metadata, declared = sources(tmp_path)
    attestation, receipt = extract_2025(root, contract, metadata, declared)
    assert attestation["source_version_id"] == 354268
    assert {r["file_name"] for r in attestation["records"]} == set(contract["expected_headers"])
    assert receipt["files_checked"] == 4
    assert receipt["status"] == "HEADER_ONLY_BYTE_IDENTITY_VERIFIED__TEMPORAL_HOLD"
    assert receipt["whole_source_file_bytes_read_for_hash"] is True
    for field in ("biological_response_rows_parsed", "parent_recruit_key_values_joined",
                  "parent_breeding_island_at_offspring_birth_verified",
                  "offspring_first_settlement_time_and_island_verified",
                  "prospective_prediction_authorized", "ecological_endpoint_authorized"):
        assert receipt[field] is False
    assert "secret_synthetic_bird_value" not in json.dumps([attestation, receipt])


def test_data_row_byte_tampering_is_detected_without_decoding_row(tmp_path):
    root, contract, metadata, declared = sources(tmp_path)
    path = root / "fitness_2025" / "Rectype_LRS.txt"
    raw = path.read_bytes()
    changed = raw.replace(b"secret_synthetic_bird_value",
                          b"SECRET_SYNTHETIC_BIRD_VALUE")
    assert len(raw) == len(changed)
    path.write_bytes(changed)
    with pytest.raises(ValueError, match="independent SHA256"):
        extract_2025(root, contract, metadata, declared)


def test_missing_pinned_field_is_not_accepted(tmp_path):
    root, contract, metadata, declared = sources(tmp_path)
    path = root / "fitness_2025" / "Rectype_ARS_Survival.txt"
    blob = path.read_bytes().replace(b"flok.year", b"other.year")
    path.write_bytes(blob)
    record = next(x for x in metadata["inventories"]["fitness_2025"]["files"]
                  if x["name"] == "Rectype_ARS_Survival.txt")
    record["size_bytes"] = len(blob)
    record["source_declared_sha256"] = hashlib.sha256(blob).hexdigest()
    with pytest.raises(ValueError, match="mandatory README roles"):
        extract_2025(root, contract, metadata, declared)


def test_source_only_cross_archive_route_is_not_used(tmp_path):
    root, contract, metadata, declared = sources(tmp_path)
    (root / "pedigree_2024").mkdir()
    (root / "pedigree_2024" / "SNPpedigree_GeneticArchitecture.txt").write_bytes(b"unused")
    evidence, _ = extract_2025(root, contract, metadata, declared)
    assert all(record["file_name"] not in ("GGAM_data_GeneticArchitecture.txt",
                                          "SNPpedigree_GeneticArchitecture.txt")
               for record in evidence["records"])


def test_wrong_version_or_delimiter_rejected(tmp_path):
    root, contract, metadata, declared = sources(tmp_path)
    contract["source"]["dryad_version_id"] = -1
    with pytest.raises(ValueError, match="Changed source version"):
        extract_2025(root, contract, metadata, declared)
    root, contract, metadata, declared = sources(tmp_path)
    declared["LRS.txt"] = "COMMA"
    with pytest.raises(ValueError, match="Declared physical delimiter absent"):
        extract_2025(root, contract, metadata, declared)


def test_no_clobber_and_symlink_guard_inherited(tmp_path):
    root, _, _, _ = sources(tmp_path)
    good = tmp_path / "attestation.header-only.json"
    receipt = tmp_path / "receipt.json"
    assert prepare_write_paths(root, good, receipt)[1:] == (good, receipt)
    good.write_text("keep")
    with pytest.raises(ValueError, match="Refusing to overwrite"):
        prepare_write_paths(root, good, receipt)
    good.unlink()
    good.symlink_to(root / "fitness_2025" / "LRS.txt")
    with pytest.raises(ValueError, match="Refusing to overwrite"):
        prepare_write_paths(root, good, receipt)


def test_offline_no_download_or_bird_row_parser():
    source=(ROOT / "scripts/extract_helgeland_2025_parent_recruit_firstline_v1.py").read_text()
    for forbidden in ("urlopen(", "import requests", "import urllib", "read_csv(",
                      "import pandas", "import numpy", "/download", "socket."):
        assert forbidden not in source
    assert "sha256_bytes" in source and "tokenize_header" in source
