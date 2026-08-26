from __future__ import annotations

import json
from pathlib import Path

import gate1_response_independent_profile as gate1

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "build" / "vermont_american_marten_replication_2" / "gate4b_searchlist_membership.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

SEARCH_LIST_ID = "sp_ch2021"
FOCAL_TOKENS = {"marten", "american marten", "martes americana", "180559"}


def clean(row):
    return {str(k): str(v or "").strip() for k, v in row.items()}


def contains_focal(row):
    text = " | ".join(str(v or "") for v in row.values()).casefold()
    return any(tok in text for tok in FOCAL_TOKENS)


def dictionary_rows(rows, table_names):
    out = []
    needles = {x.casefold() for x in table_names}
    for i, row in enumerate(rows, 1):
        text = " | ".join(str(v or "") for v in row.values()).casefold()
        if any(n in text for n in needles):
            out.append({"row_index": i, "values": clean(row)})
    return out


def write(result):
    result["fingerprint"] = gate1.fp({k: v for k, v in result.items() if k != "fingerprint"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


def main():
    result = {
        "schema": "eog.vermont_american_marten_replication_2.gate4b_searchlist_membership.v3",
        "attempt_id": gate1.CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "search_list_id": SEARCH_LIST_ID,
        "observed_headers": {},
        "librarylist_row": None,
        "list_row": None,
        "librarylistitems_rows": [],
        "listitems_rows": [],
        "focal_librarylistitems_rows": [],
        "focal_listitems_rows": [],
        "dictionary_relationship_rows": [],
        "membership_assessment": {},
        "biological_response_firewall": dict(gate1.CONTRACT["biological_response_firewall"]),
    }
    try:
        item_id = gate1.CONTRACT["sciencebase"]["item_id"]
        item, _, _ = gate1.get_json(f"https://www.sciencebase.gov/catalog/item/{item_id}?format=json")
        parsed = {}
        for name in ("librarylists.csv", "librarylistitems.csv", "lists.csv", "listitems.csv", "dbdictionary.csv", "taxa.csv"):
            raw, _ = gate1.fetch_allowed(item, name, gate1.ALLOWED[name])
            header, rows, _, _ = gate1.decode(raw, name)
            parsed[name] = (header, rows)
            result["observed_headers"][name] = header

        ll_header, ll_rows = parsed["librarylists.csv"]
        lli_header, lli_rows = parsed["librarylistitems.csv"]
        lists_header, lists_rows = parsed["lists.csv"]
        li_header, li_rows = parsed["listitems.csv"]
        _, dict_rows = parsed["dbdictionary.csv"]
        _, taxa_rows = parsed["taxa.csv"]

        # These requirements now use the exact response-independent physical schemas
        # observed in Gate4b v2. They cover only columns actually used by this gate.
        required = {
            "librarylists.csv": ({"pk_librarylistid"}, set(ll_header)),
            "librarylistitems.csv": ({"pk_librarylistitemid", "fk_librarylistid", "item", "description", "sort_order"}, set(lli_header)),
            "lists.csv": ({"pk_listid", "core_list", "description"}, set(lists_header)),
            "listitems.csv": ({"pk_listitemid", "fk_listid", "item", "description", "sort_order"}, set(li_header)),
        }
        for name, (need, have) in required.items():
            missing = need - have
            if missing:
                raise RuntimeError(f"{name} missing required columns {sorted(missing)}; observed={sorted(have)}")

        ll_matches = [clean(r) for r in ll_rows if str(r.get("pk_librarylistid") or "").strip() == SEARCH_LIST_ID]
        if len(ll_matches) != 1:
            result["status"] = "stop_search_library_list_not_unique"
            result["reason"] = f"librarylists has {len(ll_matches)} rows for {SEARCH_LIST_ID}"
            write(result)
            return 0
        result["librarylist_row"] = ll_matches[0]

        list_matches = [clean(r) for r in lists_rows if str(r.get("pk_listid") or "").strip() == SEARCH_LIST_ID]
        result["list_row"] = list_matches[0] if len(list_matches) == 1 else None

        lli_target = [clean(r) for r in lli_rows if str(r.get("fk_librarylistid") or "").strip() == SEARCH_LIST_ID]
        li_target = [clean(r) for r in li_rows if str(r.get("fk_listid") or "").strip() == SEARCH_LIST_ID]
        result["librarylistitems_rows"] = lli_target
        result["listitems_rows"] = li_target
        result["focal_librarylistitems_rows"] = [r for r in lli_target if contains_focal(r)]
        result["focal_listitems_rows"] = [r for r in li_target if contains_focal(r)]
        result["dictionary_relationship_rows"] = dictionary_rows(
            dict_rows,
            ("librarylists", "librarylistitems", "lists", "listitems", "annotations.fk_searchlistid", "annotationverifications.fk_librarylistitemid"),
        )

        focal_taxa = [clean(r) for r in taxa_rows if contains_focal(r)]
        result["focal_taxa_rows"] = focal_taxa

        # Never infer direct library-search membership merely because the controlled
        # list and library list share an ID. A future negative is admissible only if
        # the response-independent librarylistitems rows themselves identify marten.
        direct = result["focal_librarylistitems_rows"]
        controlled = result["focal_listitems_rows"]
        result["membership_assessment"] = {
            "direct_librarylistitem_focal_count": len(direct),
            "controlled_list_focal_count": len(controlled),
            "same_id_librarylist_and_controlled_list": len(list_matches) == 1,
            "direct_membership_proven": len(direct) >= 1,
            "controlled_list_contains_marten": len(controlled) >= 1,
            "cross_table_membership_inference_allowed": False,
        }
        if len(direct) >= 1:
            result["status"] = "gate4b_direct_marten_search_list_membership_proven"
            result["reason"] = "A response-independent librarylistitems row under sp_ch2021 directly identifies the focal marten search item; future absence-coverage rules may use this list after response-schema freeze"
        elif len(controlled) >= 1:
            result["status"] = "stop_direct_search_list_membership_not_proven"
            result["reason"] = "The controlled list sp_ch2021 contains a marten item, but no response-independent librarylistitems row under sp_ch2021 directly identifies marten and no undocumented cross-table mapping is inferred; absence semantics remain unproven"
        else:
            result["status"] = "stop_search_list_does_not_show_marten_membership"
            result["reason"] = "Neither the library search-list items nor the same-ID controlled list provides response-independent marten membership evidence"
        write(result)
        return 0
    except Exception as exc:
        result["status"] = "engineering_failure_pre_response"
        result["reason"] = f"{type(exc).__name__}: {exc}"
        write(result)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
