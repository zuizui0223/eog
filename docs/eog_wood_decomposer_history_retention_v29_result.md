# EOG v29 result — wood-decomposer benchmark transport STOP

## Verdict

**TRANSPORT STOP BEFORE BIOLOGICAL SCORING.**

The candidate passed scientific relevance and reuse-rights screening, and the complete
v29 scoring contract was frozen before any EOG target score was calculated.

However, the exact archived Dryad CSV byte streams could not be materialized through the
available automated transport routes.

This is not biological evidence.

## Candidate remains scientifically suitable

Source:

- Leopold et al. (2017), *Ecology Letters*;
- article DOI: `10.1111/ele.12803`;
- Dryad DOI: `10.5061/dryad.7p2cv`;
- reuse: CC0.

The experiment remains an unusually good external benchmark because it manipulates
assembly history, nitrogen and fungivore context and measures both fungal community
composition and wood decomposition in the same microcosm system.

## What was recovered without scoring

Dryad public metadata identified version/resource **13946** and the exact source files:

- `sample.data.csv` — file 52325, 35,448 bytes,
  MD5 `d35287fd5f8522d8180451d42dc8969b`;
- `species.prevalence.csv` — file 52326, 12,148 bytes,
  MD5 `1f879a53fafcaaa5d148dbe112d3b389`;
- `collembola.csv` — file 52327, 2,621 bytes,
  MD5 `b7264f326709ab41d1fe8cac8ddc4a48`.

The official Dryad preview endpoints also allowed the schema to be recovered without
using the previewed response values for scoring.

The primary source table contains:

- `Sample_ID`;
- `Experiment`;
- `Harvest`;
- `Fungivores`;
- `Nitrogen_added`;
- `Initial_species`;
- initial/final wood dry mass;
- final nitrogen and carbon percentages.

The community table contains `Sample_ID` plus ten fungal prevalence columns.

## Transport failure

Two independent anonymous download routes were audited:

1. the Dryad dataset package API returns **HTTP 401** without OAuth;
2. the public `file_stream` routes return an **Anubis anti-bot HTML interstitial**
   instead of the archived CSV bytes to the automated runner.

The probe was hardened after an early false-positive parse so that HTML can no longer be
misclassified as CSV.

The authoritative transport audit is therefore a STOP, not a schema or biological result.

## Analysis contract already frozen

Before abandoning transport retries, v29 froze:

- primary endpoint: 12-month harvest;
- history levels: Ascocoryne, Bisporella, Daldinia, Trametes;
- context: nitrogen × fungivore;
- expected primary panel: 80 microcosms, exactly five per context × history cell;
- community target: ten-species prevalence Bray–Curtis;
- function target: fractional wood dry-mass loss;
- reduced model: context only;
- full model: context × history;
- 9,999 within-context history permutations;
- primary comparison: null-calibrated excess
  `ΔE = E_community - E_decomposition`;
- fixed temporal/representation sensitivities and STOP rules.

A scorer was also implemented that will only run after exact file-size and MD5
verification.

## Claim boundary

Do not claim from v29:

- any community history-retention value;
- any decomposition history-retention value;
- any evidence for or against attenuation;
- any failed replication of v28.

Do claim:

> **v29 is a scientifically and legally eligible external benchmark whose biological
> evaluation remains unobserved because exact source-byte materialization is blocked by
> repository transport controls.**

## Mainline consequence

The active empirical test therefore moves to v30, which uses a different research group,
explicitly licensed raw GitHub data, and a fully materializable grassland arrival-order
experiment.

v29 should be reopened only if the exact three archived Dryad files become available with
their frozen MD5 values.
