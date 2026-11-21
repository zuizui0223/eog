# What is actually identified by wetland positive records? Conditional partial identification before EOG process-world inference

## Completed logical source audit — not occupancy estimation

The earlier Q1 native-method comparison showed that changing which survey-method rows are retained can reverse **5 of 27** recorded species×wetland-category prevalence differences. This follow-up asks a different question: **which directions of the corresponding hypothetical true site-level prevalence differences are logically consistent with the original source-positive evidence?**

**Result:** Under the explicitly conditional assumption that every recorded positive is a genuine site-level presence, while all source non-positives are entirely unknown, **none of the 27 strict positive or strict negative group differences is identified**. Four full-source comparisons have *one-sided weak-sign* bounds (two nonnegative, two nonpositive); 23 allow both strict signs, and zero remains feasible in **all 27**. Filtering to acoustic+visual reduces the number of weakly one-sided bounds to two and makes **25/27** comparisons two-sided.

This is a **post-exposure, static binary site-status logical calculation**, *not* a fitted occupancy likelihood, an inference that amphibian occupancy is closed for the paper's up-to-91-day survey periods, or independent evidence of ecological A/B/M.

Source: Wenner et al. (2025), *Effectiveness of wetland restoration on amphibians in a drying grassland habitat losing its breeding sites*, *Global Ecology and Conservation* 62 e03837, [DOI 10.1016/j.gecco.2025.e03837](https://doi.org/10.1016/j.gecco.2025.e03837); source CSV and original R [Zenodo 10.5281/zenodo.15044115](https://doi.org/10.5281/zenodo.15044115), CC BY 4.0. Exact pinned source: `zuizui0223/frogcs@5e2f0a87c639df373fa2700b29403d2ab417a1cc`, survey SHA256 `45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd`, site SHA256 `93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319`.

## Conditional identified set

Use original Q1 **27** source sites (13 intervention, 6 control, 8 artificial) and **9** amphibian species, giving **243** possible site×species binary status slots. For method panel `P`, group `g` and taxon `s`, let `k_{g,s,P}` be the number of source sites with at least one positive count recorded by a method in `P`, among `n_g` original group sites.

Two **unverified biological assumptions** define the conditional logic:

1. Every source-recorded positive is correct (*perfect specificity*; no false positives).
2. One site×species status across the recorded survey window can be treated as a hypothetical static binary variable; every other non-positive source record provides **no confirmed absence**. Statuses are otherwise unconstrained, with no spatial, environmental, biotic, movement, or phylogenetic relation imposed.

Then for that hypothetical static latent site-positive fraction, `pi_g`:

`k_g/n_g <= pi_g <= 1`.

For any two original wetland categories `A` and `B`:

`k_A/n_A - 1 <= pi_A-pi_B <= 1 - k_B/n_B`.

These bounds are attainable under the explicitly unconstrained binary-completion universe: choose only recorded positive sites in `A` and all sites positive in `B` for the lower extreme; choose all sites positive in `A` and only recorded positive sites in `B` for the upper extreme. Set all sites positive in both groups for a **zero-difference completion**. That zero completion is logically compatible with any source-positive-only mask, so no strict direction is identified without additional trusted negative evidence or structural assumptions.

**This is not a claim that all species actually occupy every surveyed wetland**; it is an admissible completion needed to demonstrate why source positives alone do not identify an occupancy difference.

## What the original recorded data do and do not rule out

| Source panel | Hypothetical static positive site×species constraints | Unfixed site×species slots | Comparisons allowing strictly both signs | Weakly nonnegative only | Weakly nonpositive only | Strict nonzero sign identified |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| All four methods | **144** | **99** | **23/27** | 2 | 2 | **0** |
| Acoustic+visual | **104** | **139** | **25/27** | 1 | 1 | **0** |

The original complete source records impose **40 more binary positive constraints** than acoustic+visual. In a deliberately unconstrained `27 sites × 9 taxa` Boolean completion universe, the exact number of compatible **static binary site-status masks** is `2^99` with the full source and `2^139` using the AV records alone. The latter contains `2^40` times more *simple binary mask assignments*. This is **not** an estimate of ecological EOG transition worlds, a likelihood, number of plausible colonization histories, Bayesian entropy, biological information measured in bits, or a verified field uncertainty distribution.

### Original five method-dependent sign reversals: what bounds permit

All rates below are *percentage-point differences*, with full source and AV using the same wetland category site denominators. Bounds are conditional on the two assumptions above.

| Taxon and category A−B | Full-source observed difference | Full-source possible latent difference | AV observed difference | AV-only possible latent difference |
| --- | ---: | ---: | ---: | ---: |
| *Lissotriton vulgaris*, intervention−control | +2.56 | **[−30.77, +33.33]** | −26.92 | [−76.92, +50.00] |
| *Bufo bufo*, intervention−control | −12.82 | **[−46.15, +33.33]** | +20.51 | [−46.15, +66.67] |
| *Lissotriton vulgaris*, intervention−artificial | −30.77 | **[−30.77, 0.00]** | +23.08 | [−76.92, +100.00] |
| *Lissotriton vulgaris*, artificial−control | +33.33 | **[0.00, +33.33]** | −50.00 | [−100.00, +50.00] |
| *Bufotes viridis*, artificial−control | −8.33 | **[−75.00, +66.67]** | +8.33 | [−75.00, +83.33] |

**Two of the five AV observed-sign reversals would be impossible as *strict* latent signs if all full-source positives were true**: both *L. vulgaris* comparisons involving the **8/8 source-positive artificial wetlands**.

- For intervention−artificial, artificial's full-source positive fraction is 8/8, so its hypothetical true fraction must be 1; the intervention minus artificial difference **cannot be strictly positive**, although acoustic+visual's *recorded* difference is +23.08 points.
- For artificial−control, artificial's true positive fraction is again fixed at 1 by the full-source positives; its hypothetical true difference from control **cannot be strictly negative**, although AV's *recorded* difference is −50.00 points.

The other three original observed-sign reversals still have conditional intervals allowing both strict directions, so **the original positive records alone cannot settle which latent comparison direction is real**. None of these statements establishes statistical or causal restoration outcomes, and even the one-sided boundaries still allow **equal** hypothetical true rates.

## EOG: nested evidence sets, but no ecological-world count

All 15 nonempty method subsets from acoustic, visual, dipnet, and bottletrap were exhaustively evaluated: **405** source taxon/group contrast intervals. For every pair of nested method subsets `P ⊆ Q`, the corresponding recorded positive sets satisfy `O_P ⊆ O_Q`. Under the stated conditional static binary-completion assumptions, their identified intervals necessarily nest in the opposite sense: `I_Q ⊆ I_P` (the larger source-positive set yields tighter conditional bounds).

The test checks the full 15-subset lattice pairwise, **using integer numerators for all interval endpoints** before converting to percentage points. Yet all 405 conditional source-only contrasts include **zero**, and none identifies a strict direction.

This parallels EOG's general principle that positive evidence constrains admissible configurations, but **it does not validate the finite EOG transition-world operators**, does not count real viable ecological processes, and does not authorize evidence-dependent/self-excluded source-world monotonicity claims. The static mask universe is purely an audit of what the recorded positives permit.

## Validation and scientific STOPs

The source-verified executable `benchmarks/wetland_positive_only_partial_id_v1.py` imports the previously authenticated original method-lattice source verifier. Its tests cover two-sided, nonnegative, nonpositive, and exactly zero identified intervals, whole-method witness nesting, false-positive assumption provenance, and rejection of illegal positive counts/denominators. Source positivity is never silently recoded to true ecological absence.

- Fixed post-exposure protocol `validation/wetland_positive_only_partial_id_v1/protocol.json` was committed **before** this additional source-interval computation, but the wetland data had been inspected in many previous analyses.
- Result and SHA provenance `validation/wetland_positive_only_partial_id_v1/result_receipt.json`.
- Source full-lattice long tables: `method_panel_identification_intervals.csv` (**405** rows), `method_panel_positive_only_summary.csv` (**15** rows), `native_site_species_recording_mask.csv` (**243** rows), and `five_method_reversals_identification_bounds.csv` (**5** rows).

[Verified GitHub Actions run #43713122936](https://github.com/zuizui0223/eog/actions/runs/43713122936) **SUCCESS**, result fingerprint `864b741974f0b8f12347825516eceab2232b3cd16291e998f18368416b2d9247`; artifact **14161008859**, SHA256 ZIP `5e445c6b40b330559397980b38d95b63c900d190aaf41f4bed9464cf957dc6c2`. All 15 source method panels and all 405 comparisons were checked in CI, including the two full-vs-AV sign contradictions under full-source positive-specificity assumptions.

**STOP:** Recorded positives may not be perfectly specific, biological states are not verified closed over up to 91 days, species detection and field effort remain unresolved, the data contain no verified biological absences, and original `unmarked` coefficients were not refitted. There is no ecological A/B/M causal inference, true occupancy estimation, new scored EOG-WF endpoint, or merge of Draft PR #697. The original three scored / 31 scientific STOP / three administrative exclusion evidence remains unchanged.
