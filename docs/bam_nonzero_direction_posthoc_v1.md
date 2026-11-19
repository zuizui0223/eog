# Nonzero response direction despite mechanism ambiguity — post-exposure audit

## Status and question

**Exploratory, post-result stratification of a previously exposed result; NOT a new endpoint, experiment, validation, independent species sample, or preregistered hypothesis test.** This audit preserves the parent EOG × BAM analysis and disaggregates its apparently high sign-identification counts into *positive*, *negative*, *zero*, and *ambiguous* outcomes. The question is narrower than mechanism identification: for an idealised A/B/M mask deletion, can the **nonzero sign of 90th-percentile positive-pairwise environmental span** be certified across all candidate BAM mechanisms compatible with an exact current occupancy map G?

Source: immutable [PR #677 canonical Actions run](https://github.com/zuizui0223/eog/actions/runs/42224332364), artifact `13504738461`, ZIP SHA-256 `b3cbd62afdf66adb065781e5734d1aef2a31c506742418c70df7823ea79b2efa`. Input member SHA-256 values are pinned in `benchmarks/audit_bam_nonzero_direction_v1.py`. Parent report fingerprint `bea5a189435961e4ef8501d8c0ddced3ae0c7818810667c5d97d807a3c34ac14` and denominators 12 landscapes / 768 candidate parameter worlds / 129 distinct current-G fibres / 69 mechanism-mask-ambiguous fibres are unchanged.

## Full reclassification of the original span target

Every axis row below has **129 distinct same-current-G fibres**. Direction categories are mutually exclusive and exhaustive at the original `1e-10` scale-aware sign tolerance.

| Idealised constraint release | Identified + | Identified − | Identified 0 | Ambiguous 0 vs nonzero | Ambiguous opposite ± | Any possible nonzero | Identified nonzero |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 34 | 0 | 85 | 10 | 0 | 44 | **34** |
| B | 54 | 6 | 64 | 5 | 0 | 65 | **60** |
| M | 57 | 5 | 59 | 3 | 5 | 70 | **62** |

Conditional on at least one candidate having a nonzero change, the fraction of *fibres* with unanimous nonzero direction is **34/44 (77.3%)** for A, **60/65 (92.3%)** for B, and **62/70 (88.6%)** for M. These fractions describe the finite roster's geometry; they are **not** a correct-prediction rate, conditional probability, or an ecological frequency. At least one identified nonzero response occurs in 11/12 parent landscapes for A and 12/12 for B and M, but the 129 fibres are nested within 12 constructed landscapes.

| Strictly nonzero sign identified even though… | A | B | M |
|---|---:|---:|---:|
| Multiple distinct A/B/M mechanism masks remain | 15 | **38** | 34 |
| Multiple exact released-G maps remain | 9 | **28** | 26 |

The latter is stronger than simply not recovering model parameters: even the **post-release spatial distribution** is not identified, yet the span-response sign is invariant across its alternatives. All three A/B/M *signs* are identified in 115/129 fibres, including 55/69 mechanism-mask-ambiguous fibres; only **3/129** have a nonzero response to **all three** releases. Of those 115 with all signs known, 104 have at least one nonzero response, and 11 only zero responses.

## Interpretation and guardrails

1. A/B/M denote abiotic allowance, biotic interaction and movement-accessibility **binary masks**, with G=A∩B∩M. Releasing an axis (`B∩M`, `A∩M`, `A∩B`) is a *static logic probe*, not a realised climate, partner, or dispersal manipulation. No wild causal effect was measured.
2. The target is the positive-pairwise **90th percentile** of distances of the full occupied-cell environmental point cloud under the original landscape-frozen median/MAD transform. It can **decrease under addition of occupied cells**, unlike convex-hull area. A negative span sign does not mean niche area shrank.
3. Exact complete present G, perfectly known finite candidate roster, constant environment and zero counterfactual observation error are idealised. One missed current occupied cell and probabilistic repeated detection can substantially weaken logical identification. No finite-roster percentage is field-calibrated.
4. Mechanism aliases can be target-equivalent; conversely some surviving M-release alternatives imply opposite signs and must return **abstain**. No scenario with incompatible signs is dropped to inflate the rate.
5. The conditional signs can disappear under ecological-universe expansion, new functional response targets, or actual intervention dynamics. Existing structured BAM expansion tests apply to **binary release decisions**, not these span signs; they cannot be transferred silently.

## Reproduction

Extract the original verified `bam-geometric-response-envelopes-v1` ZIP and run:

```bash
python benchmarks/audit_bam_nonzero_direction_v1.py \
  --source-dir /path/to/extracted/artifact \
  --output /tmp/bam_nonzero_direction_posthoc.json
pytest -q tests/test_bam_nonzero_direction_v1.py
```

The new script fails closed when either original member hash changes, when the parent denominators or summary values disagree, when the 3-axis fibres are incomplete, or when sign categories violate the declared partition. It does not rerun the original generator, and the archived result is a traceable *post-exposure derivative*, not fresh research evidence.

## Next independent empirical test — not claimed complete

Require a spatially out-of-sample site×visit detection history with effort and independent environmental, interaction and movement variables, plus a **predeclared, externally observed response or perturbation**. First calibrate which state/process hypotheses are compatible with imperfect observations. Freeze the ecological universe, its admissible intervention, the target geometry, and a sign/abstention rule *before* opening held-out post-change observations. Compare conditional sign coverage, wrong-sign rate, and abstention to baselines; report the landscape as the independent unit. No currently checked source provides the full causal field test, so this audit must not be converted into a predictive-superiority or natural-universality claim.