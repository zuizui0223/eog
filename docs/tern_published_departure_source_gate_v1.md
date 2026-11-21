# Arctic tern known departure→arrival colony source gate (2026 Dryad)

**Status:** source metadata and declared future biological target only. No individual event rows, publication-level movement responses, distances or geographic source-robust contrast scored in this gate.

## Rationale

Existing [source-uncertain EOG MRR](occurrence_conditioned_source_minrelax_v4.md) quantifies which geographic/environmental/barrier relaxations suffice if **at least one** declared source exists vs **every** candidate source works, and their exact graph-hop ambiguity intervals. The previous actual-toad experimental-source attempt remains a **scientific STOP** despite resolving its source-distance signed encoding after exposure. A different independent real bird banding study is required before claiming real movements support EOG source-specific necessity.

The original [Dryad Arctic tern dataset](https://doi.org/10.5061/dryad.x69p8czxh) published **2026-09-30**, from Li et al. 2026 ([published paper](https://doi.org/10.1002/ece3.74372)), offers two event tables for Danish Arctic Terns:

| Event table | Original published events | Recorded physical origin | Outcome |
| --- | ---: | --- | --- |
| `U_DaD.csv` | **890** | Colony at which bird was banded as a chick | Different colony where bird later bred |
| `Ad_DaD.csv` | **200** | Colony at which bird was banded as a breeder | Different colony where bird later bred |

Both include `depart_lat/lon`, `arrive_lat/lon` in rounded **0.01° WGS84**, `year`, derived `distance_km`, derived `direction_deg` and event `UID`. The published source record says **raw individual ringing records and true per-individual IDs are not shared**. Departure/arrival event rows are already **selected movements** (not all bird encounters), and adult repeat events may occur. Neither observed stayers, candidate colony census effort nor environmental/barrier edge states are included in these two event tables.

## Why source labels are stronger—but not complete movement observations

Each event declares an independently recorded departure colony from marking history, unlike EOG's `any recorded-positive neighborhood` existential rule. This supports a later observational **source-specific versus source-existential geographic-feasibility** comparison, provided the alternative source roster is built exclusively from earlier data, not the outcome location.

However, ringing endpoints do not reveal the physical migration trajectory, continuous dispersal between colonies, intermediate stopovers, or true movement time. A source-to-destination straight-line geographic distance is a **lower-bound geometric separation**, not a per-flight or year-specific dispersal limit. The coordinates' **0.01° rounding** makes 1–2 km-scale distinctions imprecise; very narrow radii cannot be tested without rounding/coordinate-uncertainty safeguards.

## Freeze-before-data process

**Stage 0, this PR:** precommitted [source-only contract](../validation/tern_published_departure_source_gate_v1/protocol_v1.json) locks DOI, 2026-09-30 publication version date, 5 expected publisher file names, DOI/title checks, metadata/manifest size and host limits, and source-event limitations **before first archive/event-row retrieval**. The [source-only script](../scripts/eog_tern_published_source_metadata_gate_v1.py) checks official Dryad REST metadata and returns publication/version/file sizes/digests with source SHA fingerprints. The [tests](../tests/test_eog_tern_published_source_metadata_gate_v1.py) cover bad DOI, unrelated title, publication-date drift, unexpected file roster/zero sizes and no event access. Dedicated [metadata-only GitHub Actions](../.github/workflows/eog-tern-departure-source-metadata-v1.yml) freezes an aggregate receipt.

**Stage 1 (only after source manifest qualified):** pin **exact** CSV SHA/bytes and source version in a **separate pre-event protocol**. Freeze the geographic **source-specific minimum radius** `d(departure,arrival)`, any-source optimism baseline using **only departure colonies recorded earlier in chronology**, and explicit train/holdout cutoffs/radius levels. Predeclare source-evidence confidence, 0.01° coordinate rounding uncertainty, event-level nonindependence, missing stayed birds, and a full set of fail-closed checks. The published paper already analyzed distance and natal-versus-breeding age differences, so *replicating longer natal movements is not new ecological discovery*. Additional EOG value, if any, must concern how much the origin-agnostic estimated **necessary geographic relaxation** understates the verified marked origin, **without claiming its direction as a novel theorem**.

**Stage 2:** Only after Stage 1 pre-event freeze and exact checks can archived event rows be opened. Still not a new prospectively independent original EOG-WF endpoint; the publication is already known, and the closed EOG-WF denominator is **3 scored, 31 scientific STOP, 3 administrative exclusions**.

Source type: an independent ecological event archive with real tracked-band departure/arrival colony information, not a gene-inferred origin, yet neither natal trajectory nor full BAM A/B/M mechanism is identified.
