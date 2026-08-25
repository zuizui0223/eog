from __future__ import annotations

import sys

import gate0_geometry as gate


def _fixed_base_result():
    return {
        "schema": "eog.bodie_pika_replication_2.gate0.v1",
        "attempt_id": gate.CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "dryad": {},
        "non_response_downloads": [],
        "geometry": {},
        "response_firewall": {
            "census_payload_requests": 0,
            "census_payload_bytes_opened": 0,
            "census_header_bytes_opened": 0,
            "census_sheet_names_opened": False,
            "census_rows_opened": False,
            "census_values_opened": False,
            "scientific_model_fits": 0,
            "heldout_scores": 0,
        },
    }


gate.base_result = _fixed_base_result

if __name__ == "__main__":
    sys.exit(gate.main())
