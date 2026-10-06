# Assembly-history storage — Abstract and Results draft v1

## Working title

**Assembly history is stored through contrasting structural channels in ecological communities**

## Abstract

Priority effects can make ecological communities depend on arrival history, but an
historical effect can persist in some properties of a community while becoming weak in
others. We asked where information about experimentally manipulated assembly history
remains encoded in the present. We reanalysed two independent randomized arrival-order
experiments—a plant phyllosphere microbiome and a grassland community—using matched
experimental units and randomization-calibrated measures of retained history. In both
systems, history was strongly retained in final community composition but was close to
the randomized baseline in another present-state target: fungal composition versus host
rust disease in the microbiome, and shoot functional-group composition versus belowground
root distribution in the grassland. We then removed ecological identity while preserving
the same abundance values and response dimensionality. Microbiome history remained fully
detectable in the unlabeled rank-abundance architecture, whereas most grassland history
disappeared when functional-group identities were removed. A prospective attempt to
explain this contrast by the identity of the first-arriver role failed a complete
placebo-mapping audit, preventing a role-based post hoc explanation. Further prospective
tests within the microbiome showed that historical storage was uneven across arrival
histories: Alternaria had the largest deletion leverage, and its direct contrast with the
other histories was expressed more strongly in rank-1 dominance than in lower-rank
structure. This dominance shift was positive in 11 of 12 host genotypes and was driven
primarily by a genotype-shared component. Thus assembly history is not stored in one
universal feature of ecological communities. Different systems retain the past in
different structural components of the present, and locating that storage is logically
prior to assigning a mechanism.

## Results

### Assembly history was retained unevenly across present-state targets

We first asked whether the same experimentally manipulated arrival history remained
equally visible in different properties measured on the same experimental units.

In the plant-microbiome experiment, the frozen common panel contained 233 plants spanning
12 host genotypes and five fungal arrival-history treatments. After accounting for host
genotype and calibrating the history statistic against 9,999 within-genotype treatment
permutations, final fungal community composition retained clear historical information
(partial R² = 0.3697; null median = 0.2230; retained-history excess
(E=+0.1467); permutation p = 0.0001). The aggregate host rust-lesion state, measured on
the same plants, was close to its randomized baseline (partial R² = 0.2300; null median =
0.2147; (E=+0.0153); p = 0.3893).

The independent grassland experiment gave the same qualitative contrast. The primary
panel contained 19 rhizoboxes subjected to three directional functional-group arrival
histories. Final aboveground Forbs–Grasses–Legumes biomass composition retained an
extremely strong history signal (partial R² = 0.9529; null median = 0.1495;
(E=+0.8034); p = 0.0001), whereas the complete six-layer root-biomass distribution
retained little history beyond the blocked permutation baseline (partial R² = 0.1853;
null median = 0.1509; (E=+0.0344); p = 0.3765). Total shoot biomass was similarly weak
((E=+0.0948); p = 0.2562). An exact enumeration of all 31,104 admissible within-block
history assignments reproduced the shoot-versus-root contrast.

These experiments therefore did not support a description of a community as simply
"remembering" or "forgetting" its assembly history. The amount of historical information
visible in the present depended strongly on which ecological state was measured.

### Removing ecological identity revealed different storage channels in the two systems

The strong compositional signal could arise because history determines which ecological
identity occupies each abundance position, because history changes the unlabeled
abundance distribution itself, or both. We separated these possibilities without
changing the underlying abundance values or response dimensionality.

For each experimental unit, we sorted the final composition vector from largest to
smallest, thereby deleting taxon or functional-group labels while retaining the exact
multiset of abundances. The preregistered hypothesis that compositional memory would be
generally identity based was refuted.

In the microbiome, labeled fungal composition and identity-stripped rank abundance retained
essentially the same amount of history. Labeled composition had (E=+0.1467), whereas
the five-dimensional rank-abundance target had (E=+0.1486) (p = 0.0001). The resulting
identity-storage gap was −0.0019. Shannon entropy, another label-invariant summary,
also retained strong history ((E=+0.2523); p = 0.0001). Thus fungal arrival history
changed abundance architecture even after fungal names were erased.

The grassland showed the opposite structure. Labeled functional-group composition retained
(E=+0.8034), but sorting the same three biomass values reduced retained history to
(E=+0.1949) (p = 0.0769). Only 24.3% of the labeled-composition excess remained in the
rank-abundance target. Shannon entropy still retained a smaller but detectable signal
((E=+0.3800); p = 0.0235). Most grassland memory therefore resided in the mapping
between functional-group identity and abundance position, whereas microbiome memory was
already encoded strongly in identity-free abundance structure.

### A first-arriver-role explanation failed a complete specificity audit

We next tested a plausible explanation for the contrasting storage channels. A
role-aligned representation placed the abundance of the experimentally first-arriving
identity in the first coordinate and sorted all remaining abundances. This representation
produced a very large history signal in the microbiome and little additional information
in the grassland, initially suggesting that the systems differed in how interchangeably
identities expressed the first-arriver role.

However, the transformation itself used the observed history treatment to select a
response coordinate. We therefore prospectively enumerated every equally complex
history-to-coordinate mapping.

