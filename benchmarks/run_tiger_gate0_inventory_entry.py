#!/usr/bin/env python3
"""Run the frozen tiger XLSX inventory with an administrative-state vocabulary fix.

The workbook is national, so a column named ``State`` is expected to mean an Indian
administrative state rather than a latent occupancy state.  Generic ``state`` and
``count`` tokens are therefore removed from the provisional response-keyword heuristic
before any workbook byte is opened.  Explicit tiger/presence/absence/occupancy/detection
terms remain response indicators.  No scientific gate, source, geometry or outcome
rule changes.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


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
    module.main()


if __name__ == "__main__":
    main()
