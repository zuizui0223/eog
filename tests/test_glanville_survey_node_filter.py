import csv
import json
import subprocess
import sys
from pathlib import Path


HEADER = [
    "year",
    "patch",
    "population",
    "plantago",
    "veronica",
    "plantago_low",
    "veronica_low",
    "plantago_dry",
    "veronica_dry",
    "grazing_presence",
    "grazing_intensity",
    "previous_population",
]


def _write_tsv(path: Path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def _run(tmp_path: Path, outside_population: str):
    network = tmp_path / f"network_{outside_population}.tsv"
    survey = tmp_path / f"survey_{outside_population}.tsv"
    output = tmp_path / f"filtered_{outside_population}.tsv"
    audit = tmp_path / f"audit_{outside_population}.json"

    _write_tsv(
        network,
        ["patch", "x", "y", "area"],
        [["A", 0, 0, 1], ["B", 1, 0, 1]],
    )
    _write_tsv(
        survey,
        HEADER,
        [
            [1999, "A", "7", "p1", "v1", "", "", "", "", "", "", "6"],
            [1999, "OUT", outside_population, "secret1", "secret2", "", "", "", "", "", "", "secret_prev"],
            [1999, "B", "0", "p2", "v2", "", "", "", "", "", "", "0"],
        ],
    )

    subprocess.run(
        [
            sys.executable,
            "benchmarks/filter_glanville_survey_to_frozen_nodes.py",
            "--patch-network",
            str(network),
            "--survey",
            str(survey),
            "--output",
            str(output),
            "--audit",
            str(audit),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return output.read_text(encoding="utf-8"), json.loads(audit.read_text(encoding="utf-8"))


def test_filter_keeps_only_frozen_nodes_and_preserves_retained_response_text(tmp_path):
    output, audit = _run(tmp_path, "999999")

    assert "\tOUT\t" not in output
    assert "\tA\t7\t" in output
    assert "\tB\t0\t" in output
    assert audit["network_node_count"] == 2
    assert audit["retained_survey_rows"] == 2
    assert audit["excluded_survey_rows"] == 1
    assert audit["excluded_unique_patch_ids"] == 1
    assert audit["population_response_values_parsed_or_used_for_filter"] is False
    assert audit["node_universe_expanded"] is False


def test_filter_result_is_invariant_to_excluded_response_value(tmp_path):
    output_a, audit_a = _run(tmp_path, "1")
    output_b, audit_b = _run(tmp_path, "999999")

    assert output_a == output_b
    assert audit_a == audit_b
