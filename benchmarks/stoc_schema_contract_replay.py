"""Response-free replay of the historical STOC schema mismatch through v2 aliases.

This does not rerun STOC, inspect species responses, or modify the frozen endpoint.
It checks only that the generic prospective schema contract can represent the exact
coordinate-header mapping recorded in the historical STOC result.
"""

from __future__ import annotations

import json
from pathlib import Path

from eog.v2.schema_adapter import SchemaAliasContract, SchemaRole


ROOT = Path(__file__).resolve().parents[1]
FROZEN_RESULT = ROOT / "validation" / "stoc_eogwf" / "stoc_eogwf_result.json"
FROZEN_CONTRACT = (
    ROOT / "validation" / "stoc_eogwf" / "eligibility_and_preoutcome_contract.json"
)


def run_replay() -> dict[str, object]:
    result = json.loads(FROZEN_RESULT.read_text(encoding="utf-8"))
    contract = json.loads(FROZEN_CONTRACT.read_text(encoding="utf-8"))

    historical = dict(result["schema_adapter"]["mapping"])
    declared = tuple(contract["source"]["declared_nonresponse_columns"])
    if "X_WGS84" not in declared or "Y_WGS84" not in declared:
        raise AssertionError("frozen STOC contract no longer contains uppercase coordinates")
    if historical != {"x_wgs84": "X_WGS84", "y_wgs84": "Y_WGS84"}:
        raise AssertionError("historical STOC schema mapping drift")

    adapter = SchemaAliasContract(
        roles=(
            SchemaRole("site", ("site",)),
            SchemaRole("period", ("period",)),
            SchemaRole("x", ("X_WGS84", "x_wgs84")),
            SchemaRole("y", ("Y_WGS84", "y_wgs84")),
            SchemaRole("temp", ("temp",)),
            SchemaRole("precip", ("precip",)),
            SchemaRole("cover_agri", ("cover_agri",)),
            SchemaRole("cover_water", ("cover_water",)),
            SchemaRole("cover_wet", ("cover_wet",)),
            SchemaRole("sdiv_hab", ("sdiv_hab",)),
        ),
        allow_unmapped_columns=True,
    )
    physical_header = (
        "site",
        "period",
        "x_wgs84",
        "y_wgs84",
        "temp",
        "precip",
        "cover_agri",
        "cover_water",
        "cover_wet",
        "sdiv_hab",
        "species_columns_not_opened_here",
    )
    resolved = adapter.resolve(physical_header)

    generic_to_historical = {
        resolved.mapping["x"]: "X_WGS84",
        resolved.mapping["y"]: "Y_WGS84",
    }
    if generic_to_historical != historical:
        raise AssertionError(
            f"generic alias resolution {generic_to_historical!r} does not reproduce "
            f"historical mapping {historical!r}"
        )

    return {
        "schema": "eog.stoc_schema_contract_replay.v1",
        "uses_biological_response": False,
        "reruns_frozen_stoc": False,
        "counts_as_predictive_evidence": False,
        "historical_first_failed_run": int(result["schema_adapter"]["first_failed_run"]),
        "historical_mapping": historical,
        "generic_role_mapping": resolved.mapping,
        "contract_fingerprint": adapter.fingerprint,
        "resolution_fingerprint": resolved.fingerprint,
        "physical_header_fingerprint": resolved.physical_header_fingerprint,
        "interpretation": (
            "The historical STOC lowercase coordinate spelling is representable by a "
            "prospectively declared exact-alias contract without changing source bytes "
            "or any scientific world definition."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_replay(), indent=2, sort_keys=True))
