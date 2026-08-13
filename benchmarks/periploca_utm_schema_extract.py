"""Extract only public response-free Periploca population/region/UTM metadata.

No genetic file is accepted by this script.  It exists solely to freeze the exact UTM
syntax and population-region association before coordinate conversion rules are chosen.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path


EXPECTED_GEOGRAPHY_SHA256 = "d54af743f39332aab753964ee0d6950550097d7b29216d155a50967153d5d233"


def _canonical_sha256(value: object) -> str:
    encoded=json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def extract(path: Path) -> dict[str, object]:
    data=path.read_bytes()
    digest=hashlib.sha256(data).hexdigest()
    if digest!=EXPECTED_GEOGRAPHY_SHA256:
        raise ValueError("Periploca geography file SHA drifted")
    text=data.decode("latin-1")
    reader=csv.DictReader(io.StringIO(text),delimiter="\t")
    expected={"Island/region","Population","Voucher","UTM coordinates","Collector(s)",""}
    if set(reader.fieldnames or ())!=expected:
        raise ValueError(f"unexpected Periploca geography schema: {reader.fieldnames}")
    rows=[]
    for index,raw in enumerate(reader,start=1):
        region=str(raw.get("Island/region") or "").strip()
        population=str(raw.get("Population") or "").strip()
        utm=str(raw.get("UTM coordinates") or "").strip()
        if not region or not population or not utm:
            raise ValueError(f"missing response-free region/population/UTM in row {index}")
        rows.append({"row":index,"island_region":region,"population":population,"utm":utm})
    result={
        "status":"periploca-response-free-utm-row-freeze",
        "geography_sha256":digest,
        "n_rows":len(rows),
        "n_populations":len({row['population'] for row in rows}),
        "n_island_regions":len({row['island_region'] for row in rows}),
        "rows":rows,
        "genetic_contents_accessed":False,
    }
    result["fingerprint"]=_canonical_sha256(result)
    return result


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--geography",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=extract(args.geography)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True,allow_nan=False))


if __name__=="__main__":
    main()
