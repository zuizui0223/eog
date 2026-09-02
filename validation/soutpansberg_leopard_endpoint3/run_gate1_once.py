from __future__ import annotations

import json
from pathlib import Path

from validation.soutpansberg_leopard_endpoint3.gate1_zip_metadata import (
    FrozenRangeTransport,
    Gate1Stop,
    evaluate_zip_metadata,
    load_contract,
    terminal_stop_result,
)

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUTPUT = ROOT / "build" / "soutpansberg_leopard_endpoint3" / "gate1_zip_metadata_result.json"


def main() -> None:
    contract = load_contract()
    identity = contract["gate0_identity"]
    transport = FrozenRangeTransport(
        str(identity["download_url"]),
        int(identity["size_bytes"]),
    )
    try:
        result = evaluate_zip_metadata(contract, transport.read, transport.ledger)
    except Gate1Stop as exc:
        result = terminal_stop_result(contract, str(exc), transport.ledger)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
