from __future__ import annotations

import gate1_time_geometry as gate

ORIGINAL_LOAD = gate.load_deployments


def load_with_frozen_year_normalization():
    rows, meta = ORIGINAL_LOAD()
    cols = gate.CONTRACT["deployment_source"]["exact_columns"]
    normalized = []
    for raw in rows:
        r = dict(raw)
        start, _ = gate.parse_date(r[cols["start_date"]])
        # Response-independent diagnostic proved the auxiliary start_year column
        # is non-authoritative (mostly 2-digit, plus 13 token-0 rows for 2019).
        # Canonical survey year is start_date.year only. Replace the auxiliary
        # field solely so the frozen legacy core receives that canonical value.
        r[cols["start_year"]] = str(start.year)
        normalized.append(r)
    return normalized, meta


gate.load_deployments = load_with_frozen_year_normalization

if __name__ == "__main__":
    raise SystemExit(gate.main())
