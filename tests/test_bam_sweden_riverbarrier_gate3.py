import json
from pathlib import Path

import pytest

from validation.bam_sweden_riverbarrier_external_bridge_v1.run_external_bridge_once import (
    ExecutionStop,
    parse_rawdf,
)


HERE = (
    Path(__file__).resolve().parents[1]
    / "validation"
    / "bam_sweden_riverbarrier_external_bridge_v1"
)


def _columns():
    contract = json.loads(
        (HERE / "execution_contract_draft.json").read_text(encoding="utf-8")
    )
    return contract["frozen_parser"]["exact_columns"]


def test_parser_accepts_exact_utf8_schema():
    header = ",".join(_columns()) + "\n"
    row = "0,0,A,R,1990,1,2,3\n"
    frame = parse_rawdf((header + row).encode("utf-8"), _columns())
    assert list(frame.columns) == _columns()
    assert len(frame) == 1


def test_parser_rejects_extra_column_after_payload():
    columns = _columns() + ["unexpected"]
    header = ",".join(columns) + "\n"
    row = "0,0,A,R,1990,1,2,3,x\n"
    with pytest.raises(ExecutionStop, match="CSV schema mismatch"):
        parse_rawdf((header + row).encode("utf-8"), _columns())
