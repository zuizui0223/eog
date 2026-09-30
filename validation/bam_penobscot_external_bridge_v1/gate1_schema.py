"""Gate1 schema-only inspector for the Penobscot real-system BAM bridge.

Execution is unauthorized unless a committed Gate0 PASS certificate matches the frozen
Gate1 contract.  This module is intentionally incapable of exporting data rows.

Supported schema-only paths:
- Access .accdb/.mdb: table names and field schema via mdbtools;
- CSV/TSV: first physical header line only;
- Excel .xlsx: workbook sheet names and first row only via Python stdlib ZIP/XML parsing;
- legacy .xls: terminal STOP unless a separately frozen parser exists.

The runner must never use focal fish values to choose files, columns, or worlds.
"""
from __future__ import annotations

import csv
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
import zipfile


HERE = Path(__file__).resolve().parent
GATE0 = HERE / "gate0_archive_architecture_certificate.json"
CONTRACT = HERE / "gate1_schema_contract_draft.json"
OUTPUT = HERE / "gate1_schema_certificate.json"

BASE = "https://apps-nefsc.fisheries.noaa.gov/prrp/Data/"
USER_AGENT = "EOG-Penobscot-BAM-Bridge-Gate1/1.0"
MAX_FILE_BYTES = 50_000_000
MAX_HEADER_BYTES = 8192

DATA_EXTENSIONS = {".accdb", ".mdb", ".csv", ".tsv", ".xlsx", ".xls"}
IGNORE_EXTENSIONS = {".pdf", ".log", ".txt", ".doc", ".docx", ".jpg", ".jpeg", ".png"}


class Gate1Stop(RuntimeError):
    pass


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href, "".join(self._text).strip()))
            self._href = None
            self._text = []


def canonical_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def load_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    if not GATE0.exists():
        raise Gate1Stop("Gate0 certificate is not committed")
    gate0 = json.loads(GATE0.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if gate0.get("status") != "archive_architecture_ready":
        raise Gate1Stop("Gate0 is not PASS")
    if contract.get("status") != "authorized_after_gate0_pass":
        raise Gate1Stop("Gate1 contract is not authorized")
    expected = contract["gate0_prerequisite"]["fingerprint"]
    if not expected or expected != gate0.get("fingerprint"):
        raise Gate1Stop("Gate0 fingerprint does not match Gate1 authorization")
    return gate0, contract


def fetch_bytes(url: str, *, ceiling: int = MAX_FILE_BYTES) -> bytes:
    req = Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
        method="GET",
    )
    with urlopen(req, timeout=90) as response:
        if int(response.status) != 200:
            raise Gate1Stop(f"GET {url} returned HTTP {response.status}")
        body = response.read(ceiling + 1)
    if len(body) > ceiling:
        raise Gate1Stop(f"file exceeds frozen byte ceiling: {url}")
    return body


def fetch_html(url: str) -> str:
    body = fetch_bytes(url, ceiling=1_000_000)
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError:
        return body.decode("latin-1")


def links_from_html(html: str, base_url: str) -> tuple[tuple[str, str], ...]:
    parser = LinkCollector()
    parser.feed(html)
    rows = []
    for href, text in parser.links:
        name = text.strip().rstrip("/").strip()
        if not href or not name or name in {"Name", ".."}:
            continue
        rows.append((urljoin(base_url, href), name))
    return tuple(rows)


def file_extension(name: str) -> str:
    return Path(name).suffix.lower()


def select_schema_files(
    module: str,
    links: tuple[tuple[str, str], ...],
    contract: dict[str, Any],
) -> tuple[tuple[str, str], ...]:
    rules = contract["file_selection_rules"][module]
    exact = rules.get("required_exact_file")
    if exact:
        matches = tuple(row for row in links if row[1] == exact)
        if len(matches) != 1:
            raise Gate1Stop(
                f"{module}: required exact file {exact!r} count={len(matches)}"
            )
        return matches

    selected = []
    unsupported_data_like = []
    for url, name in links:
        ext = file_extension(name)
        if ext in DATA_EXTENSIONS:
            selected.append((url, name))
        elif ext in IGNORE_EXTENSIONS or not ext:
            continue
        else:
            unsupported_data_like.append(name)

    if unsupported_data_like:
        raise Gate1Stop(
            f"{module}: unsupported archive object types: {sorted(unsupported_data_like)}"
        )
    if not selected:
        raise Gate1Stop(f"{module}: no schema-inspectable data files listed")
    return tuple(sorted(selected, key=lambda row: row[1]))


