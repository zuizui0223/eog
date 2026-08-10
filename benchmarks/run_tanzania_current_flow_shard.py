"""Generate one outcome-free Tanzania current-flow resistance shard."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.tanzania_current_flow_candidates import (
    N_SHARDS,
    read_prepared_region,
    write_candidate_shard,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--n-shards", type=int, default=N_SHARDS)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    prepared = read_prepared_region(args.prepared)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    npz_path = args.output_dir / f"current_flow_{prepared.region}_shard_{args.shard_index:02d}.npz"
    manifest = write_candidate_shard(npz_path, prepared, args.shard_index, args.n_shards)
    manifest["candidate_file"] = npz_path.name
    manifest_path = args.output_dir / f"current_flow_{prepared.region}_shard_{args.shard_index:02d}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
