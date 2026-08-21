from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path("validation/giant_kelp_complementarity")
OUT = Path("build/giant_kelp_process_sysmeta")
UA = "eog-giant-kelp-process-sysmeta/1.1"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    contract = json.loads((ROOT / "process_object_contract.json").read_text(encoding="utf-8"))
    entity = contract["process_entity"]
    pid = entity["data_pid"]
    metadata_pid = contract["metadata_pid"]
    fetched: list[dict] = []

    def get(url: str, accept: str) -> bytes:
        if not url.startswith("https://cn.dataone.org/cn/v2/"):
            raise RuntimeError(f"non-DataONE-CN endpoint blocked: {url!r}")
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
        with urllib.request.urlopen(req, timeout=60) as response:
            body = response.read()
            status = getattr(response, "status", None) or response.getcode()
            content_type = str(response.headers.get("Content-Type", ""))
            final = str(response.geturl())
        fetched.append(
            {
                "requested": url,
                "final": final,
                "status": status,
                "bytes": len(body),
                "content_type": content_type,
                "sha256": hashlib.sha256(body).hexdigest(),
            }
        )
        return body

    def lname(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]

    encoded = urllib.parse.quote(pid, safe="")
    meta_bytes = get(f"https://cn.dataone.org/cn/v2/meta/{encoded}", "application/xml,text/xml,*/*")
    sysroot = ET.fromstring(meta_bytes)

    def first_text(root: ET.Element, name: str) -> str:
        for node in root.iter():
            if lname(node.tag) == name:
                return " ".join("".join(node.itertext()).split())
        return ""

    identifier = first_text(sysroot, "identifier")
    format_id = first_text(sysroot, "formatId")
    size_text = first_text(sysroot, "size")
    checksum_node = next((n for n in sysroot.iter() if lname(n.tag) == "checksum"), None)
    checksum = " ".join("".join(checksum_node.itertext()).split()) if checksum_node is not None else ""
    checksum_algorithm = str(checksum_node.attrib.get("algorithm", "")) if checksum_node is not None else ""
    if identifier != pid:
        raise RuntimeError(f"process sysmeta identifier mismatch: {identifier!r}")
    if not size_text.isdigit() or int(size_text) <= 0:
        raise RuntimeError(f"invalid process size: {size_text!r}")
    if not checksum or not checksum_algorithm:
        raise RuntimeError("process sysmeta lacks checksum")

    checksum_bytes = get(
        f"https://cn.dataone.org/cn/v2/checksum/{encoded}",
        "application/xml,text/xml,*/*",
    )
    checksum_root = ET.fromstring(checksum_bytes)
    checksum_api = " ".join("".join(checksum_root.itertext()).split())
    checksum_api_algorithm = str(checksum_root.attrib.get("algorithm", ""))
    if checksum_api != checksum or checksum_api_algorithm.casefold() != checksum_algorithm.casefold():
        raise RuntimeError("process checksum disagreement")

    eml_encoded = urllib.parse.quote(metadata_pid, safe="")
    eml_bytes = get(
        f"https://cn.dataone.org/cn/v2/object/{eml_encoded}",
        "application/xml,text/xml,*/*",
    )
    if hashlib.sha256(eml_bytes).hexdigest() != contract["metadata_sha256"]:
        raise RuntimeError("process EML identity drift")
    eml = ET.fromstring(eml_bytes)

    def desc(node: ET.Element, target: str) -> str:
        for child in node.iter():
            if lname(child.tag) == target:
                return " ".join("".join(child.itertext()).split())
        return ""

    eml_to_physical = entity.get("eml_to_physical_header_mapping", {})
    required = set(entity["required_columns"])
    domains: dict[str, dict] = {}
    for attr in eml.iter():
        if lname(attr.tag) != "attribute":
            continue
        eml_name = desc(attr, "attributeName")
        physical_name = eml_to_physical.get(eml_name, eml_name)
        if physical_name not in required:
            continue
        missing = []
        for missing_node in attr.iter():
            if lname(missing_node.tag) == "missingValueCode":
                code = desc(missing_node, "code") or " ".join("".join(missing_node.itertext()).split())
                if code:
                    missing.append(code)
        enumerated = []
        for code_def in attr.iter():
            if lname(code_def.tag) == "codeDefinition":
                code = desc(code_def, "code")
                definition = desc(code_def, "definition")
                if code:
                    enumerated.append({"code": code, "definition": definition})
        domains[physical_name] = {
            "eml_attribute_name": eml_name,
            "missing_value_codes": sorted(set(missing)),
            "enumerated_codes": enumerated,
            "numeric_type": desc(attr, "numberType") or desc(attr, "storageType"),
            "definition": desc(attr, "attributeDefinition"),
            "unit": desc(attr, "standardUnit") or desc(attr, "customUnit"),
        }
    if set(domains) != required:
        raise RuntimeError(f"process EML domain coverage mismatch: {sorted(domains)} != {sorted(required)}")

    payload = {
        "status": "process_system_metadata_frozen",
        "candidate": contract["candidate"],
        "data_pid": pid,
        "object_name": entity["object_name"],
        "identifier": identifier,
        "format_id": format_id,
        "size_bytes": int(size_text),
        "checksum": checksum,
        "checksum_algorithm": checksum_algorithm,
        "system_metadata_sha256": hashlib.sha256(meta_bytes).hexdigest(),
        "metadata_sha256": hashlib.sha256(eml_bytes).hexdigest(),
        "eml_to_physical_header_mapping": eml_to_physical,
        "field_domains": domains,
        "parser_semantics": contract["parser_semantics"],
        "patch_mapping_gate": contract["patch_mapping_gate"],
        "process_feature_boundary": contract["process_feature_boundary"],
        "process_object_bytes_opened": contract["response_access_state"]["process_object_bytes_opened"],
        "response_package_bytes_opened": False,
        "response_rows_opened": False,
        "network_fetches": fetched,
        "next": "audit the frozen process rows against the frozen geometry universe; never open response to repair process metadata",
    }
    payload["fingerprint"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    (OUT / "process_sysmeta_result.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
