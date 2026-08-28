from __future__ import annotations

import hashlib
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "andrews_we008_red_backed_vole_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "gate0_metadata_only.json"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fingerprint(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def get_bytes(url: str, accept: str):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 EOG-WE008-metadata-only/1.0",
            "Accept": accept,
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return raw, r.geturl(), r.headers.get("Content-Type")


def head_only(url: str):
    req = urllib.request.Request(
        url,
        method="HEAD",
        headers={
            "User-Agent": "Mozilla/5.0 EOG-WE008-metadata-only/1.0",
            "Accept": "text/plain,text/csv,application/octet-stream,*/*;q=0.1",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return {
            "status": int(r.status),
            "final_url": r.geturl(),
            "content_type": r.headers.get("Content-Type"),
            "content_length": r.headers.get("Content-Length"),
            "content_disposition": r.headers.get("Content-Disposition"),
            "body_bytes_opened": 0,
        }


class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current_href = None
        self.current_text = []
        self.anchors = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self.current_href = dict(attrs).get("href")
            self.current_text = []

    def handle_data(self, data):
        if self.current_href is not None:
            self.current_text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self.current_href is not None:
            self.anchors.append({
                "href": self.current_href,
                "text": " ".join("".join(self.current_text).split()),
            })
            self.current_href = None
            self.current_text = []


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def descendants_text(node, name):
    return [
        (x.text or "").strip()
        for x in node.iter()
        if local_name(x.tag) == name and (x.text or "").strip()
    ]


def parse_tables(xml_raw: bytes):
    root = ET.fromstring(xml_raw)
    tables = [x for x in root.iter() if local_name(x.tag) == "dataTable"]
    out = []
    for ordinal, table in enumerate(tables, start=1):
        entity_names = descendants_text(table, "entityName")
        entity_descriptions = descendants_text(table, "entityDescription")
        object_names = descendants_text(table, "objectName")
        urls = descendants_text(table, "url")
        attrs = []
        for attr in table.iter():
            if local_name(attr.tag) != "attribute":
                continue
            names = descendants_text(attr, "attributeName")
            defs = descendants_text(attr, "attributeDefinition")
            attrs.append({
                "name": names[0] if names else None,
                "definition": defs[0] if defs else None,
            })
        out.append({
            "ordinal": ordinal,
            "entity_name": entity_names[0] if entity_names else None,
            "entity_descriptions": entity_descriptions,
            "object_names": object_names,
            "online_urls": urls,
            "attribute_names": [a["name"] for a in attrs if a["name"]],
            "attributes": attrs,
        })
    return out


def normalized_tokens(values):
    toks = set()
    for value in values:
        text = str(value or "").lower()
        token = ""
        for c in text:
            if c.isalnum():
                token += c
            else:
                if token:
                    toks.add(token)
                    token = ""
        if token:
            toks.add(token)
    return toks


def select_entity(tables, spec):
    ordinal = int(spec["ordinal"])
    matches = [t for t in tables if t["ordinal"] == ordinal]
    if len(matches) != 1:
        raise RuntimeError(f"entity ordinal {ordinal} not uniquely present")
    table = matches[0]
    wanted = spec["entity_name_contains"].lower()
    observed_fields = [table.get("entity_name"), *table.get("entity_descriptions", [])]
    observed = [str(value or "").lower() for value in observed_fields]
    if not any(wanted in value for value in observed):
        raise RuntimeError(
            f"entity {ordinal} name mismatch: expected substring {spec['entity_name_contains']!r}, "
            f"observed entityName={table.get('entity_name')!r}, "
            f"entityDescription={table.get('entity_descriptions', [])!r}"
        )
    return table


def one_public_data_url(table):
    urls = [u for u in table["online_urls"] if u.startswith(("http://", "https://"))]
    urls = list(dict.fromkeys(urls))
    if len(urls) != 1:
        raise RuntimeError(
            f"entity {table['ordinal']} does not expose exactly one public online URL: {urls}"
        )
    return urls[0]


def write(result):
    result["fingerprint"] = fingerprint({k: v for k, v in result.items() if k != "fingerprint"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


def main():
    firewall = dict(CONTRACT["response_firewall"])
    result = {
        "schema": "eog.andrews_we008_red_backed_vole_replication_2.gate0_metadata_only.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "landing": {},
        "eml": {},
        "entities": {},
        "head_checks": {},
        "response_firewall": firewall,
    }
    try:
        landing_url = CONTRACT["source"]["landing_url"]
        landing_raw, landing_final, landing_type = get_bytes(landing_url, "text/html,*/*;q=0.1")
        parser = AnchorParser()
        parser.feed(landing_raw.decode("utf-8", errors="replace"))
        eml_candidates = []
        for a in parser.anchors:
            href = urllib.parse.urljoin(landing_final, a["href"])
            hay = (a["text"] + " " + href).lower()
            if "eml" in hay or "ecological metadata language" in hay:
                eml_candidates.append(href)
        eml_candidates = list(dict.fromkeys(eml_candidates))
        if len(eml_candidates) != 1:
            raise RuntimeError(f"landing did not expose exactly one EML link: {eml_candidates}")
        eml_url = eml_candidates[0]
        eml_raw, eml_final, eml_type = get_bytes(eml_url, "application/xml,text/xml,*/*;q=0.1")
        tables = parse_tables(eml_raw)
        if len(tables) < 12:
            raise RuntimeError(f"EML exposed only {len(tables)} dataTable entities; expected >=12")

        roles = CONTRACT["entity_roles"]
        response = select_entity(tables, roles["forbidden_response"])
        effort = select_entity(tables, roles["response_independent_effort"])
        geometry = select_entity(tables, roles["response_independent_geometry"])
        context = select_entity(tables, roles["response_independent_context"])

        response_url = one_public_data_url(response)
        effort_url = one_public_data_url(effort)
        geometry_url = one_public_data_url(geometry)
        context_url = one_public_data_url(context)
        urls = [response_url, effort_url, geometry_url]
        objects = [
            tuple(response["object_names"]),
            tuple(effort["object_names"]),
            tuple(geometry["object_names"]),
        ]
        if len(set(urls)) != 3 or len(set(objects)) != 3:
            raise RuntimeError("response / effort / geometry physical objects are not distinct")

        effort_tokens = normalized_tokens(effort["attribute_names"])
        geometry_tokens = normalized_tokens(geometry["attribute_names"])
        if not effort_tokens.intersection(set(CONTRACT["gate0"]["require_effort_schema_tokens_any"])):
            raise RuntimeError(f"effort schema lacks required linkage tokens: {sorted(effort_tokens)}")
        if not geometry_tokens.intersection(set(CONTRACT["gate0"]["require_geometry_schema_tokens_any"])):
            raise RuntimeError(f"geometry schema lacks required linkage/coordinate tokens: {sorted(geometry_tokens)}")

        # HEAD only the response-independent effort and geometry entities. Do not HEAD/GET captures.
        effort_head = head_only(effort_url)
        geometry_head = head_only(geometry_url)
        if effort_head["status"] < 200 or effort_head["status"] >= 400:
            raise RuntimeError(f"effort HEAD failed: {effort_head}")
        if geometry_head["status"] < 200 or geometry_head["status"] >= 400:
            raise RuntimeError(f"geometry HEAD failed: {geometry_head}")

        result["landing"] = {
            "url": landing_url,
            "final_url": landing_final,
            "content_type": landing_type,
            "bytes": len(landing_raw),
            "sha256": hashlib.sha256(landing_raw).hexdigest(),
            "eml_url": eml_url,
        }
        result["eml"] = {
            "url": eml_url,
            "final_url": eml_final,
            "content_type": eml_type,
            "bytes": len(eml_raw),
            "sha256": hashlib.sha256(eml_raw).hexdigest(),
            "data_table_count": len(tables),
            "entity_inventory": [
                {
                    "ordinal": t["ordinal"],
                    "entity_name": t["entity_name"],
                    "entity_descriptions": t["entity_descriptions"],
                    "object_names": t["object_names"],
                    "attribute_names": t["attribute_names"],
                    "online_url_count": len(t["online_urls"]),
                }
                for t in tables
            ],
        }
        for role, table, url in (
            ("forbidden_response", response, response_url),
            ("response_independent_effort", effort, effort_url),
            ("response_independent_geometry", geometry, geometry_url),
            ("response_independent_context", context, context_url),
        ):
            result["entities"][role] = {
                "ordinal": table["ordinal"],
                "entity_name": table["entity_name"],
                "entity_descriptions": table["entity_descriptions"],
                "object_names": table["object_names"],
                "attribute_names": table["attribute_names"],
                "public_data_url": url,
            }
        result["head_checks"] = {
            "response_independent_effort": effort_head,
            "response_independent_geometry": geometry_head,
            "forbidden_response_head_requests": 0,
        }
        result["status"] = "gate0_pass_metadata_only_physical_separation_and_transport"
        result["reason"] = (
            "WE008 EML uniquely separated capture response, trap-status effort, and transect-endpoint geometry; "
            "anonymous HEAD succeeded only for response-independent effort/geometry; capture data remained unopened"
        )
        write(result)
        return 0
    except Exception as exc:
        result["status"] = "engineering_failure_pre_response"
        result["reason"] = f"{type(exc).__name__}: {exc}"
        write(result)
        return 1


if __name__ == "__main__":
    sys.exit(main())
