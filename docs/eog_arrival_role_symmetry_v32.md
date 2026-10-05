# EOG v32 — arrival-role alignment and priority-effect symmetry

## Status

**FROZEN BEFORE ANY v32 ROLE-ALIGNED SCORE IS CALCULATED.**

v31 showed that persistent assembly history is not stored in the same component of community structure across systems. In v28, removing fungal taxon labels left essentially all history retention intact. In v30, removing plant functional-group labels removed roughly three quarters of the retained-history excess.

v32 asks whether that difference maps onto a classic ecological distinction: whether the effect of arriving first has a similar structural form across identities, or whether its strength/form depends on which identity arrived first.

## Ecological question

> **If community identities are replaced by assembly roles, do different arrival histories converge to the same present structure?**

A relatively symmetric first-arriver effect should converge after role-alignment: the first arriver has a similar structural consequence regardless of which identity filled that role. A colonist-specific effect should retain history even after absolute identities are removed and the first-arriver role is aligned.

## Role-aligned transformation

For each experimental unit: (1) identify the abundance coordinate corresponding to the experimentally first-arriving identity; (2) place that abundance in coordinate 1, labelled only first_arriver; (3) sort all remaining abundance coordinates from largest to smallest; (4) discard all remaining taxon / functional-group names.

The transformation preserves exactly the same raw abundance values, dimensionality, total abundance, abundance assigned to the first-arriver role, and unlabeled abundance structure among later identities. It removes absolute ecological identity.

## v28 microbiome

Reuse the frozen v28 common panel and bias-corrected five-taxon representation. History-to-coordinate mapping is exact because the five Treatment labels are the five focal fungal taxa. Use n=233, context=Genotype, history=Treatment, Bray-Curtis, the frozen Genotype × Treatment model, 9,999 within-Genotype permutations, seed 20261005.

## v30 grassland

Reuse the frozen v30 primary panel and three-functional-group shoot biomass. Mapping: F-first→Forbs, G-first→Grasses, L-first→Legumes. Use n=19, block=Replicate, history=Treatment, Bray-Curtis, the frozen Replicate + History model, 9,999 within-Replicate permutations, seed 20261005.

## Primary statistics

E_role = observed role-aligned partial R² minus median(role-aligned null partial R²).

Also retain the v31 values E_labeled and E_rank. Define role_gain = E_role − E_rank, and role_fraction = E_role / E_labeled when E_labeled > 0.

## Prospective prediction

> **role_fraction(v28 microbiome) > role_fraction(v30 grassland).**

Rationale: the microbiome history signal survives complete identity removal, suggesting colonist-specific differences in abundance architecture. The grassland signal is largely lost when identity labels are removed, consistent with a more role-symmetric first-mover effect in which histories mainly swap which functional group occupies a dominant role.

This prediction was frozen before either role-aligned score was calculated. No universal threshold for symmetric versus asymmetric is declared.

## Mechanism-facing descriptive output

For each history level, report the mean and SD of the final share of total target abundance belonging to the first-arriving identity. This is descriptive only; no permutation p-value is attached because the selected response coordinate is defined by the manipulated history label itself.

## Gates

Before accepting v32 results: reproduce authoritative v28 labeled E; reproduce authoritative v28 rank E from v31; reproduce authoritative v30 labeled E; reproduce authoritative v30 rank E from v31; and verify that each role-aligned row is a permutation of the same raw values as its labeled row.

## Exposure boundary

Known before freeze: all v28, v30 and v31 results, source data, and classic theory that priority-effect strength/direction can vary with species identity and that symmetric niche preemption is possible. Unknown before freeze: both role-aligned E values, role_gain values, role_fraction values, and history-specific first-arriver-share summaries under the v32 transform.

## Claim boundary

v32 must not claim direct measurement of niche preemption versus niche modification; that role-alignment proves a mechanistic interaction model; that one system is universally symmetric and the other universally asymmetric; or first discovery that priority-effect strength varies among species.

If the prediction is supported, the allowed interpretation is: **the two empirical storage modes identified in v31 are consistent with different degrees of colonist-specific structural asymmetry: the same assembly role is expressed more differently among fungal histories than among grassland histories.**
