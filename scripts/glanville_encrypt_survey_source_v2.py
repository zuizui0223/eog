#!/usr/bin/env python3
"""One-shot source-locked 2019 EOG survey ciphertext for genetic host-gate audit v2.

New ephemeral key, original 2019 survey archive, original v1 authenticated
encryption. No survey identifiers or raw rows exported from GitHub.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import runpy

def map_protocol(p: dict) -> dict:
    if p["status"]!="pre_crosswalk_source_reacquisition_frozen" or p["schema_version"]!=2:
        raise ValueError("STOP_V2_PROTOCOL_STATUS")
    s=p["source_provider_contract"]
    e=p["encrypted_bridge"]
    if (
        p["source_identifiers"]["publisher_zip_Schulz2019_Zenodo_4987060_SHA256"]!=s["prior_source_repository"]["archive_sha256"]
        or s["max_public_years"]!=[2007,2008,2009,2010,2011,2012]
        or not e["ciphertext_only"]
        or hashlib.sha256(e["rsa_public_key_pem"].encode("ascii")).hexdigest()!=e["public_key_sha256"]
    ):
        raise ValueError("STOP_SOURCE_REACQUISITION_IDENTITY")
    return {
        "status":"frozen_after_user_file_inspection_before_crosswalk",
        "prior_source_repository":s["prior_source_repository"],
        "ephemeral_encryption_public_key_pem":e["rsa_public_key_pem"],
        "public_key_sha256":e["public_key_sha256"],
        "max_public_years":s["max_public_years"],
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--protocol",type=Path,default=Path("validation/glanville_genetic_host_world_v2/protocol_v2.json"))
    parser.add_argument("--output",type=Path,default=Path("results/glanville_genetic_host_world_v2/encrypted_survey.json"))
    args=parser.parse_args()
    p=json.loads(args.protocol.read_text(encoding="utf-8"))
    locked=map_protocol(p)
    legacy=runpy.run_path("scripts/glanville_encrypt_survey_source_v1.py")
    legacy["acquire"](locked,args.output)


if __name__=="__main__":
    main()
