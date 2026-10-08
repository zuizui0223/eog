"""Synthetic-only tests: no actual Dryad bird, genotype or survival files."""
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
from extract_helgeland_verified_firstline_v1 import (  # noqa: E402
    delimiter_assignments, extract, tokenize_header, prepare_write_paths,
)


def fixture_sources(tmp_path):
    contract = json.loads((BASE / "helgeland_header_schema_contract_v1.json").read_text())
    frozen = json.loads((BASE / "helgeland_source_metadata_frozen_v1.json").read_text())
    fake_inventory = copy.deepcopy(frozen)
    source_root = tmp_path / "private_sources"
    declared = {}
    for key, roles in contract["expected_header_roles"].items():
        source, name = key.split("/", 1)
        path = source_root / source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        # Second line is deliberately synthetic response-looking data.
        contents = ("\t".join(roles["required_exact"]) + "\n" +
                    "\t".join(["secret_synthetic_row_value"] * len(roles["required_exact"])) + "\n").encode()
        path.write_bytes(contents)
        original = next(f for f in fake_inventory["inventories"][source]["files"] if f["name"] == name)
        original["size_bytes"] = len(contents)
        original["source_declared_sha256"] = hashlib.sha256(contents).hexdigest()
        declared[key] = "TAB"
    return source_root, contract, fake_inventory, declared


def test_header_only_verified_identity_stops_before_biological_interpretation(tmp_path):
    root, contract, frozen, declared = fixture_sources(tmp_path)
    evidence, receipt = extract(root, contract, frozen, declared)
    assert evidence["schema"] == "eog.helgeland.header_only_attestation.v1"
    assert len(evidence["records"]) == 4
    assert receipt["status"] == "LOCAL_BYTES_MATCH_SOURCE_DIGEST__HEADER_ONLY__KEYS_UNJOINED"
    assert receipt["biological_scoring_authorized"] is False
    assert receipt["individual_id_and_island_values_joined"] is False
    assert receipt["source_loss_or_first_island_colonization_inferred"] is False
    assert all(item["delimiter"] == "TAB" for item in evidence["records"])
    assert all(item["first_line_only"] and not item["contains_response_values"] for item in evidence["records"])
    assert all(x["source_declared_sha256_matched_by_local_byte_hash"] for x in receipt["checks"].values())
    assert "secret_synthetic_row_value" not in json.dumps([evidence, receipt])


def test_fails_on_same_length_changed_response_bytes(tmp_path):
    root, contract, inventory, declared = fixture_sources(tmp_path)
    path = root / "fitness_2025" / "LRS.txt"
    blob = path.read_bytes()
    assert b"secret_synthetic_row_value" in blob
    path.write_bytes(blob.replace(b"secret_synthetic_row_value", b"SECRET_SYNTHETIC_ROW_VALUE"))
    assert path.stat().st_size == len(blob)
    with pytest.raises(ValueError, match="SHA256 bytes differ"):
        extract(root, contract, inventory, declared)


def test_rejects_incorrect_length_before_digest(tmp_path):
    root, contract, inventory, declared = fixture_sources(tmp_path)
    with (root / "fitness_2025" / "LRS.txt").open("ab") as f:
        f.write(b"\n")
    with pytest.raises(ValueError, match="physical size differs"):
        extract(root, contract, inventory, declared)


def test_rejects_symlinked_source(tmp_path):
    root, contract, inventory, declared = fixture_sources(tmp_path)
    original = root / "pedigree_2024" / "SNPpedigree_GeneticArchitecture.txt"
    other = tmp_path / "outside.txt"
    other.write_bytes(original.read_bytes())
    original.unlink()
    original.symlink_to(other)
    with pytest.raises(ValueError, match="Symlinked"):
        extract(root, contract, inventory, declared)


