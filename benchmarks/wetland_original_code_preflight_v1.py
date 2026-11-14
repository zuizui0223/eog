"""Source-only preflight for published Zenodo R preparation semantics.

Download only two publicly listed R script bytes, check official MD5, and
print bounded line-numbered keyword evidence. Never execute downloaded code,
fit a model, or infer which duplicate interpretation is correct.
"""
import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

RECORD = "https://zenodo.org/records/15044115"
SOURCES = {
    "wetland_amp_q1_multispecies_occu_modelling.R":
        "fcab406cd8a192a07cc97582c19011ad",
    "wetland_amp_q2_multispecies_occu_modelling.R":
        "a2b2f6a30b7243c4b9ece3b5eb75dba6",
}
PATTERN = re.compile(
    r"surv|duplicat|distinct|group_by|pivot|filter|summari|unmarked|occu|hunviphab|select|unique|num",
    re.IGNORECASE,
)
MAX_BYTES = 100000


def bounded_evidence(content, limit=100):
    lines = content.decode("utf-8-sig", errors="replace").splitlines()
    matches = [{"line": n, "text": line.strip()[:220]} for n, line in enumerate(lines, 1)
               if PATTERN.search(line)]
    seed_calls = [{"line": n, "text": line.strip()[:220]} for n, line in enumerate(lines, 1)
                  if not line.lstrip().startswith("#")
                  and re.search(r"\b(?:set\.seed|RNGkind|with_seed)\s*\(", line)]
    return {"line_count": len(lines), "keyword_hit_count": len(matches),
            "explicit_rng_seed_calls": seed_calls,
            "external_rng_state_unverified": True,
            "preparation_lines_8_to_42": [
                {"line": n, "text": lines[n - 1].strip()[:220]}
                for n in range(8, min(len(lines), 42) + 1)
            ],
            "selected_matches": matches[:limit], "truncated": len(matches) > limit}


def fetch_one(filename, expected_md5, timeout=20):
    url = RECORD + "/files/" + filename + "?download=1"
    request = urllib.request.Request(url, headers={
        "Accept": "*/*",
        "User-Agent": "EOG-public-source-method-audit/1.0",
    })
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            return {"status": "SOURCE_STOP_TOO_LARGE", "file": filename}
        observed_md5 = hashlib.md5(data).hexdigest()
        if observed_md5 != expected_md5:
            return {"status": "SOURCE_STOP_MD5_MISMATCH", "file": filename,
                    "observed_md5": observed_md5, "expected_md5": expected_md5}
        return {"status": "VERIFIED_SOURCE_BYTES_NOT_EXECUTED",
                "file": filename, "url": url, "size_bytes": len(data),
                "md5": observed_md5, "sha256": hashlib.sha256(data).hexdigest(),
                "evidence": bounded_evidence(data)}
    except urllib.error.HTTPError as err:
        return {"status": "SOURCE_STOP_HTTP_" + str(err.code), "file": filename}
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        return {"status": "SOURCE_STOP_NETWORK_OR_TIMEOUT", "file": filename,
                "error_type": type(err).__name__}


def run():
    files = [fetch_one(name, md5) for name, md5 in SOURCES.items()]
    complete = all(f["status"] == "VERIFIED_SOURCE_BYTES_NOT_EXECUTED" for f in files)
    result = {
        "schema": "eog.wetland_original_code_preflight_v1",
        "role": "SOURCE_ONLY_UNSCORED",
        "status": "ORIGINAL_SOURCE_CODE_VERIFIED_NOT_INTERPRETED" if complete
                  else "ORIGINAL_SOURCE_CODE_GATE_INCOMPLETE",
        "source": "Mizsei and Wenner (2025), Zenodo 10.5281/zenodo.15044115",
        "files": files,
        "occupancy_fitting_permitted": False,
        "duplicate_identity_adjudicated": False,
        "published_27_vs_archived_29_sites_adjudicated": False,
        "limits": [
            "Keyword matches do not establish data-cleaning or field sampling semantics.",
            "Verification of R code source is not authorization to execute it.",
            "Even a successful source read does not independently establish detection effort or closure.",
            "No new EOG-WF endpoint, ecological model or causal A/B/M inference.",
        ],
    }
    result["fingerprint"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("WETLAND_PUBLISHED_CODE_STATUS=" + result["status"])
    for file in result["files"]:
        print("WETLAND_SOURCE=" + json.dumps({
            key: file[key] for key in
            ("status", "file", "size_bytes", "md5", "sha256") if key in file
        }, sort_keys=True))
        if file.get("evidence"):
            hits = file["evidence"]["selected_matches"]
            print("WETLAND_SOURCE_KEYWORDS=" + json.dumps(hits[:60]))
            print("WETLAND_SOURCE_EXPLICIT_RNG_SEEDS=" + json.dumps({
                "file": file["file"],
                "explicit_calls": file["evidence"]["explicit_rng_seed_calls"],
                "external_state_unverified": True,
            }))
            print("WETLAND_R_PREPARATION=" + json.dumps({
                "file": file["file"],
                "lines": file["evidence"]["preparation_lines_8_to_42"]
            }))
    print("WETLAND_PUBLISHED_CODE_FINGERPRINT=" + result["fingerprint"])
