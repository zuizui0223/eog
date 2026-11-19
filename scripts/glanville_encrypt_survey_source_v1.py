#!/usr/bin/env python3
"""One-shot AES-GCM+RSA-OAEP *encrypted-only* export of SHA-locked public 2019 survey.

For local crosswalking with a user-provided, SHA-verified 2022 family-assignment
CSV, the Github runner obtains a public Zenodo 2019 archive but produces ONLY
an authenticated ciphertext. The private key is never present on Github.
Neither observed patch IDs nor patch/year statuses are logged or stored in
plaintext in Github artifacts or repository.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import urllib.error
import urllib.request
import zlib
import zipfile


class SourceStop(Exception):
    pass


def _require_headers(reader: csv.DictReader, required: tuple[str,...], member: str):
    columns=reader.fieldnames or []
    if any(k not in columns for k in required):
        raise SourceStop("STOP_SOURCE_SCHEMA_HEADERS_"+member)


def _norm_patch(s: str) -> str:
    s=str(s or "").strip()
    if not s:
        raise SourceStop("STOP_EMPTY_SITE_IDENTIFIER")
    # Preserve canonical integer site ID form without leading zero guessing.
    try:
        v=int(s)
    except (ValueError,TypeError) as e:
        raise SourceStop("STOP_NONINTEGER_SITE_IDENTIFIER") from e
    if v<0 or str(v)!=s:
        raise SourceStop("STOP_NONCANONICAL_SITE_IDENTIFIER")
    return s


def _convert(z: zipfile.ZipFile, protocol: dict) -> dict:
    require=set(protocol["prior_source_repository"]["expected_tables"])
    if not require.issubset(set(z.namelist())):
        raise SourceStop("STOP_ARCHIVE_TABLE_MISSING")
    years=set(protocol["max_public_years"])
    if len(years)!=6 or min(years)!=2007 or max(years)!=2012:
        raise SourceStop("STOP_DECLARED_YEAR_WINDOW_CHANGED")
    observed=[]
    seen=set()
    with z.open("data/survey_data.tsv") as source:
        reader=csv.DictReader(io.TextIOWrapper(source,encoding="utf-8-sig",newline=""),delimiter="\t")
        _require_headers(reader,("year","patch","population","plantago","veronica"),"survey")
        for row in reader:
            raw_year=str(row.get("year") or "").strip()
            if not raw_year or raw_year.lower() in ("na","nan"):
                continue
            try:
                y=int(raw_year)
            except ValueError as exc:
                raise SourceStop("STOP_YEAR_PARSE") from exc
            if y not in years:
                continue
            patch=_norm_patch(row["patch"])
            key=(y,patch)
            if key in seen:
                raise SourceStop("STOP_SURVEY_DUPLICATE_YEAR_PATCH")
            seen.add(key)
            observed.append([y,patch,str(row.get("population") or "").strip(),
                             str(row.get("plantago") or "").strip(),
                             str(row.get("veronica") or "").strip()])
    network=[]
    seen_sites=set()
    with z.open("data/patch_network.tsv") as source:
        reader=csv.DictReader(io.TextIOWrapper(source,encoding="utf-8-sig",newline=""),delimiter="\t")
        _require_headers(reader,("patch","x","y"),"network")
        for row in reader:
            patch=_norm_patch(row["patch"])
            if patch in seen_sites:
                raise SourceStop("STOP_NETWORK_DUPLICATE_SITE")
            seen_sites.add(patch)
            network.append([patch,str(row.get("x") or "").strip(),str(row.get("y") or "").strip()])
    if len(observed)<5000 or len(network)<1000:
        raise SourceStop("STOP_SOURCE_DATA_UNEXPECTEDLY_SMALL")
    return {"schema_version":1,"years":sorted(years),"survey":observed,"network":network,
            "coordinate_original_units":"EPSG3067 original publisher README x/y kilometers"}


def _seal(dataset: dict, protocol: dict) -> dict:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    public=protocol["ephemeral_encryption_public_key_pem"].encode("ascii")
    if hashlib.sha256(public).hexdigest()!=protocol["public_key_sha256"]:
        raise SourceStop("STOP_PUBLIC_KEY_FINGERPRINT")
    key=serialization.load_pem_public_key(public)
    secret=os.urandom(32)
    nonce=os.urandom(12)
    aad=("EOG-audit-v1|"+protocol["prior_source_repository"]["archive_sha256"]).encode()
    plaintext=zlib.compress(json.dumps(dataset,separators=(",",":"),ensure_ascii=False).encode("utf-8"),level=9)
    ciphertext=AESGCM(secret).encrypt(nonce,plaintext,aad)
    wrapped=key.encrypt(secret,padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                            algorithm=hashes.SHA256(),label=None))
    b64=lambda b:base64.b64encode(b).decode("ascii")
    return {
        "schema_version":1,
        "status":"ENCRYPTED_SURVEY_SOURCE_ONLY_NO_PUBLIC_ROW_RECORDS",
        "public_source_archive_sha256":protocol["prior_source_repository"]["archive_sha256"],
        "public_key_sha256":protocol["public_key_sha256"],
        "encoding":"RSA-OAEP-SHA256+AES-256-GCM, zlib+JSON; private key local only",
        "nonce_b64":b64(nonce),"wrapped_key_b64":b64(wrapped),"ciphertext_b64":b64(ciphertext),
        "survey_row_count":len(dataset["survey"]),"spatial_patch_count":len(dataset["network"]),
        "uncompressed_bytes_before_encryption":len(plaintext),
        "rows_or_site_identifiers_logged":0
    }


def acquire(protocol: dict, output: Path) -> dict:
    if protocol.get("status")!="frozen_after_user_file_inspection_before_crosswalk":
        raise SourceStop("STOP_PROTOCOL_NOT_FROZEN")
    source=protocol["prior_source_repository"]
    sha=hashlib.sha256()
    with tempfile.TemporaryDirectory(prefix="eog_source_export_") as temp:
        zipfile_path=Path(temp)/"public_source.zip"
        url=source["archive_url"]
        if not url.startswith("https://zenodo.org/records/4987060/files/ECOG-04799.zip"):
            raise SourceStop("STOP_SOURCE_URL_CHANGED")
        request=urllib.request.Request(url,headers={"Accept":"*/*","User-Agent":"EOG-ephemeral-encrypted-audit/1.0"})
        size=0
        try:
            with urllib.request.urlopen(request,timeout=40) as response,zipfile_path.open("wb") as sink:
                for block in iter(lambda:response.read(1024*1024),b""):
                    size+=len(block)
                    if size>source["max_bytes"]:
                        raise SourceStop("STOP_ARCHIVE_BYTES")
                    sha.update(block)
                    sink.write(block)
        except urllib.error.HTTPError as exc:
            raise SourceStop(f"STOP_HTTP_{exc.code}") from exc
        except (urllib.error.URLError,TimeoutError,OSError) as exc:
            raise SourceStop("STOP_SOURCE_TRANSPORT_"+type(exc).__name__) from exc
        if sha.hexdigest()!=source["archive_sha256"]:
            raise SourceStop("STOP_ARCHIVE_SHA_MISMATCH")
        with zipfile.ZipFile(zipfile_path) as z:
            if len(z.infolist())>2000 or sum(i.file_size for i in z.infolist())>100_000_000:
                raise SourceStop("STOP_ARCHIVE_ZIP_RESOURCE_BUDGET")
            dataset=_convert(z,protocol)
        sealed=_seal(dataset,protocol)
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(sealed,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps({
            "status":sealed["status"],
            "survey_row_count":sealed["survey_row_count"],
            "spatial_patch_count":sealed["spatial_patch_count"],
            "raw_records_published":0,
            "encrypted_artifact_file":str(output),
        },sort_keys=True))
        return sealed


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",type=Path,default=Path("validation/glanville_uploaded_origin_crosswalk_v1/protocol_v1.json"))
    p.add_argument("--output",type=Path,default=Path("results/glanville_uploaded_origin_crosswalk_v1/encrypted_survey.json"))
    args=p.parse_args()
    acquire(json.loads(args.protocol.read_text()),args.output)


if __name__=="__main__":
    main()
