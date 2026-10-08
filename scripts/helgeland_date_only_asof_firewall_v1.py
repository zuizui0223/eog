#!/usr/bin/env python3
"""Date-only observed-encounter input firewall for Helgeland EOG.

Pure, synthetic-testable utility. This module NEVER loads source files or
computes future-outcome targets, dispersal, occupation or model performance.
It does not claim observation records were entered in the database by cutoff.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Iterable, Mapping

DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
DIRECT_STAGES = frozenset(("nest", "capt", "obs"))
# Only these five fields are inspected. Especially not Year, Least_age,
# Least_hatchyear, scriptsex, filled, gene_new or model-derived N_corr.
ALLOWED_FIELDS = ("ID", "Island", "Location", "date", "stage")

@dataclass(frozen=True)
class ObservedAtCutoff:
    individual_id: str
    island: str
    locality: str
    observed_date: date
    direct_stage: str


def strict_date(value: str) -> date:
    if not isinstance(value, str) or not DATE.fullmatch(value):
        raise ValueError("Only ISO YYYY-MM-DD physical observation dates are accepted")
    return date.fromisoformat(value)


def direct_history_as_of(
    records: Iterable[Mapping[str, str]], cutoff_date: str
) -> tuple[ObservedAtCutoff, ...]:
    """Project ONLY directly observed on/before-cutoff records.

    This defines information availability from *observation timestamps*, NOT
    actual database-entry times (which are still unqualified).
    Subsequent record rows are not consulted after their dates are checked.
    Never infer an individual's birthplace from a later sighting.
    """
    cutoff = strict_date(cutoff_date)
    output: list[ObservedAtCutoff] = []
    for record in records:
        when = strict_date(record["date"])
        if when > cutoff:
            continue
        stage = record["stage"]
        if stage not in DIRECT_STAGES:
            continue
        ident = record["ID"].strip()
        island = record["Island"].strip()
        locality = record["Location"].strip()
        if not ident or not island or not locality:
            raise ValueError("Direct encounter missing ID or observed island/locality")
        output.append(ObservedAtCutoff(ident, island, locality, when, stage))
    return tuple(sorted(output, key=lambda x: (x.observed_date, x.individual_id,
                                                x.island, x.direct_stage)))


def directly_observed_single_nest_sources_as_of(
    history: tuple[ObservedAtCutoff, ...]
) -> frozenset[tuple[str, str]]:
    """Return eligible same-ID, single-nest-island sources, NOT movements.

    A source means that a physical nest encounter was observed at/before the
    cutoff on exactly one island. No post-cutoff information is consulted.
    """
    nests: dict[str, set[str]] = {}
    for item in history:
        if item.direct_stage == "nest":
            nests.setdefault(item.individual_id, set()).add(item.island)
    return frozenset((ident, next(iter(islands))) for ident, islands in nests.items()
                     if len(islands) == 1)


def hold_receipt(cutoff_date: str) -> dict:
    """Only gate/status metadata; do not serialize individual encounter tuples."""
    strict_date(cutoff_date)
    return {
        "schema": "eog.helgeland.date_only_asof_information_firewall.v1",
        "status": "SYNTHETIC_INFORMATION_FIREWALL_ONLY__ECOLOGICAL_HOLD",
        "cutoff_calendar_date": cutoff_date,
        "input_time_source": "physical date field only; never the Year label",
        "direct_stage_allowed": sorted(DIRECT_STAGES),
        "other_source_fields_used": False,
        "future_observations_restricted_to_outcome_side": True,
        "database_ingestion_time_verified": False,
        "actual_field_encounter_observed_as_of_date_verified": False,
        "recording_effort_and_surveyed_zero_verified": False,
        "post_cutoff_biological_outcomes_read": False,
        "individual_observations_exported": False,
        "dispersal_or_colonization_scored": False,
        "independent_heldout_benchmark_qualified": False,
        "ecological_endpoint_authorized": False,
    }