def inspect_delimited_header(body: bytes, *, delimiter: str) -> dict[str, Any]:
    if len(body) > MAX_HEADER_BYTES:
        first_newline = body.find(b"\n", 0, MAX_HEADER_BYTES)
    else:
        first_newline = body.find(b"\n")
    if first_newline < 0:
        raise Gate1Stop("delimited header exceeds frozen byte ceiling")
    header_bytes = body[: first_newline + 1]
    if header_bytes.endswith(b"\r\n"):
        raw = header_bytes[:-2]
        terminator = "CRLF"
    else:
        raw = header_bytes[:-1]
        terminator = "LF"
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise Gate1Stop("delimited header is not UTF-8") from exc
    rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    if len(rows) != 1 or not rows[0]:
        raise Gate1Stop("delimited header did not parse as exactly one row")
    columns = rows[0]
    if any(not str(value).strip() for value in columns):
        raise Gate1Stop("delimited header contains empty column name")
    if len(set(columns)) != len(columns):
        raise Gate1Stop("delimited header contains duplicate column names")
    return {
        "columns": columns,
        "header_bytes_opened": len(header_bytes),
        "line_terminator": terminator,
        "data_row_bytes_interpreted": 0,
    }


def inspect_xlsx_schema(body: bytes) -> dict[str, Any]:
    """Read workbook metadata + row 1 only; do not parse any later worksheet row."""

    try:
        zf = zipfile.ZipFile(io.BytesIO(body))
    except zipfile.BadZipFile as exc:
        raise Gate1Stop("xlsx is not a valid ZIP container") from exc

    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_by_id = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels
    }
    ns = {
        "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }

    shared_strings: list[str] = []
    if "xl/sharedStrings.xml" in zf.namelist():
        root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
        for si in root.findall("m:si", ns):
            text = "".join(node.text or "" for node in si.findall(".//m:t", ns))
            shared_strings.append(text)

    sheet_rows = []
    for sheet in workbook.findall("m:sheets/m:sheet", ns):
        name = sheet.attrib["name"]
        rel_id = sheet.attrib[f"{{{ns['r']}}}id"]
        target = rel_by_id.get(rel_id)
        if not target:
            raise Gate1Stop(f"xlsx sheet {name!r} has no relationship target")
        path = target.lstrip("/")
        if not path.startswith("xl/"):
            path = "xl/" + path
        root = ET.fromstring(zf.read(path))
        row1 = root.find(".//m:sheetData/m:row[@r='1']", ns)
        columns = []
        if row1 is not None:
            for cell in row1.findall("m:c", ns):
                cell_type = cell.attrib.get("t")
                value_node = cell.find("m:v", ns)
                inline = cell.find("m:is/m:t", ns)
                value = ""
                if inline is not None:
                    value = inline.text or ""
                elif value_node is not None:
                    raw = value_node.text or ""
                    if cell_type == "s":
                        try:
                            value = shared_strings[int(raw)]
                        except (ValueError, IndexError) as exc:
                            raise Gate1Stop(
                                f"xlsx invalid shared-string index in {name!r}"
                            ) from exc
                    else:
                        value = raw
                columns.append(value)
        sheet_rows.append({"sheet": name, "row1_values": columns})

    return {
        "sheets": sheet_rows,
        "later_rows_interpreted": 0,
    }


def _run_checked(command: list[str]) -> str:
    proc = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise Gate1Stop(
            f"schema command failed {command[0]}: {proc.stderr.strip()[:500]}"
        )
    return proc.stdout


def inspect_access_schema(body: bytes, suffix: str) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as handle:
        handle.write(body)
        handle.flush()
        tables_text = _run_checked(["mdb-tables", "-1", handle.name])
        tables = tuple(
            sorted(
                line.strip()
                for line in tables_text.splitlines()
                if line.strip() and not line.startswith("MSys")
            )
        )
        if not tables:
            raise Gate1Stop("Access database exposes no user tables")

        schemas = {}
        for table in tables:
            schema = _run_checked(["mdb-schema", handle.name, "-T", table])
            # Retain DDL only. mdb-schema does not export table rows.
            schemas[table] = schema.strip()
        return {
            "tables": list(tables),
            "ddl_by_table": schemas,
            "data_rows_exported": 0,
        }


def inspect_file(name: str, body: bytes) -> dict[str, Any]:
    ext = file_extension(name)
    if ext == ".csv":
        schema = inspect_delimited_header(body, delimiter=",")
    elif ext == ".tsv":
        schema = inspect_delimited_header(body, delimiter="\t")
    elif ext == ".xlsx":
        schema = inspect_xlsx_schema(body)
    elif ext in {".accdb", ".mdb"}:
        schema = inspect_access_schema(body, ext)
    elif ext == ".xls":
        raise Gate1Stop("legacy .xls is unsupported by the frozen Gate1 parser")
    else:
        raise Gate1Stop(f"unsupported Gate1 file type: {name}")
    return {
        "name": name,
        "extension": ext,
        "size_bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "schema": schema,
    }


def evaluate_live() -> dict[str, Any]:
    gate0, contract = load_inputs()

    selected: dict[str, list[dict[str, Any]]] = {}
    total_file_bytes = 0
    total_file_requests = 0

    for module in contract["file_selection_rules"]:
        module_url = BASE + f"index.php?b={quote(module)}"
        links = links_from_html(fetch_html(module_url), module_url)
        files = select_schema_files(module, links, contract)
        module_rows = []
        for url, name in files:
            body = fetch_bytes(url)
            total_file_requests += 1
            total_file_bytes += len(body)
            module_rows.append(inspect_file(name, body))
        selected[module] = module_rows

    # Schema-only pass conditions.  Do not inspect fish data values.
    fish = selected["FishCommunity"][0]
    fish_text = json.dumps(fish["schema"], sort_keys=True).lower()
    if not any(token in fish_text for token in ("year", "date", "sample")):
        raise Gate1Stop("FishCommunity schema exposes no obvious time field")
    if not any(token in fish_text for token in ("species", "taxon", "common", "scientific")):
        raise Gate1Stop("FishCommunity schema exposes no obvious taxon identity field")

    physical_text = json.dumps(
        selected["Geomorphology"] + selected["WaterQuality"],
        sort_keys=True,
    ).lower()
    if not any(token in physical_text for token in ("site", "reach", "station", "location")):
        raise Gate1Stop("A modules expose no obvious spatial linkage field")

    result: dict[str, Any] = {
        "schema": "eog.bam_penobscot_external_bridge.gate1_schema.v1",
        "status": "schema_ready",
        "gate0_fingerprint": gate0["fingerprint"],
        "selected_files": selected,
        "data_file_requests": total_file_requests,
        "data_file_bytes_opened_for_schema": total_file_bytes,
        "fish_response_rows_exported": 0,
        "fish_response_rows_interpreted": 0,
        "model_fits": 0,
        "next_authorized_stage": "freeze exact column bindings and world constructors before any focal fish response row is read",
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def main() -> int:
    try:
        result = evaluate_live()
    except Exception as exc:
        result = {
            "schema": "eog.bam_penobscot_external_bridge.gate1_schema.v1",
            "status": "stop_gate1_schema_or_transport",
            "reason": str(exc),
            "fish_response_rows_exported": 0,
            "fish_response_rows_interpreted": 0,
            "model_fits": 0,
            "retry_or_parser_repair_allowed": False,
        }
        result["fingerprint"] = canonical_sha256(result)
    OUTPUT.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
