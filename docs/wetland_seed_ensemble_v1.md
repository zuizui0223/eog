# EOG × wetland amphibians: 256-seed source-processing sensitivity

## State and scientific role

**Completed post-exposure algorithmic robustness audit, not an independent biological replication.** The source is the fixed 2024 Hungary wetland amphibian survey data supplied by Mizsei & Wenner (2025), Zenodo DOI [10.5281/zenodo.15044115](https://doi.org/10.5281/zenodo.15044115), CC BY 4.0. The exact archived `zuizui0223/frogcs` commit `5e2f0a87c639df373fa2700b29403d2ab417a1cc`, survey CSV SHA256 `45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd` and site SHA256 `93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319` are checked before computation.

The **fixed 256 seeds** are consecutive integers **1 through 256** and include the original R script's `set.seed(123)`. Each seed runs the same public `edvardmizsei/hunviphab::survreps` code pinned to commit `25d4c64da289ffcc14679619bb3b18bd494de872`, Git blob `ae7de0753faa1660b9e1ce1bc81b8cdb39a9c670`, under R 4.4.3 / `Mersenne-Twister;Inversion;Rejection`. Each cohort is filtered before its own `set.seed(seed)`, as in the verified original Q1/Q2 preparation. No occupancy fitting is run.

Protocol `validation/wetland_seed_ensemble_v1/protocol.json` was committed **before** this seed ensemble's scores were produced. However the same real data, mechanism, exact expectation and seed=123 were already exposed: this remains **retrospective/post-exposure** research, not a new prospectively heldout ecological endpoint.

## Source-positive evidence and seed sensitivity

A *native-positive site×species pair* is one with at least one positive count in the original recorded survey rows. A pair is considered **lost in the pseudo-occasion representation** when none of its originally positive source rows were selected in the 20-row site-level `survreps` output. This is a statement about input-data thinning, never about true species absence.

| Metric | Q1: 27 sites, 144 native-positive pairs | Q2: 13 intervention sites, 77 pairs |
| --- | ---: | ---: |
| Original seed=123 lost pairs | **3** | **6** |
| Fixed 256-seed mean lost pairs | **9.9570** | **4.9219** |
| Fixed 256-seed median | **10** | **5** |
| Seed 5th–95th percentiles | **5–15** | **2–9** |
| Seed min–max | **3–19** | **0–11** |
| Exact per-row sampling expectation (not Monte Carlo) | **9.4759** | **4.8714** |
| Seeds with zero lost pairs | **0/256** | **2/256** |

- Original seed=123's Q1 loss **3** is tied for the minimum across the 256 seeds; **3/256** seeds have loss ≤3. This is an *algorithmic seed-rank statement*, not a p-value or evidence of intentional seed selection by the study's authors.
- The 256-seed mean differs from the exact theoretical expectation by +0.4812 Q1 and +0.0504 Q2. The seed-to-seed descriptive Monte Carlo standard errors of the means are 0.1936 and 0.1384, respectively. These are **not** confidence intervals for the real wetland population, and seeds are not ecological replicates.
- The highest previously identified exact per-pair loss probability is *Triturus dobrogicus* at `tengelyut-1` (1 positive among 18 archived rows, exact conditional drop probability 0.3188). It was omitted in **87/256** Q1 seed representations and **76/256** Q2 representations; this compares a deterministic fixed seed roster with the analytic probability, not independent field resampling.

## Shared-site analyst processing instability

Q2's 13 sites are a strict subset of Q1's 27. Their **native positive site×species evidence is identical**, yet the cohort-specific filtering changes the sequence of seed-conditioned row-selection calls, so the pseudo-detection representation differs.

| Shared 13-site comparison | Result across 256 fixed paired seeds |
| --- | ---: |
| Mean disagreement in pseudo-detection site×species labels | **7.9688** |
| Median disagreements | **8** |
| 5th–95th percentile | **4.75–12** |
| Min–max | **3–14** |
| Seeds with ≥1 disagreement | **256/256** |
| Original seed=123 disagreements | **7** |

This directly demonstrates **representation instability conditional on analyst cohort choice**, not changes in biology, actual movement, wetland restoration or historical colonization.

## Resampled-row repetition

Each cohort normalizes recorded observations to 20 pseudo-occasion rows per site, regardless of original row count. Over the same 256 seeds:

| Repetition result | Q1 | Q2 |
| --- | ---: | ---: |
| Total output pseudo-row positions | 540 | 260 |
| Mean distinct original rows represented | **280.25** | **148.36** |
| Mean positions duplicating a previously used source row | **259.75** | **111.64** |
| Seed=123 duplicated source-row positions | **253** | **107** |

Reusing a source row does not create another independent physical visit. Distinct **source CSV rows**, however, also cannot automatically be equated with truly independent physical bottle traps or dates: the source `surv` key is `site:method:doy` and includes two multi-row bottletrap groups.

## Reproducibility and validation

- R generator: `benchmarks/wetland_seed_ensemble_v1.R`
- Independent Python evaluator: `benchmarks/wetland_seed_ensemble_v1.py`
- Fail-closed tests: `tests/test_wetland_seed_ensemble_v1.py`
- Frozen post-exposure protocol: `validation/wetland_seed_ensemble_v1/protocol.json`
- Exact seed-level outcome CSV: `seed_ensemble_summary.csv`
- Full positive-pair×seed evidence table: `seed_ensemble_native_positive_pairs.csv` (**56,576** rows = 256×(144+77)).
- The seed123 selected source rows were replayed against the previous **independently archived mapping**; all Q1/Q2 earlier counts were reproduced. The Python validator independently recomputed loss counts, exact per-pair probabilities, paired disagreements, seed roster and fingerprints.

Source-authenticated dedicated run: [GitHub Actions #43674891349](https://github.com/zuizui0223/eog/actions/runs/43674891349), **SUCCESS**. ZIP artifact ID **14145523682**, SHA256 `5efd36b7dab619ea5c32becbfedc24b17766d908be873b2032bd24b190dd7895`. Both CSVs are in this artifact with standalone SHA256 `0ed9b0f74ea4da5580a35ddfeada709cc6dfac5804bb1a9c916a71dd7b16b7cd` (seed summaries) and `3ba582b5fbbdaa0e6c6f89cb70bb640cba9e56e50bc0ca187a223f81c0a45ae6` (native-positive pair details). Machine-readable result fingerprint `6094d8e326e7027a0ff0548679b5d88edc89dae3fa469dc7625d523661f58cdf`.

## What this does not establish

1. **No occupancy coefficient or original field inference** has been evaluated: reusing row-level pseudo-occasions does not prove an original treatment coefficient or significance test is wrong.
2. No claim that the publicly pinned `hunviphab` and R4.4.3 precisely match the author's historical installed R environment.
3. No attempt to deduplicate the two same-`surv` bottletrap groups or to infer independent trap identities, effort, repeat-visit closure, or detection probability.
4. Seeds are **not independent populations, habitats or independent scientific tests**. Reported empirical seed quantiles concern algorithmic input perturbations.
5. This work is separate from the immutable EOG-WF method-paper **3 scored predictive endpoints / 31 scientific STOPs / 3 administrative exclusions**. No fourth endpoint, causal A/B/M or generic prediction-superiority claim is added.

**Next valid scientific dependency:** Obtain physical visit/trap effort and closure metadata, and ideally original R/package session information, before comparing occupancy estimates from native observation units to the publication's pseudo-occasion representation. This protocol cannot independently certify those field assumptions.
