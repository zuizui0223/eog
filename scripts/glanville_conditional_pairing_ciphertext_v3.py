#!/usr/bin/env python3
"""One-shot publisher-SHA-locked AES-GCM ciphertext export for conditional origin-null v3.

Reuses original signed 2019 public survey ZIP source parser and AES-GCM +
ephemeral RSA-OAEP envelope. The new private key remains local and is never
provided to GitHub or committed. This script has no genetic data or records.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import runpy


def translate(protocol: dict) -> dict:
    if protocol["schema_version"]!=3 or protocol["status"]!="frozen_before_opportunity_null_scoring_and_2019_source_reacquisition":
        raise ValueError("STOP_FROZEN_SOURCE_CONTRACT")
    sources=protocol["sources"]
    envelope=protocol["source_transport"]
    source=sources["survey"]
    pem=envelope["new_local_ephemeral_rsa_public_key_pem"]
    if (hashlib.sha256(pem.encode("ascii")).hexdigest()!=envelope["new_local_ephemeral_rsa_public_key_sha256"]
            or not envelope["ciphertext_only_GitHub_artifact"]
            or not envelope["single_download_no_retry"]
            or source["sha256"]!="c70f43544f61e7273afebfa42ed1d488c3b945efe4d5c68e6557030087ee7fd9"):
        raise ValueError("STOP_SOURCE_REACQUISITION_SIGNATURE")
    return {
        "status":"frozen_after_user_file_inspection_before_crosswalk",
        "prior_source_repository":{
            "archive_url":source["url"],
            "archive_sha256":source["sha256"],
            "max_bytes":source["max_bytes"],
            "expected_tables":["data/survey_data.tsv","data/patch_network.tsv"],
        },
        "ephemeral_encryption_public_key_pem":pem,
        "public_key_sha256":envelope["new_local_ephemeral_rsa_public_key_sha256"],
        "max_public_years":[2007,2008,2009,2010,2011,2012],
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",type=Path,default=Path("validation/glanville_conditional_pairing_null_v3/protocol_v3.json"))
    p.add_argument("--output",type=Path,default=Path("results/glanville_conditional_pairing_null_v3/encrypted_survey.json"))
    args=p.parse_args()
    converted=translate(json.loads(args.protocol.read_text(encoding="utf-8")))
    legacy=runpy.run_path("scripts/glanville_encrypt_survey_source_v1.py")
    sealed=legacy["acquire"](converted,args.output)
    if sealed["status"]!="ENCRYPTED_SURVEY_SOURCE_ONLY_NO_PUBLIC_ROW_RECORDS":
        raise ValueError("STOP_NOT_CIPHERTEXT_ONLY")


if __name__=="__main__":
    main()
