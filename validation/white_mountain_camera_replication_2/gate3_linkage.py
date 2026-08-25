from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import gate2_dictionary as d

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "white_mountain_camera_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "gate3_linkage_contract.json").read_text())
OUT = BUILD / "gate3_linkage.json"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fp(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def row_text(row, header):
    return " | ".join(str(row.get(c) or "") for c in header).lower()


def main():
    result = {
        "schema": "eog.white_mountain_camera_replication_2.gate3_linkage.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "sciencebase_inventory": {},
        "dictionary": {},
        "linkage_rows": [],
        "linkage_summary": {},
        "response_firewall": dict(CONTRACT["response_firewall"]),
    }
    try:
        item = d.get_json(f"https://www.sciencebase.gov/catalog/item/{CONTRACT['sciencebase_item_id']}?format=json")
        files = [x for x in (item.get("files") or []) if isinstance(x, dict)]
        inventory = []
        for f in files:
            name = d.fname(f)
            inventory.append({
                "name": name,
                "size": f.get("size"),
                "content_type": f.get("contentType"),
                "md5": d.checksum_md5_from_meta(f),
            })
        inventory.sort(key=lambda x: str(x["name"]).lower())
        csv_names = [x["name"] for x in inventory if str(x["name"]).lower().endswith(".csv")]
        deployment_like = [
            n for n in csv_names
            if any(t in str(n).lower() for t in ("deploy", "rutc", "camera", "station", "site", "location", "visit", "effort", "occasion"))
        ]
        result["sciencebase_inventory"] = {
            "title": item.get("title"),
            "top_level_file_count": len(inventory),
            "top_level_csv_count": len(csv_names),
            "top_level_files": inventory,
            "deployment_or_effort_like_csvs": deployment_like,
        }

        allowed = CONTRACT["allowed_payloads"]["dbdictionary.csv"]
        matches = [x for x in files if d.fname(x) == "dbdictionary.csv"]
        if len(matches) != 1:
            raise RuntimeError(f"expected one dbdictionary.csv, found {len(matches)}")
        f = matches[0]
        if int(f.get("size")) != int(allowed["size"]):
            raise RuntimeError("dbdictionary size metadata drift")
        meta_md5 = d.checksum_md5_from_meta(f)
        if meta_md5 != allowed["md5"]:
            raise RuntimeError(f"dbdictionary MD5 metadata drift: {meta_md5}")
        url = d.furl(f)
        if not url:
            raise RuntimeError("dbdictionary.csv lacks public download URL")
        raw, _, _ = d.get_bytes(url)
        if len(raw) != int(allowed["size"]):
            raise RuntimeError("dbdictionary payload size mismatch")
        actual_md5 = hashlib.md5(raw).hexdigest()
        if actual_md5 != allowed["md5"]:
            raise RuntimeError("dbdictionary payload MD5 mismatch")
        header, rows, enc, delim = d.decode(raw)

        table_col = "database_tablename"
        field_col = "table_field"
        if table_col not in header or field_col not in header:
            raise RuntimeError(f"dictionary schema missing table/field columns: {header}")
        table_counts = Counter(str(r.get(table_col) or "").strip() for r in rows)
        all_tables = sorted(k for k in table_counts if k)
        deployment_tables = [t for t in all_tables if "deploy" in t.lower() or "rutc" in t.lower()]

        target_tables = {x.lower() for x in CONTRACT["dictionary_tables_of_interest"]}
        field_terms = [x.lower() for x in CONTRACT["dictionary_field_terms_of_interest"]]
        linkage_rows = []
        by_table_fields = defaultdict(list)
        for i, row in enumerate(rows, start=2):
            table = str(row.get(table_col) or "").strip()
            field = str(row.get(field_col) or "").strip()
            text = row_text(row, header)
            table_low = table.lower()
            keep = (
                table_low in target_tables
                or "deploy" in table_low
                or "rutc" in table_low
                or table_low in {"visits", "media", "annotations", "taxa"}
            ) and any(term in text for term in field_terms)
            if keep:
                clean = {c: row.get(c) for c in header}
                linkage_rows.append({"physical_line": i, "row": clean})
                by_table_fields[table].append(field)

        # Extract exact relation candidates using field names/descriptions only.
        relation_candidates = []
        for itemrow in linkage_rows:
            row = itemrow["row"]
            table = str(row.get(table_col) or "").strip()
            field = str(row.get(field_col) or "").strip()
            text = row_text(row, header)
            if any(token in field.lower() for token in ("fk_", "pk_", "location", "visit", "deploy", "date", "time")) or "foreign key" in text:
                relation_candidates.append(itemrow)

        media_visit_rows = [
            x for x in relation_candidates
            if str(x["row"].get(table_col) or "").strip().lower() == "media"
            and "visit" in str(x["row"].get(field_col) or "").lower()
        ]
        media_deployment_rows = [
            x for x in relation_candidates
            if str(x["row"].get(table_col) or "").strip().lower() == "media"
            and "deploy" in str(x["row"].get(field_col) or "").lower()
        ]
        deployment_location_rows = [
            x for x in relation_candidates
            if ("deploy" in str(x["row"].get(table_col) or "").lower() or "rutc" in str(x["row"].get(table_col) or "").lower())
            and "location" in (str(x["row"].get(field_col) or "") + " " + str(x["row"].get("description") or "")).lower()
        ]

        released_deployment_like = [
            n for n in deployment_like
            if str(n).lower() not in {"locations.csv", "visits.csv"}
        ]

        result["dictionary"] = {
            "bytes": len(raw),
            "md5": actual_md5,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "encoding": enc,
            "delimiter": delim,
            "header": header,
            "row_count": len(rows),
            "table_count": len(all_tables),
            "deployment_like_tables": deployment_tables,
            "selected_table_field_catalog": {k: sorted(set(v)) for k, v in sorted(by_table_fields.items())},
        }
        result["linkage_rows"] = relation_candidates
        result["linkage_summary"] = {
            "released_deployment_like_csvs_beyond_locations_visits": released_deployment_like,
            "media_visit_link_row_count": len(media_visit_rows),
            "media_deployment_link_row_count": len(media_deployment_rows),
            "deployment_location_link_row_count": len(deployment_location_rows),
            "media_visit_link_rows": media_visit_rows,
            "media_deployment_link_rows": media_deployment_rows,
            "deployment_location_link_rows": deployment_location_rows,
            "dictionary_has_deployment_table_semantics": bool(deployment_tables),
            "public_release_has_separate_deployment_like_csv": bool(released_deployment_like),
        }
        result["status"] = "gate3_response_free_linkage_profile_complete"
        result["reason"] = "ScienceBase top-level file metadata and the exact dictionary were profiled without opening annotations/media/taxa/model/photo payloads"
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
    raise SystemExit(main())
