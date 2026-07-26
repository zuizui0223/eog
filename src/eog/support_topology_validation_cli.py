"""Command-line entry point for audited support-topology held-out validation."""
from __future__ import annotations

import argparse
from pathlib import Path

from .support_topology_validation import run_heldout_validation, write_validation_bundle


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--support", type=Path, required=True)
    parser.add_argument("--mask", type=Path, required=True)
    parser.add_argument("--anchors", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--declaration", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    bundle = run_heldout_validation(
        support_path=args.support,
        mask_path=args.mask,
        anchors_path=args.anchors,
        candidates_path=args.candidates,
        declaration_path=args.declaration,
    )
    write_validation_bundle(bundle, args.output_dir)
    print(bundle.fingerprint)


if __name__ == "__main__":
    main()
