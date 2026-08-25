from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "fukushima_wild_boar_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "transport_diag.json"


class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms = []
        self.links = []
        self._form = None

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "form":
            self._form = {"action": d.get("action"), "method": d.get("method", "get").lower(), "inputs": []}
            self.forms.append(self._form)
        elif tag == "input" and self._form is not None:
            # Password-like/user-entered fields are retained only by type/name; values are omitted.
            typ = d.get("type", "text").lower()
            item = {"type": typ, "name": d.get("name")}
            if typ in {"hidden", "submit", "checkbox", "radio"}:
                item["value"] = d.get("value")
            self._form["inputs"].append(item)
        elif tag == "a" and d.get("href"):
            self.links.append(d["href"])

    def handle_endtag(self, tag):
        if tag == "form":
            self._form = None


def get_html(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 EOG-response-free-transport-diagnostic/1.0", "Accept": "text/html,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return raw.decode("utf-8", errors="replace"), len(raw), r.geturl(), r.headers.get("Content-Type")


def safe_url_summary(value, base):
    if not value:
        return None
    u = urllib.parse.urljoin(base, value)
    p = urllib.parse.urlparse(u)
    q = urllib.parse.parse_qs(p.query, keep_blank_values=True)
    # Preserve only routing keys, never cookies/tokens.
    safe_q = {k: v for k, v in q.items() if k.lower() in {"data_id", "docid", "docname", "lang", "action", "qformat"}}
    return {"scheme": p.scheme, "host": p.netloc, "path": p.path, "query": safe_q}


def main():
    result = {
        "schema": "eog.fukushima_wild_boar_replication_2.transport_diag.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "files": {},
        "response_firewall": dict(CONTRACT["response_firewall"]),
    }
    try:
        for role in ("occasion", "evacuation"):
            spec = CONTRACT["response_independent_files"][role]
            qs = urllib.parse.urlencode({"data_id": spec["data_id"], "docname": spec["filename"], "lang": "en"})
            url = f"https://db.cger.nies.go.jp/JaLTER/script/licence.php?{qs}"
            html, n, final_url, ctype = get_html(url)
            parser = Parser()
            parser.feed(html)
            result["files"][role] = {
                "data_id": spec["data_id"],
                "filename": spec["filename"],
                "license_page_bytes": n,
                "content_type": ctype,
                "final_url": safe_url_summary(final_url, url),
                "forms": [
                    {
                        "action": safe_url_summary(f.get("action"), final_url),
                        "method": f.get("method"),
                        "inputs": f.get("inputs"),
                    }
                    for f in parser.forms
                ],
                "links": [safe_url_summary(h, final_url) for h in parser.links[:50]],
            }
        result["status"] = "transport_form_diagnostic_complete_response_still_closed"
        result["reason"] = "Only public license-page HTML for occasion/evacuation was inspected; no dataset file payload and no detection endpoint was requested"
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
