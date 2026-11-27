"""Audit only the public braid polyline ZIP, not biological response or connectivity."""
import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import re
import stat
from urllib.request import HTTPRedirectHandler, Request, build_opener
import zipfile

HERE = Path(__file__).resolve().parent
URL = "https://www.sciencebase.gov/catalog/file/get/67102a7ad34edd269209626c?name=Elwha_River_braids_2006_to_2022.zip"
MAX_BYTES = 33554432
MAX_UNCOMPRESSED = 134217728
MAX_ENTRIES = 500
NAME = re.compile(r"Elwha_braids_(\d{8})_((?:LR|MR|CR)(?:_(?:LR|MR|CR))*)", re.I)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def audit_zip(raw):
    import shapefile
    from pyproj import CRS

    if len(raw) > MAX_BYTES:
        raise ValueError("compressed size exceeds cap")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos = z.infolist()
        if (len(infos) > MAX_ENTRIES
                or sum(i.file_size for i in infos) > MAX_UNCOMPRESSED
                or len({i.filename.casefold() for i in infos}) != len(infos)):
            raise ValueError("archive resource cap or duplicate member")
        for i in infos:
            p = PurePosixPath(i.filename)
            if (p.is_absolute() or ".." in p.parts or "\\" in i.filename
                    or stat.S_ISLNK(i.external_attr >> 16) or i.flag_bits & 1):
                raise ValueError("unsafe or encrypted ZIP member")
        if z.testzip() is not None:
            raise ValueError("CRC check failed")
        members = {i.filename.casefold(): i.filename for i in infos if not i.is_dir()}
        shapes = sorted(n for n in members if n.endswith(".shp"))
        if not shapes:
            raise ValueError("no polyline shapefiles")
        dates = set()
        rows = []
        target_crs = CRS.from_epsg(6339)
        for shp in shapes:
            stem = shp[:-4]
            match = NAME.fullmatch(PurePosixPath(stem).name)
            if not match:
                raise ValueError("unexpected shapefile naming")
            date, labels = match.group(1), match.group(2).upper().split("_")
            datetime.strptime(date, "%Y%m%d")
            if date in dates or len(set(labels)) != len(labels):
                raise ValueError("duplicate date or reach label")
            dates.add(date)
            def member(ext):
                key = stem + ext
                if key not in members:
                    raise ValueError("missing mandatory shapefile component")
                return z.read(members[key])
            crs = CRS.from_wkt(member(".prj").decode("utf-8-sig").strip())
            if not crs.equals(target_crs, ignore_axis_order=True):
                raise ValueError("unverified NAD83(2011) UTM10N")
            with shapefile.Reader(shp=io.BytesIO(member(".shp")),
                                  shx=io.BytesIO(member(".shx")),
                                  dbf=io.BytesIO(member(".dbf"))) as reader:
                if reader.shapeType != shapefile.POLYLINE:
                    raise ValueError("unexpected shape type")
                fields = {f[0].casefold(): f[0] for f in reader.fields[1:]}
                if not {"riverreach", "length_m"} <= fields.keys():
                    raise ValueError("missing expected attributes")
                stats = defaultdict(list)
                observed_count = 0
                for sr in reader.iterShapeRecords():
                    observed_count += 1
                    d = {k.casefold(): v for k, v in sr.record.as_dict().items()}
                    section = d["riverreach"]
                    length = d["length_m"]
                    points = sr.shape.points
                    if (section not in labels or type(length) not in (int, float)
                            or not math.isfinite(length) or length <= 0
                            or sr.shape.shapeType != shapefile.POLYLINE
                            or not points or not all(math.isfinite(x) for p in points for x in p)):
                        raise ValueError("invalid feature or attribute")
                    stats[section].append(float(length))
                if observed_count != len(reader) or set(stats) != set(labels):
                    raise ValueError("record/filename coverage mismatch")
                for section in sorted(stats):
                    rows.append({"date": date, "section": section,
                                 "features": len(stats[section]),
                                 "sum_provider_polyline_length_m": math.fsum(stats[section])})
        return {"status": "GEOMETRY_SCHEMA_INSPECTED_PENDING_METADATA_CROSSWALK",
                "sha256": hashlib.sha256(raw).hexdigest(), "zip_bytes": len(raw),
                "publisher_checksum_verified": False, "crs_epsg": 6339,
                "shapefile_count": len(shapes), "date_count": len(dates),
                "actual_date_labels": sorted(dates), "date_section_summaries": rows,
                "topology_verified": False, "survey_crosswalk_verified": False,
                "historical_fish_passability_verified": False}


