"""Exact finite observation histories under explicitly synthetic occupancy models.

Occupancy is stipulated, never derived from EOG reachability. Independent visits,
constant occupancy, and no false positives are assumptions of these fixtures only.
"""

import json
from fractions import Fraction
from itertools import product


def run_benchmark():
    rows = []
    checked = 0
    for case, occupied_probability in (
        ("perfect_detection", Fraction(1)),
        ("imperfect_detection", Fraction(1, 2)),
        ("uninformative_detection", Fraction(0)),
    ):
        # The worlds differ in stipulated occupancy at one surveyed site.
        probabilities = {"absent": Fraction(0), "occupied": occupied_probability}
        for visits in (1, 2, 3):
            histories = []
            total_mass = dict.fromkeys(probabilities, Fraction(0))
            for history in product((0, 1), repeat=visits):
                likelihoods = {}
                for world, p in probabilities.items():
                    mass = p ** sum(history) * (1 - p) ** (visits - sum(history))
                    likelihoods[world] = mass
                    total_mass[world] += mass
                survivors = sorted(w for w, mass in likelihoods.items() if mass > 0)
                # Independent support oracle, not a floating-point cutoff.
                expected = []
                if not any(history):
                    expected.append("absent")
                if (
                    (occupied_probability == 1 and all(history))
                    or (0 < occupied_probability < 1)
                    or (occupied_probability == 0 and not any(history))
                ):
                    expected.append("occupied")
                if survivors != expected:
                    raise AssertionError((case, history, survivors, expected))
                checked += 1
                histories.append(
                    {
                        "detections": list(history),
                        "likelihoods": {w: str(m) for w, m in likelihoods.items()},
                        "compatible_world_ids": survivors,
                        "status": "contract_falsified"
                        if not survivors
                        else (
                            "unique_within_declared_models"
                            if len(survivors) == 1
                            else "unresolved"
                        ),
                    }
                )
            if any(mass != 1 for mass in total_mass.values()):
                raise AssertionError(
                    "observation history probabilities must sum to one"
                )
            rows.append({"case": case, "visits": visits, "histories": histories})
    return {
        "schema": "eog.detection_identifiability_boundary.v1",
        "claim_ceiling": "stipulated occupancy and detection models only; not reachability or empirical evidence",
        "histories_checked": checked,
        "results": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run_benchmark(), indent=2, sort_keys=True))
