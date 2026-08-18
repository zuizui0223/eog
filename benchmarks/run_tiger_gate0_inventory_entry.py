#!/usr/bin/env python3
"""Run the frozen tiger XLSX inventory with two metadata-only disambiguations.

1. A column named ``State`` is expected to mean an Indian administrative state rather
   than latent occupancy state, so generic ``state``/``count`` tokens are removed from
   the provisional response-keyword heuristic.
2. Excel may attach namespaced extension attributes such as ``x14ac:dyDescent`` to the
   first worksheet row.  Because Gate 0 intentionally extracts that row without the
   whole worksheet namespace envelope, those extension attributes are removed before
   the standard spreadsheet cells are parsed.

Neither correction opens a later row or changes any source, geometry, world, response
or decision rule.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import sys


PREFIXED_ATTRIBUTE = re.compile(
    br"\s+[A-Za-z_][A-Za-z0-9_.-]*:[A-Za-z_][A-Za-z0-9_.-]*=\"[^\"]*\""
)


def main() -> None:
    path = Path(__file__).with_name("run_tiger_gate0_xlsx_inventory.py")
    spec = importlib.util.spec_from_file_location("tiger_gate0_inventory", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load tiger Gate 0 inventory module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    module.RESPONSE_TERMS.discard("state")
    module.RESPONSE_TERMS.discard("count")

    original_parse_row_cells = module.parse_row_cells

    def parse_row_cells_without_extension_attributes(row_bytes):
        if row_bytes:
            row_bytes = PREFIXED_ATTRIBUTE.sub(b"", row_bytes)
        return original_parse_row_cells(row_bytes)

    module.parse_row_cells = parse_row_cells_without_extension_attributes
    module.main()


if __name__ == "__main__":
    main()
