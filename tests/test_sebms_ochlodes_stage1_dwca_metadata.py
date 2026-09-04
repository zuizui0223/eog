import io
import json
import zipfile
from pathlib import Path

import pytest

from validation.sebms_ochlodes_endpoint3.gate1_dwca_metadata import (
    Gate1Stop,
    evaluate_dwca_metadata,
)


CONTRACT = (
    Path(__file__).resolve().parents[1]
    / "validation"
    / "sebms_ochlodes_endpoint3"
    / "gate1_dwca_metadata_contract.json"
)


def _contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _meta_xml(*, include_occurrence=True):
    occurrence = """
  <extension encoding="UTF-8" fieldsTerminatedBy="\\t" linesTerminatedBy="\\n" ignoreHeaderLines="1" rowType="http://rs.tdwg.org/dwc/terms/Occurrence">
    <files><location>occurrence.txt</location></files>
    <coreid index="0"/>
    <field index="1" term="http://rs.tdwg.org/dwc/terms/scientificName"/>
  </extension>
""" if include_occurrence else ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<archive xmlns="http://rs.tdwg.org/dwc/text/">
  <core encoding="UTF-8" fieldsTerminatedBy="\\t" linesTerminatedBy="\\n" ignoreHeaderLines="1" rowType="http://rs.tdwg.org/dwc/terms/Event">
    <files><location>event.txt</location></files>
    <id index="0"/>
    <field index="1" term="http://rs.tdwg.org/dwc/terms/eventID"/>
    <field index="2" term="http://rs.tdwg.org/dwc/terms/eventDate"/>
  </core>
  <extension encoding="UTF-8" fieldsTerminatedBy="\\t" linesTerminatedBy="\\n" ignoreHeaderLines="1" rowType="http://rs.gbif.org/terms/1.0/ExtendedMeasurementOrFact">
    <files><location>emof.txt</location></files>
    <coreid index="0"/>
    <field index="1" term="http://rs.tdwg.org/dwc/terms/measurementType"/>
  </extension>
  {occurrence}
</archive>
""".encode("utf-8")


def _archive(*, include_occurrence=True, duplicate_meta=False):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("meta.xml", _meta_xml(include_occurrence=include_occurrence))
        if duplicate_meta:
            zf.writestr("nested/meta.xml", b"<archive/>")
        zf.writestr("event.txt", b"eventID\teventDate\ne1\t2020-01-01\n")
        zf.writestr("emof.txt", b"eventID\tmeasurementType\ne1\ttemperature\n")
        zf.writestr("occurrence.txt", b"eventID\tscientificName\ne1\tSECRET_RESPONSE\n")
    return buffer.getvalue()


def _evaluate(data):
    ledger = []

    def read_range(start, end, role):
        payload = data[start : end + 1]
        ledger.append(
            {
                "role": role,
                "start": start,
                "end": end,
                "status": 206,
                "bytes_opened": len(payload),
            }
        )
        return payload

    result = evaluate_dwca_metadata(_contract(), len(data), read_range, ledger)
    return result, ledger


def test_stage1_resolves_event_emof_occurrence_from_meta_only():
    result, ledger = _evaluate(_archive())
    assert result["status"] == "gate1_dwca_metadata_ready"
    assert set(result["resolved_roles"]) == {
        "event_core",
        "extended_measurement_or_fact",
        "occurrence",
    }
    assert result["resolved_roles"]["event_core"]["location"] == "event.txt"
    assert result["resolved_roles"]["extended_measurement_or_fact"]["location"] == "emof.txt"
    assert result["resolved_roles"]["occurrence"]["location"] == "occurrence.txt"
    assert result["event_member_payload_bytes_opened"] == 0
    assert result["emof_member_payload_bytes_opened"] == 0
    assert result["occurrence_member_header_bytes_opened"] == 0
    assert result["occurrence_member_payload_bytes_opened"] == 0
    assert result["response_rows_opened"] == 0
    assert result["response_values_opened"] is False
    assert [row["role"] for row in ledger].count("meta_xml_payload") == 1


def test_stage1_never_reads_occurrence_payload_even_when_it_contains_response_token():
    data = _archive()
    result, ledger = _evaluate(data)
    occurrence = result["resolved_roles"]["occurrence"]["member"]
    response_interval = (occurrence["payload_start"], occurrence["payload_end"])
    for row in ledger:
        if row["role"] == "meta_xml_payload":
            continue
        assert not (
            row["start"] <= response_interval[1]
            and response_interval[0] <= row["end"]
        )


def test_stage1_fails_closed_when_required_occurrence_role_is_missing():
    data = _archive(include_occurrence=False)
    with pytest.raises(Gate1Stop, match="occurrence"):
        _evaluate(data)


def test_stage1_requires_exact_root_meta_member_not_a_substitute():
    data = _archive()
    # Rebuild an archive lacking the frozen root meta.xml but carrying a nested namesake.
    source = zipfile.ZipFile(io.BytesIO(data), "r")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("nested/meta.xml", source.read("meta.xml"))
        for name in ("event.txt", "emof.txt", "occurrence.txt"):
            zf.writestr(name, source.read(name))
    with pytest.raises(Gate1Stop, match="meta.xml"):
        _evaluate(buffer.getvalue())