def test_rejects_header_missing_required_column_even_with_matching_digest(tmp_path):
    root, contract, inventory, declared = fixture_sources(tmp_path)
    path = root / "fitness_2025" / "LRS.txt"
    blob = path.read_bytes().replace(b"adult.island", b"other.island")
    path.write_bytes(blob)
    item = next(x for x in inventory["inventories"]["fitness_2025"]["files"] if x["name"] == "LRS.txt")
    item["size_bytes"] = len(blob)
    item["source_declared_sha256"] = hashlib.sha256(blob).hexdigest()
    with pytest.raises(ValueError, match="required published columns"):
        extract(root, contract, inventory, declared)


def test_rejects_missing_newline_in_physical_first_line(tmp_path):
    path = tmp_path / "x.txt"
    path.write_bytes(b"ID\tnatal.island")
    with pytest.raises(ValueError, match="missing newline"):
        tokenize_header(path, "TAB")


def test_rejects_guessed_or_partial_delimiter_plan(tmp_path):
    _, contract, _, _ = fixture_sources(tmp_path)
    required = set(contract["expected_header_roles"])
    key = sorted(required)[0]
    with pytest.raises(ValueError, match="All four"):
        delimiter_assignments([f"{key}=TAB"], required)
    with pytest.raises(ValueError, match="Unknown, duplicate"):
        delimiter_assignments([f"{key}=BOGUS"], required)
    with pytest.raises(ValueError, match="Unknown, duplicate"):
        delimiter_assignments([f"{key}=TAB", f"{key}=TAB"], required)


def test_wrong_declared_delimiter_is_not_guessed(tmp_path):
    root, contract, inventory, declared = fixture_sources(tmp_path)
    declared["fitness_2025/LRS.txt"] = "COMMA"
    with pytest.raises(ValueError, match="Declared physical delimiter absent"):
        extract(root, contract, inventory, declared)


def test_whitespace_cannot_alias_tab_automatically(tmp_path):
    p = tmp_path / "x.txt"
    p.write_bytes(b"ID\tnatal.island\n")
    with pytest.raises(ValueError, match="ambiguous"):
        tokenize_header(p, "WHITESPACE")


def test_destination_rejects_existing_file_or_symlink(tmp_path):
    root, _, _, _ = fixture_sources(tmp_path)
    evidence = tmp_path / "out" / "real.header-only.json"
    receipt = tmp_path / "out" / "receipt.json"
    evidence.parent.mkdir()
    assert prepare_write_paths(root, evidence, receipt)[1:] == (evidence, receipt)
    evidence.write_text("KEEP", encoding="utf-8")
    with pytest.raises(ValueError, match="Refusing to overwrite"):
        prepare_write_paths(root, evidence, receipt)
    assert evidence.read_text() == "KEEP"
    evidence.unlink()
    evidence.symlink_to(root / "fitness_2025" / "LRS.txt")
    with pytest.raises(ValueError, match="Refusing to overwrite"):
        prepare_write_paths(root, evidence, receipt)


def test_destination_rejects_raw_dir_redirection_and_colliding_outputs(tmp_path):
    root, _, _, _ = fixture_sources(tmp_path)
    evidence = tmp_path / "out" / "first.header-only.json"
    with pytest.raises(ValueError, match="different destinations"):
        prepare_write_paths(root, evidence, evidence)
    with pytest.raises(ValueError, match="inside raw-source"):
        prepare_write_paths(root, root / "nested" / "first.header-only.json", tmp_path / "receipt.json")
    link_dir = tmp_path / "source_alias"
    link_dir.symlink_to(root, target_is_directory=True)
    with pytest.raises(ValueError, match="inside raw-source"):
        prepare_write_paths(root, link_dir / "first.header-only.json", tmp_path / "receipt.json")


def test_source_root_rejects_symlinked_ancestor(tmp_path):
    root, _, _, _ = fixture_sources(tmp_path)
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    evidence = tmp_path / "out" / "first.header-only.json"
    receipt = tmp_path / "out" / "receipt.json"
    with pytest.raises(ValueError, match="symlinked ancestor"):
        prepare_write_paths(alias, evidence, receipt)
    deep_alias = alias / "fitness_2025"
    with pytest.raises(ValueError, match="symlinked ancestor"):
        prepare_write_paths(deep_alias, evidence, receipt)
