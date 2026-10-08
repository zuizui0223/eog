#!/usr/bin/env python3
"""Read ONLY public Dryad API JSON metadata for two frozen Helgeland DOIs.

No downloads, file-byte reads, physical-header reads, biological rows, or models.
The source-provided digest is NOT verification of bytes. Fail closed on
unavailable metadata or unexpected version/file identities.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://datadryad.org"
SOURCES = {
    "fitness_2025": {
        "doi": "10.5061/dryad.qfttdz0sx",
        "expected": frozenset((
            "ARS_Survival.txt", "LRS.txt", "README.md",
            "Rectype_ARS_Survival.txt", "Rectype_LRS.txt",
        )),
    },
    "pedigree_2024": {
        "doi": "10.5061/dryad.80gb5mkxh",
        "expected": frozenset((
            "GGAM_data_GeneticArchitecture.txt",
            "GWAS_data_genotype_GeneticArchitecture.raw",
            "GWAS_data_phenotype_GeneticArchitecture.dat",
            "README.md", "SNPpedigree_GeneticArchitecture.txt",
        )),
    },
}
VERSION_RE = re.compile(r"^/api/v2/versions/([0-9]+)$")
SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")


def api_json(url: str) -> dict:
    # Constrain this auditor to the two JSON API namespaces: never file downloads.
    parsed = urllib.parse.urlparse(url)
    allowed = (
        re.fullmatch(r"/api/v2/datasets/doi%3A10\.5061%2Fdryad\.[A-Za-z0-9]+", parsed.path, re.I),
        re.fullmatch(r"/api/v2/versions/[0-9]+/files", parsed.path),
    )
    if parsed.scheme != "https" or parsed.netloc != "datadryad.org" or parsed.query or not any(allowed):
        raise ValueError(f"Refusing non-metadata endpoint: {url}")
    request = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "EOG-metadata-only-audit/1.0"}
    )
    with urllib.request.urlopen(request, timeout=25) as stream:
        if "json" not in stream.headers.get("Content-Type", "").lower():
            raise ValueError("Non-JSON source response")
        raw = stream.read(3_000_001)
        if len(raw) > 3_000_000:
            raise ValueError("Unexpectedly large API metadata; refusing")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Unexpected JSON response type")
    return value


def inventory_from_metadata(name: str, dataset: dict, files: dict) -> dict:
    expected = SOURCES[name]
    identifier = dataset.get("identifier", "")
    if identifier.lower() != f"doi:{expected['doi']}".lower():
        raise ValueError(f"{name}: DOI mismatch: {identifier}")
    version_link = dataset.get("_links", {}).get("stash:version", {}).get("href")
    if not isinstance(version_link, str) or not VERSION_RE.fullmatch(version_link):
        raise ValueError(f"{name}: missing authoritative version link")
    version_id = int(VERSION_RE.fullmatch(version_link).group(1))
    embedded = files.get("_embedded", {}).get("stash:files")
    if not isinstance(embedded, list) or len(embedded) == 0:
        raise ValueError(f"{name}: no file list in Dryad JSON")
    if files.get("total") != len(embedded) or files.get("count") != len(embedded):
        raise ValueError(f"{name}: source file inventory incomplete/paginated")
    self_link = files.get("_links", {}).get("self", {}).get("href")
    if self_link != f"/api/v2/versions/{version_id}/files":
        raise ValueError(f"{name}: file inventory version differs from dataset version")
    rows=[]
    for f in embedded:
        path=f.get("path")
        if not isinstance(path, str) or "/" in path or not path or path.startswith("."):
            raise ValueError("Unsafe or missing file name")
        sha=f.get("digest")
        dtype=f.get("digestType")
        size=f.get("size")
        meta_href=f.get("_links",{}).get("self",{}).get("href")
        if not re.fullmatch(r"/api/v2/files/[0-9]+", str(meta_href)):
            raise ValueError(f"{path}: bad file metadata link")
        if not isinstance(size, int) or size <= 0:
            raise ValueError(f"{path}: no positive file size")
        rows.append({
            "name": path,
            "file_metadata_id":int(meta_href.rsplit("/",1)[1]),
            "size_bytes":size,
            "source_declared_digest":sha if isinstance(sha,str) else None,
            "source_declared_digest_type":dtype,
            "sha256_format_valid":bool(isinstance(sha,str) and
                                      dtype in ("sha-256","sha256") and SHA256_RE.fullmatch(sha)),
            "actual_file_bytes_downloaded":False,
            "actual_file_header_read":False,
            "actual_digest_verified_against_downloaded_bytes":False,
        })
    if len(set(x["name"] for x in rows))!=len(rows):
        raise ValueError("Duplicate filename in frozen Dryad inventory")
    names={x["name"] for x in rows}
    if names != expected["expected"]:
        raise ValueError(f"{name}: unexpected Dryad file inventory; missing={sorted(expected['expected']-names)}, extra={sorted(names-expected['expected'])}")
    status=("SOURCE_DECLARED_INVENTORY_WITH_SHA256" if all(x["sha256_format_valid"] for x in rows)
            else "SOURCE_DECLARED_INVENTORY_DIGEST_UNQUALIFIED")
    return {
        "status":status,
        "doi":expected["doi"],
        "dryad_dataset_id":dataset.get("id"),
        "dryad_version_id":version_id,
        "dryad_version_number":dataset.get("versionNumber"),
        "files":sorted(rows,key=lambda x:x["name"]),
        "source_archive_downloaded":False,
        "physical_headers_verified":False,
        "individual_or_fitness_records_opened":False,
        "bird_island_join_verified":False,
    }


def audit() -> dict:
    results={}
    for name, details in SOURCES.items():
        url=API+"/api/v2/datasets/"+urllib.parse.quote("doi:"+details["doi"],safe="")
        try:
            dataset=api_json(url)
            relative=dataset.get("_links",{}).get("stash:version",{}).get("href")
            if not isinstance(relative,str) or not VERSION_RE.fullmatch(relative):
                raise ValueError("No verifiable Dryad version")
            files=api_json(API+relative+"/files")
            results[name]=inventory_from_metadata(name,dataset,files)
        except (urllib.error.URLError,TimeoutError,ValueError,KeyError,json.JSONDecodeError) as e:
            results[name]={
                "status":"METADATA_TRANSPORT_OR_SCHEMA_STOP",
                "doi":details["doi"],
                "error_type":type(e).__name__,
                "error_message":str(e)[:180],
                "actual_file_bytes_downloaded":False,
                "individual_or_fitness_records_opened":False,
                "bird_island_join_verified":False,
            }
    return {
        "schema":"eog.helgeland.public_dryad_api_inventory.v1",
        "stage":"SOURCE_METADATA_ONLY",
        "overall_status":("METADATA_INVENTORIES_RETRIEVED" if all(
            v["status"].startswith("SOURCE_DECLARED_INVENTORY") for v in results.values()
            ) else "HOLD_INCOMPLETE_METADATA_INVENTORY"),
        "datasets":results,
        "new_eog_endpoint_authorized":False,
        "source_declared_digest_is_independent_byte_verification":False,
        "raw_biological_data_opened":False,
        "original_pr619_holds_unchanged":True,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=audit()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"overall_status":report["overall_status"],
                      "source_status":{k:v["status"] for k,v in report["datasets"].items()}}))


if __name__=="__main__":
    main()
