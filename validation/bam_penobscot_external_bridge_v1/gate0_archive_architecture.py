"""Response-blind directory-architecture Gate0 for the Penobscot BAM bridge.

This gate is allowed to fetch HTML directory indexes only. It must not download any
fish, passage, geomorphology or water-quality data file.
"""
from __future__ import annotations

from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "source_protocol_v1.json"
OUTPUT = HERE / "gate0_archive_architecture_certificate.json"

BASE = "https://apps-nefsc.fisheries.noaa.gov/prrp/Data/"
MODULE_URL = BASE + "index.php?b={module}"
USER_AGENT = "EOG-Penobscot-BAM-Bridge-Gate0/1.0"


class Gate0Stop(RuntimeError):
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


def load_protocol(path: Path = PROTOCOL) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != "frozen_before_prrp_data_file_payload_access":
        raise Gate0Stop("Penobscot source protocol is not at expected frozen boundary")
    return payload


def fetch_html(url: str) -> tuple[str, int]:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        },
        method="GET",
    )
    with urlopen(request, timeout=60) as response:
        if int(response.status) != 200:
            raise Gate0Stop(f"directory request returned HTTP {response.status}: {url}")
        body = response.read(1_000_001)
    if len(body) > 1_000_000:
        raise Gate0Stop("directory HTML exceeded 1 MB ceiling")
    try:
        return body.decode("utf-8"), len(body)
    except UnicodeDecodeError:
        return body.decode("latin-1"), len(body)


def parse_links(html: str) -> tuple[tuple[str, str], ...]:
    parser = LinkCollector()
    parser.feed(html)
    return tuple(parser.links)


def normalized_names(links: tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    names = []
    for _, text in links:
        cleaned = text.strip()
        if not cleaned or cleaned in {"Name", "../", ".. /"}:
            continue
        if cleaned.endswith("/"):
            cleaned = cleaned[:-1].strip()
        names.append(cleaned)
    return tuple(sorted(set(names)))


def evaluate_live(protocol: dict[str, Any]) -> dict[str, Any]:
    base_html, base_bytes = fetch_html(BASE)
    base_links = parse_links(base_html)
    base_names = normalized_names(base_links)

    required_modules = tuple(protocol["source"]["required_modules"])
    missing = sorted(set(required_modules).difference(base_names))
    if missing:
        raise Gate0Stop(f"required PRRP modules missing from archive index: {missing}")

    module_results: dict[str, object] = {}
    total_directory_bytes = base_bytes
    for module in required_modules:
        html, byte_count = fetch_html(MODULE_URL.format(module=module))
        total_directory_bytes += byte_count
        names = normalized_names(parse_links(html))
        module_results[module] = {
            "object_names": list(names),
            "object_count": len(names),
            "directory_html_bytes_opened": byte_count,
        }

    fish_names = set(module_results["FishCommunity"]["object_names"])
    expected_fish = str(protocol["source"]["known_response_file_from_directory_metadata"])
    if expected_fish not in fish_names:
        raise Gate0Stop(f"expected FishCommunity database missing: {expected_fish}")

    upstream_names = set(module_results["FishPassage-Upstream"]["object_names"])
    expected_upstream = str(
        protocol["source"]["known_upstream_passage_file_from_directory_metadata"]
    )
    if expected_upstream not in upstream_names:
        raise Gate0Stop(f"expected upstream passage database missing: {expected_upstream}")

    for module in ("Geomorphology", "WaterQuality", "FishPassage-System-wide"):
        if int(module_results[module]["object_count"]) < 1:
            raise Gate0Stop(f"required module {module} contains no listed objects")

    result: dict[str, Any] = {
        "schema": "eog.bam_penobscot_external_bridge.gate0_archive_architecture.v1",
        "status": "archive_architecture_ready",
        "required_modules": list(required_modules),
        "base_module_names": list(base_names),
        "module_results": module_results,
        "directory_request_count": 1 + len(required_modules),
        "directory_html_bytes_opened": total_directory_bytes,
        "data_file_requests": 0,
        "data_file_payload_bytes_opened": 0,
        "fish_response_rows_opened": 0,
        "model_fits": 0,
        "next_authorized_stage": "Gate1 documentation/schema-only inspection after Gate0 certificate is committed",
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def main() -> int:
    protocol = load_protocol()
    try:
        result = evaluate_live(protocol)
    except Exception as exc:
        result = {
            "schema": "eog.bam_penobscot_external_bridge.gate0_archive_architecture.v1",
            "status": "stop_gate0_archive_architecture",
            "reason": str(exc),
            "data_file_requests": 0,
            "data_file_payload_bytes_opened": 0,
            "fish_response_rows_opened": 0,
            "model_fits": 0,
            "retry_or_source_switch_allowed": False,
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
