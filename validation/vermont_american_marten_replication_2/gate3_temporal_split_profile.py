from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import gate1_response_independent_profile as gate1

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CONTRACT = json.loads((HERE / "gate3_temporal_split_contract.json").read_text())
GATE2_CONTRACT = json.loads((HERE / "gate2_effort_geometry_contract.json").read_text())
GATE2_CERT = json.loads((HERE / "gate2_effort_geometry_certificate.json").read_text())
OUT = ROOT / "build" / "vermont_american_marten_replication_2" / "gate3_temporal_split_profile.json"
OUT.parent.mkdir(parents=True, exist_ok=True)


def parse_float(value):
    text = str(value or "").strip()
    if not text:
        return None
    try:
        x = float(text)
    except ValueError:
        return None
    return x if math.isfinite(x) else None


def parse_media_date(value):
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    try:
        return date.fromisoformat(text[:10])
    except Exception:
        return None


def halfyear(d: date):
    return f"{d.year}H{1 if d.month <= 6 else 2}"


def write(result):
    result["fingerprint"] = gate1.fp({k: v for k, v in result.items() if k != "fingerprint"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


def main():
    result = {
        "schema": "eog.vermont_american_marten_replication_2.gate3_temporal_split_profile.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "reproduced_site_week_registry": {},
        "calibration": {},
        "heldout": {},
        "biological_response_firewall": dict(CONTRACT["biological_response_firewall"]),
    }
    try:
        if GATE2_CERT["fingerprint"] != CONTRACT["input_gate2_fingerprint"]:
            raise RuntimeError("Gate2 certificate fingerprint mismatch")
        item_id = gate1.CONTRACT["sciencebase"]["item_id"]
        item, _, _ = gate1.get_json(f"https://www.sciencebase.gov/catalog/item/{item_id}?format=json")
        parsed = {}
        for name in ("locations.csv", "visits.csv", "media.csv"):
            raw, _ = gate1.fetch_allowed(item, name, gate1.ALLOWED[name])
            header, rows, _, _ = gate1.decode(raw, name)
            parsed[name] = (header, rows)

        # Reproduce the frozen 70-site public proxy eligibility without persisting coordinates.
        _, loc_rows = parsed["locations.csv"]
        registry = set()
        for row in loc_rows:
            if str(row.get("location_type") or "").strip() != GATE2_CONTRACT["site_registry"]["eligible_location_type_exact"]:
                continue
            vals = [parse_float(row.get(c)) for c in ("lat_min", "lat_max", "long_min", "long_max")]
            if any(v is None for v in vals):
                continue
            lat_min, lat_max, lon_min, lon_max = vals
            if not (-90 <= lat_min <= lat_max <= 90 and -180 <= lon_min <= lon_max <= 180):
                continue
            registry.add(str(row.get("pk_locationid") or "").strip())
        if len(registry) != 70:
            raise RuntimeError(f"Gate2 site registry not reproduced: {len(registry)}")

        _, visit_rows = parsed["visits.csv"]
        visit_lookup = {}
        for row in visit_rows:
            vid = str(row.get("pk_visitid") or "").strip()
            if not vid or vid in visit_lookup:
                raise RuntimeError("visit id invalid")
            visit_lookup[vid] = str(row.get("fk_locationid") or "").strip()

        false_tokens = set(GATE2_CONTRACT["effort_endpoint_universe"]["sb_exclude_false_tokens_casefolded"])
        true_tokens = set(GATE2_CONTRACT["effort_endpoint_universe"]["sb_exclude_true_tokens_casefolded"])
        _, media_rows = parsed["media.csv"]
        site_week_media = Counter()
        for row in media_rows:
            token = str(row.get("sb_exclude") or "").strip().casefold()
            if token in true_tokens:
                continue
            if token not in false_tokens:
                raise RuntimeError(f"unexpected sb_exclude token {token!r}")
            vid = str(row.get("fk_visitid") or "").strip()
            lid = visit_lookup.get(vid)
            if lid not in registry:
                continue
            d = parse_media_date(row.get("start_date"))
            if d is None:
                continue
            week = d - timedelta(days=d.weekday())
            site_week_media[(lid, week.isoformat())] += 1

        rows_for_fp = [
            {"location_id": lid, "week_start": week, "media_count": site_week_media[(lid, week)]}
            for lid, week in sorted(site_week_media)
        ]
        registry_fp = gate1.fp(rows_for_fp)
        expected_fp = CONTRACT["input_site_week_registry_fingerprint"]
        if registry_fp != expected_fp:
            raise RuntimeError(f"Gate2 site-week registry fingerprint mismatch: {registry_fp} != {expected_fp}")
        result["reproduced_site_week_registry"] = {
            "site_week_count": len(site_week_media),
            "fingerprint": registry_fp,
        }

        cutoff = date(2018, 1, 1)
        cal = [(lid, date.fromisoformat(week), count) for (lid, week), count in site_week_media.items() if date.fromisoformat(week) < cutoff]
        held = [(lid, date.fromisoformat(week), count) for (lid, week), count in site_week_media.items() if date.fromisoformat(week) >= cutoff]
        if not cal or not held:
            raise RuntimeError("chronological calibration/heldout split produced empty side")

        result["calibration"] = {
            "rule": CONTRACT["calibration"]["rule"],
            "site_week_count": len(cal),
            "site_count": len({x[0] for x in cal}),
            "media_row_count": sum(x[2] for x in cal),
            "earliest_week": min(x[1] for x in cal).isoformat(),
            "latest_week": max(x[1] for x in cal).isoformat(),
            "registry_fingerprint": gate1.fp([
                {"location_id": lid, "week_start": d.isoformat(), "media_count": count}
                for lid, d, count in sorted(cal, key=lambda x: (x[1], x[0]))
            ]),
        }

        unit_rows = defaultdict(list)
        for lid, d, count in held:
            unit_rows[halfyear(d)].append((lid, d, count))
        min_weeks = int(CONTRACT["heldout"]["primary_unit_minimum_label_free_site_weeks"])
        units = []
        primary = []
        supplementary = []
        for unit in sorted(unit_rows):
            vals = unit_rows[unit]
            payload = {
                "unit_id": unit,
                "site_week_count": len(vals),
                "site_count": len({x[0] for x in vals}),
                "media_row_count": sum(x[2] for x in vals),
                "earliest_week": min(x[1] for x in vals).isoformat(),
                "latest_week": max(x[1] for x in vals).isoformat(),
                "primary": len(vals) >= min_weeks,
                "registry_fingerprint": gate1.fp([
                    {"location_id": lid, "week_start": d.isoformat(), "media_count": count}
                    for lid, d, count in sorted(vals, key=lambda x: (x[1], x[0]))
                ]),
            }
            units.append(payload)
            (primary if payload["primary"] else supplementary).append(unit)

        result["heldout"] = {
            "rule": CONTRACT["heldout"]["rule"],
            "outer_unit_rule": CONTRACT["heldout"]["outer_unit"],
            "primary_minimum_label_free_site_weeks": min_weeks,
            "total_site_week_count": len(held),
            "total_site_count": len({x[0] for x in held}),
            "total_media_row_count": sum(x[2] for x in held),
            "units": units,
            "primary_unit_ids": primary,
            "supplementary_unit_ids": supplementary,
            "primary_unit_count": len(primary),
        }
        if len(primary) < int(CONTRACT["heldout"]["require_primary_outer_units_at_least"]):
            result["status"] = "stop_insufficient_response_independent_primary_outer_units"
            result["reason"] = f"only {len(primary)} primary heldout half-years meet the label-free effort threshold"
            write(result)
            return 0

        result["status"] = "gate3_response_independent_temporal_split_pass"
        result["reason"] = "Chronological calibration and heldout half-year units were frozen using label-free site-week effort only; biological response remained closed"
        write(result)
        return 0
    except Exception as exc:
        result["status"] = "engineering_failure_pre_response"
        result["reason"] = f"{type(exc).__name__}: {exc}"
        write(result)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
