from __future__ import annotations

import csv
import hashlib
import io
import json
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "neon_forest_coyote_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
OUT = BUILD / "start_year_diagnostic.json"
SOURCE = json.loads((HERE / "source_contract.json").read_text())


def get_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent":"EOG-NEON-year-diagnostic/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def parse_date(s):
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise RuntimeError(f"unsupported date {s!r}")


def main():
    rid = int(SOURCE["zenodo_record_id"])
    spec = SOURCE["response_independent"]["deployments"]
    url = f"https://zenodo.org/records/{rid}/files/{urllib.parse.quote(spec['filename'], safe='')}?download=1"
    raw = get_bytes(url)
    md5 = hashlib.md5(raw).hexdigest()
    if md5 != spec["expected_md5"]:
        raise RuntimeError("deployment MD5 mismatch")
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    token_counts = Counter()
    canonical_counts = Counter()
    cross = Counter()
    examples = defaultdict(list)
    for r in rows:
        did = r["deployment_id"].strip()
        token = r["start_year"].strip()
        year = parse_date(r["start_date"]).year
        token_counts[token] += 1
        canonical_counts[str(year)] += 1
        cross[(token, str(year))] += 1
        if len(examples[(token, str(year))]) < 5:
            examples[(token, str(year))].append(did)
    out = {
        "schema":"eog.neon_forest_coyote_replication_2.start_year_diagnostic.v1",
        "deployment_rows":len(rows),
        "deployment_md5":md5,
        "auxiliary_start_year_token_counts":dict(sorted(token_counts.items())),
        "canonical_start_date_year_counts":dict(sorted(canonical_counts.items())),
        "cross_tab":[
            {"auxiliary_start_year":a,"canonical_start_date_year":y,"count":n,"example_deployment_ids":examples[(a,y)]}
            for (a,y),n in sorted(cross.items())
        ],
        "response_firewall":{
            "sequence_payload_requests":0,
            "sequence_payload_bytes_opened":0,
            "sequence_header_bytes_opened":0,
            "sequence_rows_opened":False,
            "sequence_values_opened":False,
            "model_fits":0,
            "heldout_scores":0
        }
    }
    out["fingerprint"] = hashlib.sha256(json.dumps(out,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True,ensure_ascii=False))


if __name__ == "__main__":
    main()
