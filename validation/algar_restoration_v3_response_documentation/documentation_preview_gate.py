from __future__ import annotations

from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "documentation_contract_v1_1.json"
DEFAULT_OUTPUT = HERE / "documentation_result_v1_1.json"


class DocumentationPreviewStop(RuntimeError):
    pass


class _PreviewParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_pre = False
        self.pre_chunks: list[str] = []
        self.all_text: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        if tag.casefold() == "pre":
            self._in_pre = True

    def handle_endtag(self, tag: str):
        if tag.casefold() == "pre":
            self._in_pre = False

    def handle_data(self, data: str):
        self.all_text.append(data)
        if self._in_pre:
            self.pre_chunks.append(data)


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def fetch_preview(url: str, maximum_bytes: int) -> tuple[bytes, dict[str, object]]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html,*/*",
            "Accept-Encoding": "identity",
            "User-Agent": "EOG-WF-Algar-Documentation-Preview/1.1",
        },
    )
    try:
        response = urllib.request.urlopen(request, timeout=90)
    except urllib.error.HTTPError as exc:
        raise DocumentationPreviewStop(
            f"documentation preview GET returned HTTP {exc.code}"
        ) from exc
    except (OSError, urllib.error.URLError) as exc:
        raise DocumentationPreviewStop(
            f"documentation preview transport unavailable: {exc}"
        ) from exc

    with response:
        status = int(getattr(response, "status", response.getcode()))
        if status != 200:
            raise DocumentationPreviewStop(
                f"documentation preview GET returned HTTP {status}"
            )
        if response.headers.get("Content-Encoding", "identity").casefold() != "identity":
            raise DocumentationPreviewStop(
                "documentation preview unexpectedly used content encoding"
            )
        body = response.read(int(maximum_bytes) + 1)
        final_url = response.geturl()

    if not body:
        raise DocumentationPreviewStop("documentation preview returned empty body")
    if len(body) > int(maximum_bytes):
        raise DocumentationPreviewStop(
            "documentation preview exceeded frozen HTML byte bound"
        )
    return body, {
        "url": url,
        "final_url": final_url,
        "status": status,
        "bytes_opened": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
    }


def parse_preview_html(raw: bytes, expected_filename: str) -> tuple[str, dict[str, object]]:
    try:
        html = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DocumentationPreviewStop(
            "documentation preview HTML is not UTF-8"
        ) from exc

    parser = _PreviewParser()
    parser.feed(html)
    all_text = " ".join(chunk.strip() for chunk in parser.all_text if chunk.strip())
    if f"Preview: {expected_filename}" not in all_text:
        raise DocumentationPreviewStop(
            "documentation preview filename heading does not match frozen README"
        )

    text = "".join(parser.pre_chunks)
    if not text.strip():
        if "Preview is currently unavailable." in all_text:
            raise DocumentationPreviewStop("Dryad reports README preview unavailable")
        raise DocumentationPreviewStop("README preview contains no <pre> text")

    return text, {
        "preview_html_sha256": hashlib.sha256(raw).hexdigest(),
        "preview_html_bytes": len(raw),
        "preview_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "preview_text_characters": len(text),
        "preview_text_lines": len(text.splitlines()),
    }


def _nonempty_lines(text: str) -> list[str]:
    return [line.rstrip() for line in text.splitlines() if line.strip()]


def run(
    contract_path: Path = DEFAULT_CONTRACT,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    fetcher=fetch_preview,
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    route = contract["preview_route"]
    response = contract["candidate_response_file"]

    base = {
        "schema": "eog.algar_restoration_v3_response_documentation.result.v1_1",
        "attempt_id": contract["attempt_id"],
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "focal_taxon": contract["focal_taxon"],
        "candidate_response_file": response,
        "readme_preview_requests": 0,
        "response_csv_preview_requests": 0,
        "response_csv_payload_requests": 0,
        "response_csv_payload_bytes_opened": 0,
        "biological_response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
        "changes_closed_eog_wf_synthesis": False,
    }

    try:
        raw, request = fetcher(
            str(route["url"]),
            int(route["maximum_html_bytes"]),
        )
        base["readme_preview_requests"] = 1
        text, preview_audit = parse_preview_html(
            raw,
            str(route["expected_preview_filename"]),
        )
        lines = _nonempty_lines(text)
        filename = str(response["path"])
        mentions = [
            line for line in lines if filename.casefold() in line.casefold()
        ]

        result = {
            **base,
            "status": "readme_preview_opened_response_still_locked",
            "preview_request": request,
            "preview_audit": preview_audit,
            "documentation_text": text,
            "nonempty_line_count": len(lines),
            "candidate_response_filename_mentions": mentions,
            "response_filename_documented": bool(mentions),
            "sufficiency_rule": contract["sufficiency_rule"],
            "next_if_sufficient": contract["next_if_sufficient"],
            "next_if_insufficient": contract["next_if_insufficient"],
        }
    except (DocumentationPreviewStop, KeyError, TypeError, ValueError) as exc:
        result = {
            **base,
            "status": "stop_documentation_preview_gate",
            "reason": str(exc),
            "next_gate": "none; response CSV remains locked",
        }

    result["fingerprint"] = canonical_sha256(
        {key: value for key, value in result.items() if key != "fingerprint"}
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    result = run()
    print(
        json.dumps(
            {
                "status": result["status"],
                "response_filename_documented": result.get(
                    "response_filename_documented"
                ),
                "response_csv_payload_bytes_opened": (
                    result["response_csv_payload_bytes_opened"]
                ),
                "fingerprint": result["fingerprint"],
            },
            sort_keys=True,
        )
    )
