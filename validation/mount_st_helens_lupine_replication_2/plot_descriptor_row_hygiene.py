from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "mount_st_helens_lupine_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "plot_descriptor_row_hygiene.json"
UA = "EOG-Mount-St-Helens-plot-row-hygiene/1.0"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fp(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def get_bytes(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/csv,text/plain,*/*;q=0.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read(5_000_001)
        final = r.geturl()
        ctype = r.headers.get("Content-Type")
    if len(raw) > 5_000_000:
        raise RuntimeError("plot descriptor exceeded 5 MB bound")
    return raw, final, ctype


def decode(raw: bytes):
    text = None
    encoding = None
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = raw.decode(enc)
            encoding = enc
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise RuntimeError("plot descriptor decode failed")
    reader = csv.DictReader(io.StringIO(text), delimiter=",")
    header = list(reader.fieldnames or [])
    rows = list(reader)
    if not header:
        raise RuntimeError("plot descriptor has no header")
    return header, rows, encoding


def clean(v):
    return "" if v is None else str(v).strip()


def main():
    result = {
        "schema": "eog.mount_st_helens_lupine_replication_2.plot_descriptor_row_hygiene.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "plot_descriptor": {},
        "row_hygiene": {},
        "response_firewall": dict(CONTRACT["response_firewall"]),
    }
    try:
        raw, final, ctype = get_bytes(CONTRACT["archive"]["plot_descriptor_url"])
        header, rows, encoding = decode(raw)
        if "PLOT_CODE" not in header:
            raise RuntimeError(f"PLOT_CODE missing; header={header}")

        fully_blank = []
        blank_code = []
        nonblank_codes = []
        for idx, row in enumerate(rows, start=2):  # line 1 is header
            values = {str(k): clean(v) for k, v in row.items() if k is not None}
            nonempty = {k: v for k, v in values.items() if v != ""}
            code = clean(row.get("PLOT_CODE"))
            if not nonempty:
                fully_blank.append(idx)
            if not code:
                blank_code.append({
                    "csv_line_number": idx,
                    "nonempty_fields": nonempty,
                })
            else:
                nonblank_codes.append(code)

        counts = Counter(nonblank_codes)
        duplicates = {k: v for k, v in sorted(counts.items()) if v > 1}
        result["plot_descriptor"] = {
            "url": CONTRACT["archive"]["plot_descriptor_url"],
            "final_url": final,
            "content_type": ctype,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "encoding": encoding,
            "header": header,
            "raw_dictreader_row_count": len(rows),
        }
        result["row_hygiene"] = {
            "published_plot_count": int(CONTRACT["archive"]["published_plot_descriptor_rows"]),
            "fully_blank_row_count": len(fully_blank),
            "fully_blank_csv_line_numbers": fully_blank,
            "blank_plot_code_row_count": len(blank_code),
            "blank_plot_code_rows": blank_code,
            "nonblank_plot_code_row_count": len(nonblank_codes),
            "unique_nonblank_plot_code_count": len(counts),
            "duplicate_nonblank_plot_codes": duplicates,
            "nonblank_plot_codes_sorted": sorted(nonblank_codes),
            "exactly_92_nonblank_unique_plot_codes": len(nonblank_codes) == 92 and len(counts) == 92 and not duplicates,
        }
        if len(fully_blank) == 4 and len(nonblank_codes) == 92 and len(counts) == 92 and not duplicates:
            result["status"] = "descriptor_hygiene_reveals_exactly_four_fully_blank_trailing_or_internal_rows"
            result["reason"] = "96 DictReader rows consist of 92 unique nonblank plot-code rows plus exactly four fully blank rows; filtering rows with no nonempty fields is deterministic source hygiene and does not use biological response"
        elif len(nonblank_codes) == 96 and len(counts) == 96 and not duplicates:
            result["status"] = "descriptor_hygiene_confirms_96_genuine_plot_rows"
            result["reason"] = "all 96 parsed rows contain unique nonblank plot codes; published 92-plot boundary is not reproduced response-independently"
        else:
            result["status"] = "descriptor_hygiene_ambiguous_nonblank_or_malformed_extra_rows"
            result["reason"] = "row-count discrepancy is not explained by exactly four fully blank rows and cannot be repaired prospectively"
        result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
        result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