def self_test():
    import shapefile
    from pyproj import CRS

    shp, shx, dbf = io.BytesIO(), io.BytesIO(), io.BytesIO()
    with shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=shapefile.POLYLINE) as w:
        w.field("RiverReach", "C", size=3)
        w.field("Length_m", "N", size=12, decimal=2)
        w.line([[(500000, 5300000), (500010, 5300000)]])
        w.record("LR", 10.0)
    archive = io.BytesIO()
    stem = "Elwha_braids_20130213_LR"
    with zipfile.ZipFile(archive, "w") as z:
        for ext, buf in ((".shp", shp), (".shx", shx), (".dbf", dbf)):
            z.writestr(stem + ext, buf.getvalue())
        z.writestr(stem + ".prj", CRS.from_epsg(6339).to_wkt())
    r = audit_zip(archive.getvalue())
    assert r["date_section_summaries"] == [
        {"date": "20130213", "section": "LR", "features": 1,
         "sum_provider_polyline_length_m": 10.0}]
    assert not r["topology_verified"] and not r["publisher_checksum_verified"]
    unsafe = io.BytesIO()
    with zipfile.ZipFile(unsafe, "w") as z:
        z.writestr("../evil.shp", b"")
    try:
        audit_zip(unsafe.getvalue())
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe member accepted")
    print("Offline braid geometry fixtures passed.")


def run():
    p = json.loads((HERE / "historical_braids_protocol.json").read_text(encoding="utf-8"))
    a = p["access"]
    if (p["status"] != "FROZEN_BEFORE_ARCHIVE_ACCESS" or p["archive_url"] != URL
            or a["max_ci_attempts_if_local_network_unavailable"] != 1
            or a["max_download_bytes"] != MAX_BYTES or a["max_uncompressed_bytes"] != MAX_UNCOMPRESSED
            or a["max_entries"] != MAX_ENTRIES or a["timeout_seconds"] != 30):
        raise ValueError("frozen access contract mismatch")
    r = {"source_url": URL, "request_attempts": 1,
         "fish_response_files_opened": 0, "fish_response_rows_parsed": 0,
         "ecological_scores": 0}
    try:
        req = Request(URL, headers={"User-Agent": "EOG-public-geometry-audit/1.0"})
        with build_opener(NoRedirect()).open(req, timeout=30) as resp:
            r["http_status"] = resp.status
            if resp.geturl() != URL:
                raise ValueError("unexpected endpoint")
            raw = resp.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("compressed size exceeds cap")
        r.update({"zip_bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        r.update(audit_zip(raw))
        expected = set(p["metadata_dates_verbatim"])
        actual = set(r["actual_date_labels"])
        r["metadata_only_date_labels"] = sorted(expected - actual)
        r["archive_only_date_labels"] = sorted(actual - expected)
        r["metadata_crosswalk_verified"] = False
    except Exception as exc:
        r.update({"status": "HOLD_BRAIDS_ARCHIVE_OR_SCHEMA_FAILED",
                  "error_type": type(exc).__name__, "http_error_code": getattr(exc, "code", None),
                  "diagnostic": str(exc)[:240]})
    return r


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        if args.output is None:
            parser.error("--output required")
        result = run()
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(result["status"])
