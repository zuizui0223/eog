from __future__ import annotations

import hashlib
import html.parser
import json
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT = HERE / "stage1a_deployment_link_contract.json"
OUTPUT = ROOT / "build/snapshot_usa_selective_promotion/stage1a_deployment_link.json"


class LinkParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str):
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href, "".join(self._text).strip()))
            self._href = None
            self._text = []


def _fp(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def main() -> int:
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    base = {
        "schema": "eog.snapshot_usa_selective_promotion.stage1a_deployment_link.v1",
        "attempt_id": c["attempt_id"],
        "landing_requests": 0,
        "deployment_payload_requests": 0,
        "sequence_payload_requests": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    try:
        req = Request(c["authorized_url"], headers={"User-Agent": "eog-response-blind-stage1a/1.0"})
        with urlopen(req, timeout=45) as response:  # noqa: S310 exact frozen public landing URL
            raw = response.read()
            final_url = response.geturl()
            status = int(getattr(response, "status", 200))
        base["landing_requests"] = 1
        if status != 200:
            raise RuntimeError(f"landing HTTP status {status}")
        parser = LinkParser()
        parser.feed(raw.decode("utf-8", errors="replace"))
        target = c["target_visible_filename"]
        candidates = []
        for href, text in parser.links:
            if text == target or target in href:
                candidates.append(urljoin(final_url, href))
        candidates = sorted(set(candidates))
        if len(candidates) != 1:
            raise RuntimeError(f"deployment link candidates={len(candidates)}; expected exactly one")
        if c["forbidden_target_filename"] in candidates[0]:
            raise RuntimeError("recovered link unexpectedly names forbidden sequence file")
        result = {
            **base,
            "status": "stage1a_deployment_link_frozen",
            "deployment_url": candidates[0],
            "landing_bytes_opened": len(raw),
            "next_gate": "freeze exact deployment URL and one-request deployment payload authorization; sequences remains closed",
        }
    except Exception as exc:
        result = {
            **base,
            "status": "stop_pre_response_deployment_link_identity_or_transport",
            "reason": str(exc),
            "next_gate": "none; do not guess or substitute a link",
        }
    result["fingerprint"] = _fp(result)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
