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
        token = str(r[cols["start_year"]]).strip()
        try:
            aux = int(token)
        except ValueError as exc:
            raise RuntimeError(f"non-integer auxiliary start_year for {r.get(cols['deployment_id'])}: {token!r}") from exc
        if aux == start.year:
            pass
        elif 0 <= aux <= 99 and aux == start.year % 100:
            r[cols["start_year"]] = str(start.year)
        else:
            raise RuntimeError(
                f"auxiliary start_year conflicts with canonical start_date year for {r.get(cols['deployment_id'])}: {aux} vs {start.year}"
            )
        normalized.append(r)
    return normalized, meta


gate.load_deployments = load_with_frozen_year_normalization

if __name__ == "__main__":
    raise SystemExit(gate.main())
