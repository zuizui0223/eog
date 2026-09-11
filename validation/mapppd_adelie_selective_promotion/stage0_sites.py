from __future__ import annotations

import base64
import hashlib
import json
import math
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT = HERE / "stage0_sites_contract.json"
OUTPUT = ROOT / "build/mapppd_adelie_selective_promotion/stage0_sites.json"
EARTH_RADIUS_KM = 6371.0088


def canonical_sha256(obj: object) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def quantile_linear(xs: list[float], q: float) -> float:
    vals = sorted(xs)
    if not vals:
        raise RuntimeError("no finite pairwise distances")
    pos = (len(vals) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return vals[lo]
    f = pos - lo
    return vals[lo] * (1 - f) + vals[hi] * f


def haversine(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = a
    lat2, lon2 = b
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(x))


def fetch_blob(sha: str) -> bytes:
    url = f"https://api.github.com/repos/CCheCastaldo/mapppdr/git/blobs/{sha}"
    req = Request(url, headers={"User-Agent": "eog-mapppd-sites-stage0/1.0", "Accept": "application/vnd.github+json"})
    with urlopen(req, timeout=30) as r:  # noqa: S310 - prospectively frozen public GitHub blob
        raw = r.read()
        status = int(getattr(r, "status", 200))
    if status != 200:
        raise RuntimeError(f"GitHub blob HTTP status {status}")
    obj = json.loads(raw.decode("utf-8"))
    if obj.get("sha") != sha or obj.get("encoding") != "base64":
        raise RuntimeError("sites blob identity/encoding mismatch")
    return base64.b64decode(obj["content"])


def main() -> int:
    import pyreadr

    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    base = {
        "schema": "eog.mapppd_adelie_selective_promotion.stage0_sites.result.v1",
        "attempt_id": c["attempt_id"],
        "sites_blob_gets": 0,
        "response_blob_gets": 0,
        "response_header_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    try:
        sha = c["authorized_access"]["sites_blob_sha"]
        blob = fetch_blob(sha)
        base["sites_blob_gets"] = 1
        with tempfile.NamedTemporaryFile(suffix=".rda") as fh:
            fh.write(blob)
            fh.flush()
            objects = pyreadr.read_r(fh.name)
        if len(objects) != 1:
            raise RuntimeError(f"expected one object in sites.rda, found {len(objects)}")
        df = next(iter(objects.values()))
        required = set(c["required_site_columns"])
        if not required.issubset(df.columns):
            raise RuntimeError(f"missing required site columns: {sorted(required - set(df.columns))}")
        rows = []
        for _, row in df.iterrows():
            sid = str(row["site_id"]).strip()
            try:
                lat = float(row["latitude"])
                lon = float(row["longitude"])
            except Exception:
                continue
            if not sid or not math.isfinite(lat) or not math.isfinite(lon) or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                continue
            rows.append((sid, lat, lon))
        by_site = {}
        for sid, lat, lon in rows:
            by_site.setdefault(sid, (lat, lon))
            if by_site[sid] != (lat, lon):
                raise RuntimeError(f"site coordinate conflict for {sid}")
        if len(by_site) < c["qualification"]["min_unique_valid_sites"]:
            raise RuntimeError(f"too few unique valid sites: {len(by_site)}")
        vals = list(by_site.items())
        distances = []
        for i, (_, a) in enumerate(vals):
            for _, b in vals[i + 1:]:
                d = haversine(a, b)
                if math.isfinite(d) and d > 0:
                    distances.append(d)
        thresholds = [quantile_linear(distances, float(q)) for q in c["qualification"]["distance_world_quantiles"]]
        if not (len(thresholds) == 4 and all(x > 0 for x in thresholds) and all(a < b for a, b in zip(thresholds, thresholds[1:]))):
            raise RuntimeError("distance worlds not strictly increasing positive")
        result = {
            **base,
            "status": "stage0_sites_qualified",
            "sites_blob_sha": sha,
            "sites_blob_bytes": len(blob),
            "site_rows_total": int(len(df)),
            "unique_valid_sites": len(by_site),
            "distance_thresholds_km": thresholds,
            "external_open_world": True,
            "next_gate": "freeze final response/model contract before penguin_obs access",
        }
    except Exception as exc:
        result = {
            **base,
            "status": "stop_pre_response_sites_transport_schema_or_geometry",
            "reason": str(exc),
            "next_gate": "none; no repair within this attempt",
        }
    result["fingerprint"] = canonical_sha256(result)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
