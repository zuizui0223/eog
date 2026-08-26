from __future__ import annotations

import json
from pathlib import Path

import gate1_response_independent_profile as gate1

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "build" / "vermont_american_marten_replication_2" / "gate4_response_schema_context.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

FOCAL_TOKENS = ("american marten", "martes americana", "marten", "180559")
TARGET_TABLE_TOKENS = (
    "annotations", "annotationverifications", "annotags",
    "media", "taxa", "librarylists", "librarylistitems",
)


def clean_row(row):
    return {str(k): str(v or "").strip() for k, v in row.items() if str(v or "").strip()}


def matching_rows(rows, tokens):
    out = []
    for i, row in enumerate(rows, 1):
        text = " | ".join(str(v or "") for v in row.values()).casefold()
        if any(t.casefold() in text for t in tokens):
            out.append({"row_index": i, "values": clean_row(row)})
    return out


def write(result):
    result["fingerprint"] = gate1.fp({k: v for k, v in result.items() if k != "fingerprint"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


def main():
    result = {
        "schema": "eog.vermont_american_marten_replication_2.gate4_response_schema_context.v1",
        "attempt_id": gate1.CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "files": {},
        "dbdictionary_target_rows": [],
        "focal_lookup_rows": {},
        "resolved_library_searchlists_containing_focal_taxon": [],
        "biological_response_firewall": dict(gate1.CONTRACT["biological_response_firewall"]),
    }
    try:
        item_id = gate1.CONTRACT["sciencebase"]["item_id"]
        item, _, _ = gate1.get_json(f"https://www.sciencebase.gov/catalog/item/{item_id}?format=json")
        parsed = {}
        for name in (
            "dbdictionary.csv", "taxa.csv", "librarylists.csv", "librarylistitems.csv",
            "lists.csv", "listitems.csv", "medialists.csv", "medialistitems.csv",
        ):
            raw, meta = gate1.fetch_allowed(item, name, gate1.ALLOWED[name])
            header, rows, enc, delim = gate1.decode(raw, name)
            parsed[name] = (header, rows)
            result["files"][name] = {
                **meta,
                "header": header,
                "row_count": len(rows),
                "encoding": enc,
                "delimiter": delim,
            }

        dh, dr = parsed["dbdictionary.csv"]
        result["dbdictionary_target_rows"] = matching_rows(dr, TARGET_TABLE_TOKENS)
        for name in ("taxa.csv", "librarylists.csv", "librarylistitems.csv", "lists.csv", "listitems.csv", "medialists.csv", "medialistitems.csv"):
            _, rows = parsed[name]
            result["focal_lookup_rows"][name] = matching_rows(rows, FOCAL_TOKENS)

        # Resolve library search lists containing the prospectively frozen focal taxon,
        # but only if the response-independent physical schemas expose the expected FK columns.
        ll_header, ll_rows = parsed["librarylists.csv"]
        lli_header, lli_rows = parsed["librarylistitems.csv"]
        focal_taxon_id = "American Marten"
        list_id_col = "pk_librarylistid" if "pk_librarylistid" in ll_header else None
        item_list_fk = "fk_librarylistid" if "fk_librarylistid" in lli_header else None
        item_taxon_fk = "fk_taxonid" if "fk_taxonid" in lli_header else None
        if list_id_col and item_list_fk and item_taxon_fk:
            lists = {str(r.get(list_id_col) or "").strip(): clean_row(r) for r in ll_rows}
            resolved = []
            for row in lli_rows:
                if str(row.get(item_taxon_fk) or "").strip() != focal_taxon_id:
                    continue
                lid = str(row.get(item_list_fk) or "").strip()
                resolved.append({
                    "library_list_id": lid,
                    "library_list_row": lists.get(lid),
                    "library_list_item_row": clean_row(row),
                })
            result["resolved_library_searchlists_containing_focal_taxon"] = resolved

        result["status"] = "gate4_response_schema_context_complete"
        result["reason"] = "Only response-independent dictionary/taxonomy/list lookup tables were opened; response table relationships and focal-search-list context were extracted without biological response access"
        write(result)
        return 0
    except Exception as exc:
        result["status"] = "engineering_failure_pre_response"
        result["reason"] = f"{type(exc).__name__}: {exc}"
        write(result)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
