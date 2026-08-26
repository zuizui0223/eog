from __future__ import annotations

import gate2_effort_geometry_profile as gate

# Engineering-only compatibility for the frozen Gate2 implementation: the source
# contains one lowercase JSON-style false token in an output-only audit field.
# Supplying the intended Python constant does not alter any eligibility, geometry,
# timing, scale, or response-access rule.
gate.false = False

if __name__ == "__main__":
    raise SystemExit(gate.main())
