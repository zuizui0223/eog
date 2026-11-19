# Glanville k-exception minimum-relaxation sensitivity — frozen exploratory result

## Verified execution

- Pre-score (but post-exposure) protocol: `validation/glanville_minrelax_exception_budget_v1/protocol_v1.json`
- GitHub Actions: [44499784063](https://github.com/zuizui0223/eog/actions/runs/44499784063), **success**, synthetic guard tests succeeded, 12/12 original panels and 48/48 original strict radius/missing-source cells reverified.
- Canonical result artifact: `glanville-minrelax-exception-budget-v1`, ID `14515774216`, original JSON fingerprint without self-hash `f332758bd5510801e626c631281e6c090b61abb267639cb48685637410a9f07e`.
- Source archive SHAs, documented 2019 km->m conversion, host score thresholds `delta=0,1,2,3`, source policies and target eligibility were held unchanged.
- Original EOG-WF 3 scored /31 scientific STOP /3 administrative exclusions **unchanged**.

## The actual scientific result

The previous EOG maximum nearest-source requirement is genuinely a **tail-driven full-coverage bound**.

For the **primary t-1 source policy** and **unrestricted ordinal host difference** (`delta=3`), the following metrics were observed. `r_0` requires all targets to have at least one eligible local source within the radius; `r_{5%}` permits at most `floor(0.05*n)` target positives to remain unexplained under this local source model.

| Year | Eligible positive transitions | Strict full-coverage radius `r_0` (km) | Radius with <=5% unresolved `r_{5%}` (km) | Decrease |
| --- | ---: | ---: | ---: | ---: |
| 2007 | 349 | 4.443 | 2.296 | 48.3% |
| 2008 | 157 | 2.680 | 1.209 | 54.9% |
| 2009 | 285 | 5.953 | 2.049 | 65.6% |
| 2010 | 102 | 3.310 | 1.300 | 60.7% |
| 2011 | 521 | 8.050 | 2.533 | 68.5% |
| 2012 | 400 | 5.115 | 2.109 | 58.8% |

Under `delta=1`, the same six annual full-coverage radii range 4.608–11.283 km, but with <=5% unresolved they range 2.100–3.923 km (relative reductions 54.4–71.4%). The precise magnitudes depend on source and habitat constraint declaration.

**The decrease is mathematically guaranteed when exceptions are added.** The empirical information is **how much** the maximum changes and which years/source conditions exhibit high-tail concentration. It is not a null-hypothesis rejection and does not independently establish rare long-distance dispersal.

Across all 24 predeclared **primary host-gap panels** (12 year×source-policy combinations, `delta=1` and 3), removing the need to explain only **one** target reduced the strict bound by at least 25% in **3/24**. Thus high-tail concentration does not generally reduce to *one single extreme patch*. Many radii remain large with one target excepted; allowing a larger fixed fraction yields the strongest sensitivity.

## Unsupported source class is retained, not erased

Strict `delta=0` conditions were non-estimable in **6/12** year×source-policy panels because at least one target had no host-identical eligible source. When an exception budget of <=1% is permitted, **2/6** become finitely locally explainable; with <=5%, all **6/6** become finite. This does **not** validate the assumptions of missing source, unrecorded migration, or false positives. It reveals the minimum unresolved-positive count required before the declared local explanation becomes finite under that strict environment gate.

No strict `delta=1` or `delta=3` panel had missing compatible sources, so the 24-primary-panel result is not an artefact of reclassifying undefined as zero.

## What this changes in the EOG interpretation

A single `minimum required geographic relaxation to explain ALL observed occurrences` is too coarse a headline for this empirical system. It should be retained as the exact **universal positive-coverage bound** *inside its specified source and one-hop model*, alongside the **exception-conditional family of bounds** `r_k(delta)`. The two are different hypotheses:

- `r_0(delta)`: every observed-positive transition should have an eligible local source no farther than this radius.
- `r_k(delta)`: at least n−k positives are locally explainable; at most k remain without such an explanation under the same constraints.

The `k` unresolved positives must not be called false records, accidental outliers, or verified migrant events. They could reflect incomplete source history, observation error, rare displacements, other host constraints or misspecified patch-to-patch movement processes. They remain scientifically important.

The maximum/quantile comparison does not identify actual migration distances, causal environmental filtering, genetic parentage, the direction of movement, barriers across the Baltic, nor independent SDM predictive improvement. The same historical Glanville archives were already inspected; this analysis is **post-exposure exploratory robustness**, not a prospective ecological validation.

## Next inferential obstacle

A stronger biogeographic test requires **independent evidence about origin and observation**: patch-year survey effort and non-detection, independently inferred source-origin directions (mark-recapture or validated parentage), and a graph model with fixed candidate sources before scoring withheld transitions. Without that independent evidence, extending the exception set is a conditional **description of what cannot be explained locally**, not proof of its biological cause.

Run (reproduction only):

```bash
python -m pytest -q tests/test_glanville_minrelax_exception_budget_v1.py
python benchmarks/glanville_minrelax_exception_budget_v1.py \
  --protocol validation/glanville_minrelax_exception_budget_v1/protocol_v1.json \
  --parent validation/glanville_minrelax_empirical_unitfix_v2/frozen_aggregate_summary_v2.json \
  --output results/glanville_minrelax_exception_budget_v1/result.json
```
