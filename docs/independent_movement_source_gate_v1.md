# Independent movement evidence gate for EOG minimum required relaxation (v1)

**Status:** PRE-TRANSPORT SOURCE-ONLY QUALIFICATION. No ecological outcome has been read or scored by this workflow. The first branch commit froze [the DOI/filename/STOP protocol](../validation/independent_movement_source_gate_v1/protocol_v1.json) before any provider files were downloaded. All source bytes remain ephemeral; only metadata SHA256s, public CSV headers, exact row counts and an explicit scientific gate outcome may be preserved in GitHub artifacts.

## Why this follows source-uncertain EOG v4

The v4 [source-hop bound](occurrence_conditioned_source_minrelax_v4.md) yields exact finite-graph facts:

- The possible but not universal source-consistency interval at a threshold is `h_possible <= H < h_robust`.
- On a strongly connected baseline source core, its width is at most the directed core diameter.
- **An actual ecological explanation requires source evidence**; neither the set of all positive sites nor a model-assigned origin is an observed historical founder.
- EOG's existing Åland Glanville series is post-exposure and its genetic origins are *model inferred*; it cannot be presented as a fresh independent validation of the same target.

Instead of producing another synthetic ecology panel, this gate searches for a genuinely separate real marked-individual source–destination design **without opening any movement response values until a new, pre-score target design is defined**.

## Publisher evidence and predeclared candidates

| Priority | Independent source and DOI | Published file names | Evidential strength and intrinsic limitation |
| --- | --- | --- | --- |
| **Primary** | [Moura et al. 2021 Heliconius mark–release–recapture/translocation](https://doi.org/10.5061/dryad.34tmpg4m6) | `data_site_fidelity.csv`, `turning_data.csv`, `README.txt` | Marked butterflies, experimental release/translocation and recapture, so potentially **observed individual origin–later location**. An experimental release point is not a natural founder; a target patch graph/environment/barrier is not guaranteed. |
| Secondary | [Jreidini & Green 2022 toad displacement and later recapture](https://doi.org/10.5061/dryad.x3ffbg7ms) | `Jreidini_and_Green_homing_toads_2021.csv`, `README_file.rtf` | Explicit displacement treatment (100/250/500m) and a 24-hour relocation context. Does **not** itself demonstrate a site-to-site colonization, ecological barrier or environmental connectivity rule. |

The two studies differ from the previously used Glanville records and from each other. They are **not** independent replications of EOG until a compatible inferential estimand has been defined and verified at the source-column/record level.

## Frozen STOP conditions

The one-shot [GitHub Actions source-only gate](../.github/workflows/eog-independent-movement-source-gate-v1.yml) follows Dryad's published REST API links under explicit source host, version, file count and byte caps, and checks the filenames and publisher-supplied digests before reporting **CSV headers and total rows only**. It may return:

- `SOURCE_SCHEMA_ONLY_QUALIFIED_BIOLOGICAL_OUTCOME_NOT_SCORED`: official published files were received and checksums/header/row counts match. **Does NOT mean** the data have a usable biological source–destination clock.
- `STOP_TRANSPORT_*`: the public API or file cannot be fetched within the one-attempt source gate.
- `STOP_PUBLISHER_FILELIST_MISMATCH`, `STOP_MEMBER_*`, `STOP_VERSION_*`: source version or identity not verifiable.
- `SOURCE_SCHEMA_HAS_SCIENTIFIC_STOP`: aggregate one or both source gates failed. A successful GitHub Actions *job* that records a scientific STOP is **not** source qualification.

Allowed inference following **future** source qualification must separate the following three claims:

1. **Individual observed movement geometry:** same marked ID, pre/post times and metric positions. This can independently check a *source-locked geographic lower bound* at the **appropriate** spatial and temporal grain.
2. **Population colonization or source uncertainty:** needs independently justified population source hypotheses, observation/detection correction and eligible target patch-years. Individual recapture alone does not qualify.
3. **Three-axis EOG minrelax:** requires external landscape source/edge graph, environmental transitions, physically authenticated barrier states and held-out transitions; absent those, mark `environmental_barrier_NOT_IDENTIFIABLE`, never invent them.

**The source-only gate does not set a dispersal radius from the outcomes.** A positive or adverse biological test needs a new freeze before reading movement-event rows, including the unit (individual/patch/occasion), source meaning, holdout rules, comparator, source accuracy and environmental/barrier availability.

## Reproduce offline source gate safety tests

```bash
python -m pytest -q tests/test_eog_independent_movement_source_gate_v1.py
```

Sources and implementation:

- [Pre-transport source protocol](../validation/independent_movement_source_gate_v1/protocol_v1.json)
- [Strict Dryad official-API script](../scripts/eog_independent_movement_source_gate_v1.py)
- [Offline file-identity/checksum/STOP tests](../tests/test_eog_independent_movement_source_gate_v1.py)
- [Dedicated GitHub workflow](../.github/workflows/eog-independent-movement-source-gate-v1.yml)

**Hard boundary:** EOG-WF 3 scored /31 scientific STOP /3 administrative exclusions remains closed; zero new scored predictive endpoints; original Glanville and v4 source-MRR results unchanged.
