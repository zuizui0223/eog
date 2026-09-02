from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from .gate1a_header import HeaderGateStop, read_first_physical_record, summarize_stage1a


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "gate1a_header_contract.json"
DEFAULT_OUTPUT = ROOT / "build" / "loomis_snowshoe_hare_endpoint3" / "stage1a_headers.json"
USER_AGENT = "EOG-Loomis-Snowshoe-Hare-Stage1A/1.0"


class StrictZenodoByteTransport:
    def __init__(self, url: str, expected_size: int, allowed_hosts: tuple[str, ...] = ("zenodo.org",)) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
            raise ValueError("URL must be HTTPS on an allowed host")
        if isinstance(expected_size, bool) or not isinstance(expected_size, int) or expected_size <= 0:
            raise ValueError("expected_size must be positive int")
        self.url = url
        self.expected_size = expected_size
        self.allowed_hosts = allowed_hosts
        self.ledger: list[dict[str, object]] = []

    def read_byte(self, offset: int, role: str) -> bytes:
        if isinstance(offset, bool) or not isinstance(offset, int) or not (0 <= offset < self.expected_size):
            raise HeaderGateStop(f"invalid byte offset {offset}")
        req = urllib.request.Request(
            self.url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/csv,text/plain;q=0.9,*/*;q=0.1",
                "Accept-Encoding": "identity",
                "Range": f"bytes={offset}-{offset}",
            },
        )
        try:
            response_context = urllib.request.urlopen(req, timeout=60)
        except (OSError, urllib.error.URLError) as exc:
            raise HeaderGateStop(f"bounded header transport unavailable: {exc}") from exc

        with response_context as response:
            status = getattr(response, "status", None) or response.getcode()
            headers = {k.lower(): v for k, v in response.headers.items()}
            final = urlparse(response.geturl())
            row: dict[str, object] = {
                "role": role,
                "offset": offset,
                "status": status,
                "content_range": headers.get("content-range"),
                "final_host": final.hostname,
                "bytes_opened": 0,
            }
            self.ledger.append(row)
            if status != 206:
                raise HeaderGateStop(f"Range returned HTTP {status}; body was not opened")
            if final.scheme != "https" or final.hostname not in self.allowed_hosts:
                raise HeaderGateStop(f"Range left allowed host set: {final.hostname!r}")
            if headers.get("content-encoding", "identity").casefold() != "identity":
                raise HeaderGateStop("Range response applied content encoding")
            match = re.fullmatch(rf"bytes {offset}-{offset}/(\d+)", headers.get("content-range", ""))
            if match is None or int(match.group(1)) != self.expected_size:
                raise HeaderGateStop("Content-Range does not preserve frozen file size")
            body = response.read(2)
            row["bytes_opened"] = len(body)
        if len(body) != 1:
            raise HeaderGateStop(f"Range response length {len(body)} != 1")
        return body


def run(contract_path: Path = DEFAULT_CONTRACT, output_path: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    evidence = []
    request_ledgers: dict[str, list[dict[str, object]]] = {}
    base: dict[str, object] = {
        "schema": "eog.loomis_snowshoe_hare_endpoint3.stage1a_live.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "contract_git_blob_binding": "stage1a_header_contract.json",
        "counts_as_predictive_evidence": False,
        "deployment_rows_opened": 0,
        "detection_header_bytes_opened": 0,
        "detection_payload_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }
    try:
        for item in contract["allowed_files"]:
            transport = StrictZenodoByteTransport(str(item["url"]), int(item["size"]))
            header = read_first_physical_record(
                str(item["key"]),
                transport.read_byte,
                maximum_header_bytes=int(contract["transport"]["maximum_header_bytes_per_file"]),
            )
            evidence.append(header)
            request_ledgers[str(item["key"])] = transport.ledger
        summary = summarize_stage1a(evidence)
        result = {
            **base,
            **summary,
            "request_ledgers": request_ledgers,
            "total_header_bytes_opened": sum(h.bytes_consumed for h in evidence),
        }
    except HeaderGateStop as exc:
        result = {
            **base,
            "status": "stop_pre_row_header_transport_or_schema",
            "reason": str(exc),
            "request_ledgers": request_ledgers,
            "next_stage": "terminal within this attempt; do not repair header transport/schema and continue as fresh",
        }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