In the microbiome, the biologically correct mapping ranked only 53rd among all 120
one-to-one mappings. Its role-aligned R² was 0.945878, almost identical to the median
incorrect-mapping R² of 0.945209; the exact finite mapping-tail fraction was 0.4417.
In the grassland, the biologically correct mapping ranked last among the six possible
mappings (R² = 0.337247), whereas the strongest incorrect mapping reached R² = 0.938223.

The role-alignment statistic was therefore not specific to the biological first-arriver
mapping. We retained the numerical transformation results but rejected the mechanistic
interpretation. This negative test left the system-specific storage-channel result intact
while showing that a treatment-indexed response transformation can generate convincing
but biologically nonspecific separation.

### Historical leverage within the microbiome was distributed but strongly uneven

The placebo-mapping ensemble nevertheless yielded one prospective clue: every one of its
five highest-scoring microbiome mappings preserved Alternaria-to-Alternaria while
reassigning the other fungal histories. We tested this clue using the treatment-independent
rank-abundance response.

Removing each fungal arrival-history treatment in turn showed that Alternaria had the
largest positive deletion leverage. Full five-history rank-abundance memory was
(E=+0.1486). Removing Alternaria reduced it to (E=+0.0875) (p = 0.0086), giving
leverage (D=+0.0611). Removing Cladosporium produced a smaller positive leverage
((+0.0264)), whereas removing Aureobasidium, Fusarium, or Dioszegia increased the
null-calibrated history signal. A separate Alternaria-versus-all-other-histories contrast
on the complete 233-plant panel retained (E=+0.0803) (p = 0.0004).

Alternaria was therefore not the sole source of architecture memory—the remaining four
histories still retained a significant signal—but it contributed the largest prospective
leverage.

### Alternaria-associated history was concentrated more strongly in dominance than in lower-rank structure

We decomposed identity-free rank abundance into the largest abundance share and the
relative organization of the remaining ranks.

Across all five histories, rank-1 dominance retained (E=+0.1759) (p = 0.0002), and the
normalized ranks 2–5 retained (E=+0.1258) (p = 0.0005). Removing Alternaria reduced
dominance memory to (E=+0.0895) and lower-rank memory to (E=+0.0862). Alternaria
deletion leverage was therefore +0.0865 for dominance and +0.0396 for the lower-rank
tail, supporting the preregistered dominance-centered prediction.

We then replaced the deletion analysis with a direct randomized-history comparison on the
full panel. For Alternaria versus the other four histories, rank-1 dominance retained
(E=+0.1181) (p = 0.0002), whereas the normalized lower-rank tail retained
(E=+0.0472) (p = 0.0316). The preregistered component contrast was
(Delta E=+0.0709). The same dominance-centered pattern therefore emerged under both
leave-one-history-out and direct-history designs.

Alternaria-history plants had a mean rank-1 share of 0.778 and a median of 0.793, compared
with 0.711 and 0.713, respectively, among the other histories. These identity-free
statistics do not establish which fungal taxon occupied rank 1 in any individual plant.

### The Alternaria-associated dominance shift was broadly shared across host genotypes

Finally, we asked whether the pooled dominance signal was generated by a small subset of
host-genotype interactions. Every one of the 12 host genotypes contained both Alternaria
and Other history levels, allowing the contrast to be evaluated within genotype.

We decomposed the binary-history fit into a genotype-shared component and an additional
genotype-by-history interaction. The common component explained R² = 0.1353
(p = 0.0001), whereas the additional interaction component explained R² = 0.0342 and was
not unusually large relative to the within-genotype permutation null (p = 0.7548).
The shared component accounted for 79.8% of the observed binary-history sum of squares.

Alternaria-minus-Other dominance contrasts were positive in 11 of 12 genotypes. Their
equal-genotype-weighted mean was +0.0610 (p = 0.0001), with a median of +0.0714.
All five East genotypes and six of seven West genotypes were positive descriptively.

Thus the dominance-centered Alternaria history signature was not principally produced by
one or two host backgrounds. Within the tested panel, it was a broadly shared response to
assembly history, although the analysis does not imply complete genotype independence or
identify the interaction mechanism that generated the dominance shift.

## Results-level conclusion

Across two independent assembly experiments, historical information was not uniformly
distributed across present ecological states. The two systems also differed in the
structural component of community composition that carried that information. In the
microbiome, identity-free abundance architecture retained substantial history; prospective
follow-up localized its strongest history-level contribution to an Alternaria-associated,
host-genotype-shared increase in community dominance. In the grassland, most historical
information instead depended on which functional-group identity occupied the abundance
structure.

Source reconciliation sharpens the microbiome interpretation. The original study reports
that Alternaria had the greatest relative abundance across treatments but only a relatively
small species-specific benefit from arriving early. Thus the EOG dominance result is not
equivalent to an exceptionally strong Alternaria priority-effect log-ratio. The archived
relative-abundance data also lack absolute fungal load, direct pairwise interaction
measurements and a clean later pre-pathogen community time point.

A candidate first-arriver-role explanation failed a complete specificity audit, and the
remaining archive cannot distinguish intrinsic competitive ability, competitor suppression,
niche pre-emption, niche modification or host-mediated effects. The supported contribution
is therefore the localization of historical storage, not identification of the interaction
mechanism that generates it.
