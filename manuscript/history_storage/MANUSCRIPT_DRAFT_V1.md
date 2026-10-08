# Assembly history is stored through contrasting structural channels in ecological communities

## Abstract

Priority effects can make ecological communities depend on arrival history, yet a historical effect need not remain equally visible in every property of the resulting community. We asked where experimentally manipulated assembly history remains encoded in the present. We reanalysed two independent randomized arrival-order experiments—a plant phyllosphere microbiome and a grassland community—using matched experimental units and randomization-calibrated measures of retained history. In both systems, history was strongly retained in final community composition but was close to the randomized baseline in another present-state target: fungal composition versus host rust disease in the microbiome, and shoot functional-group composition versus belowground root distribution in the grassland. We then removed ecological identity while preserving the same abundance values and response dimensionality. Microbiome history remained fully detectable in unlabeled rank-abundance architecture, whereas most grassland history disappeared when functional-group identities were removed. A prospective attempt to explain this contrast by first-arriver role alignment failed a complete placebo-mapping audit, preventing a role-based post hoc explanation. Further prospective tests within the microbiome showed that historical storage was uneven across arrival histories: Alternaria had the largest deletion leverage, and its direct contrast with the other histories was expressed more strongly in rank-1 dominance than in lower-rank structure. This dominance shift was positive in 11 of 12 host genotypes and was driven primarily by a genotype-shared component. Source reconciliation showed that Alternaria was generally highly abundant but did not have the largest species-specific early-arrival benefit, and the archive lacks the absolute-abundance and interaction data required to identify mechanism. Thus assembly history is not stored in one universal feature of ecological communities. Different systems retain the past in different structural components of the present, and locating that storage is logically prior to assigning a mechanism.

## Introduction

The order in which species arrive can alter the trajectory of community assembly long after the initial colonization event. These priority effects are a central source of historical contingency in ecological communities and can arise through niche pre-emption, niche modification, or other interaction processes that allow early arrivals to change the conditions experienced by later colonists (Fukami 2015). Empirical work has shown that arrival order can alter species abundances, community composition, host-associated microbiomes, ecosystem processes, and restoration outcomes across a wide range of systems (Fukami et al. 2010; Dickie et al. 2012; Leopold and Busby 2020; Weidlich et al. 2021; Debray et al. 2022). The existence of priority effects is therefore no longer the main unresolved question.

A harder problem is what becomes of that historical signal after assembly has proceeded. Previous studies have asked whether assembly-history effects attenuate as one moves from individual species to community- or ecosystem-level properties, but there is no general expectation that higher-level properties must erase history. In wood-decaying fungi, for example, assembly history can strongly affect ecosystem functioning (Fukami et al. 2010), and field experiments found little evidence for universal attenuation from species or community responses to ecosystem properties (Dickie et al. 2012). Conversely, taxonomically distinct communities can sometimes converge in function. Thus the relationship between historical contingency in community structure and historical contingency in other ecological properties is contingent rather than monotonic.

This raises a different question: **where, within the present state of a community, is assembly history actually stored?** We use “storage” here descriptively, not in an information-theoretic or mechanistic sense. A present-day variable stores history to the extent that experimentally assigned assembly histories remain distinguishable in that variable after the relevant design structure is accounted for. Under this framing, a community does not simply “remember” or “forget” its past. The same historical perturbation may remain conspicuous in taxonomic or functional-group composition while becoming weak in an aggregate host, spatial, or ecosystem state. Even within community composition, history might reside mainly in which identities occupy abundance positions, in the unlabeled shape of the abundance distribution, or in both.

We examined this problem using two independently published arrival-order experiments that provide complementary ecological settings. In a black cottonwood foliar microbiome experiment, five fungal colonists were introduced in different arrival-history treatments across 12 host genotypes, and final fungal composition and host rust disease were measured on the same plants (Leopold and Busby 2020). In an independent grassland rhizobox experiment, forbs, grasses, or legumes were sown before the other functional groups, and final aboveground biomass composition and belowground root distribution were quantified (Alonso-Crespo et al. 2022). The original studies established priority effects in their respective systems. We therefore treated them as external benchmarks rather than as fresh tests of whether arrival order matters.

Our analysis proceeded in a prospectively constrained sequence. First, we quantified how much assembly history remained in different present-state targets within each experiment. Second, we removed ecological identity from the composition vectors while preserving the same abundance values and response dimensionality, allowing us to distinguish identity-dependent storage from unlabeled abundance architecture. Third, when a biologically attractive first-arriver-role explanation emerged, we tested its specificity against all equally complex history-to-coordinate mappings rather than retaining it as a post hoc narrative. Finally, within the microbiome, we prospectively localized the strongest architecture-level historical signal to particular history levels and to specific components of rank-abundance structure, and tested whether that signal generalized across host genotypes.

This design leads to three distinct questions. First, is assembly-history retention strongly target specific within real experiments? Second, is persistent compositional history stored in the same structural component across systems? Third, once a storage channel is localized, how far can the existing archive support a mechanistic explanation? The answer to the first two questions is empirical; the third defines the boundary between a structural legacy and an inferred ecological mechanism.

## Methods

### Analytical framework

For every analysis, we compared a reduced model containing the frozen experimental context or block structure with a full model that additionally contained the manipulated assembly-history factor. For scalar responses, retained history was quantified with nested-model partial (R^2). For multivariate responses, we used a Gower-centered distance-based analogue of the same nested-model decomposition.

Because partial (R^2) can be inflated by model dimensionality even under randomized history labels, especially in factorial models with many genotype-by-history terms, we calibrated each observed value against a design-respecting permutation distribution. We summarize retained history as

[
E = R^2_{mathrm{observed}} - operatorname{median}(R^2_{mathrm{null}}).
]

We refer to (E) as retained-history excess. It is a null-calibrated effect-size diagnostic, not a universal measure of ecological importance. Permutation (p)-values are reported as diagnostics for the frozen randomization contracts.

All derived analyses were specified in versioned protocols before the corresponding target score was calculated. Where a later interpretation depended on a transformation of the response using observed treatment labels, we added a separate placebo-transformation audit before retaining a mechanistic interpretation.

### Plant microbiome experiment

We used the publicly available data underlying Leopold and Busby (2020). The frozen common panel contained 233 plants spanning 12 host genotypes and five fungal arrival-history treatments: Alternaria, Aureobasidium, Cladosporium, Dioszegia, and Fusarium. We used the pre-rust fungal community sample (Timepoint 1) and aggregated rust lesion measurements to the plant level.

For fungal composition, we retained the five focal fungal taxa, divided counts by the deposited taxon-specific sequencing-bias factors, preserved structural zeros, and closed the five corrected abundances to proportions. Bray–Curtis dissimilarity was calculated on the resulting five-dimensional vectors. The host-state target was plant-level rust lesion fraction.

The reduced model contained Genotype. The full model contained Genotype, Treatment, and the Genotype × Treatment interaction. Treatment labels were permuted within Genotype for 9,999 permutations using the frozen seed 20261005. This model intentionally treats genotype-specific priority effects as part of the history signal.

### Grassland experiment

We used the raw data underlying Alonso-Crespo et al. (2023). The primary panel contained 19 rhizoboxes assigned to directional arrival histories in which forbs, grasses, or legumes were sown first. Synchronous controls were excluded from the primary history contrast. Replicate was retained as the blocking factor.

The aboveground target was the three-dimensional final biomass vector of Forbs, Grasses, and Legumes. The belowground target was the six-dimensional root-biomass distribution across 10-cm soil layers from 0–60 cm. Bray–Curtis dissimilarity was used for both multivariate targets.

The reduced model contained Replicate and the full model contained Replicate + History. History labels were permuted within Replicate for 9,999 permutations. An independent post-freeze enumeration of all admissible within-block history assignments was used to audit the primary contrast.

### Identity-stripping analysis

To separate abundance architecture from ecological identity, we transformed each composition vector by sorting the exact same abundance values from largest to smallest within each experimental unit. This operation preserves response dimensionality, total abundance, and the complete multiset of abundance values but deletes the mapping between an abundance and its taxon or functional-group identity.

For the microbiome, the five labeled fungal proportions were compared with the corresponding five-dimensional rank-abundance vector. For the grassland, the three functional-group biomasses were compared with the corresponding three-dimensional rank-abundance vector. The same history model, experimental units, distance metric, and permutation stream were used within each system.

Shannon entropy of the closed composition was used as a secondary label-invariant scalar sensitivity.

### Role-alignment and placebo-mapping audit

A subsequent analysis aligned each community by assembly role: the abundance associated with the experimentally first-arriving identity was placed in the first coordinate and the remaining abundances were sorted. Because this response transformation uses the observed history label, we did not treat a large role-aligned score as mechanistically interpretable without a specificity control.

We therefore enumerated every equally complex one-to-one mapping between history labels and response coordinates: all 120 bijections for the five-fungus microbiome and all six bijections for the three functional groups in the grassland. We compared the biologically correct mapping with the complete placebo-mapping ensemble. The mapping-tail fraction is an exact specificity comparison over transformations, not a causal randomization (p)-value.

### Microbiome history-level leverage

After the placebo-mapping audit, all five highest-scoring microbiome mappings shared one feature: Alternaria history was mapped to the Alternaria coordinate. We treated this only as a clue and froze a new treatment-independent test.

Using the rank-abundance response from the identity-stripping analysis, we removed each of the five fungal history levels in turn and recomputed (E) on the remaining four histories. For history (h), deletion leverage was

[
D_h = E_{mathrm{full}} - E_{-h}.
]

The prospective prediction was that Alternaria would have the largest positive (D_h). We also tested a frozen binary contrast of Alternaria versus the four other histories on the full 233-plant panel.

### Dominance versus lower-rank architecture

We decomposed the identity-free rank-abundance vector into two targets. Rank-1 dominance was the largest of the five sorted focal-fungus proportions. The lower-rank target contained ranks 2–5 renormalized to sum to one, thereby removing variation in the magnitude of the dominant rank.

We quantified retained history for both targets on the full five-history panel and after the frozen Alternaria deletion. We then repeated the component comparison using the direct Alternaria-versus-rest binary history on all 233 plants.

### Host-genotype generality

For rank-1 dominance, we decomposed the Alternaria-versus-rest fit into a genotype-shared history component and an additional Genotype × BinaryHistory interaction component. We also calculated the within-genotype difference in mean rank-1 dominance between Alternaria and Other histories for all 12 genotypes.

### Mechanistic ceiling audit

No new derived target was scored after the genotype-generality analysis. Instead, we reconciled the EOG results with the source experiment and audited whether the archive contained measurements capable of discriminating ecological mechanism. The source study's second community time point was not used because the original analysis states that it was collected during rust sampling and was overwhelmed by rust reads. We also searched the archived repository for absolute-abundance, growth, pairwise-interaction, or host-response measurements. None provided the process-level evidence required to distinguish intrinsic competitive ability, competitor suppression, niche pre-emption, niche modification, or host-mediated effects.

## Results

### Assembly history was retained unevenly across present-state targets

In the plant-microbiome experiment, final fungal community composition retained a clear assembly-history signal after accounting for host genotype. Partial history (R^2) was 0.3697, compared with a permutation-null median of 0.2230, giving retained-history excess (E=+0.1467) ((p=0.0001)). In contrast, aggregate rust lesion fraction on the same plants had partial (R^2=0.2300) but a null median of 0.2147, yielding only (E=+0.0153) ((p=0.3893)).

The independent grassland experiment showed the same qualitative asymmetry. Final shoot functional-group composition had partial (R^2=0.9529), null median 0.1495, and (E=+0.8034) ((p=0.0001)). The complete six-layer root-biomass distribution retained little history beyond the blocked null ((R^2=0.1853), null median 0.1509, (E=+0.0344), (p=0.3765)). Total shoot biomass was also weak ((E=+0.0948), (p=0.2562)). Exact enumeration of all 31,104 admissible within-block history assignments reproduced the shoot-versus-root contrast.

Thus neither system was well described as simply remembering or forgetting its assembly history. The strength of historical retention depended strongly on which present ecological state was measured.

### Removing ecological identity revealed contrasting storage channels

The hypothesis that compositional memory would generally depend on ecological identity was refuted.

In the microbiome, labeled fungal composition retained (E=+0.1467), whereas the same five abundance values sorted within each plant retained (E=+0.1486) ((p=0.0001)). The identity-storage gap was therefore (-0.0019). Shannon entropy also retained strong history ((E=+0.2523), (p=0.0001)). Removing fungal names did not erase the assembly-history signal.

The grassland showed a different structure. Labeled functional-group composition retained (E=+0.8034), but sorting the same three biomass values reduced retained history to (E=+0.1949) ((p=0.0769)). Only 24.3% of the labeled retained-history excess remained in the rank-abundance target. Shannon entropy retained a smaller but detectable signal ((E=+0.3800), (p=0.0235)).

The two systems therefore differed not only in how much history was visible across endpoints, but in the structural component of community composition carrying that history. Microbiome history was strongly encoded in unlabeled abundance architecture, whereas most grassland history depended on which functional-group identity occupied each abundance position.

### A first-arriver-role explanation failed a complete specificity audit

Aligning each community by the experimentally first-arriving identity produced a large apparent history signal in the microbiome and little additional signal in the grassland, initially suggesting a difference in how identities expressed the first-arriver role.

The placebo-mapping audit did not support that mechanism.

In the microbiome, the biologically correct history-to-fungus mapping had role-aligned (R^2=0.945878). The median among the 119 incorrect mappings was 0.945209. The correct mapping ranked only 53rd of 120, with an exact mapping-tail fraction of 0.4417. Several biologically incorrect mappings produced larger (R^2), reaching 0.956289.

In the grassland, the biologically correct mapping ranked last among the six possible mappings. Its (R^2) was 0.337247, compared with a median incorrect-mapping value of 0.876815 and a maximum of 0.938223.

Thus treatment-indexed coordinate transformations could generate strong separation even when the mapping between treatment and ecological identity was wrong. We retained the numerical role-alignment results as descriptive transformations but rejected the interpretation that first-arriver-role interchangeability explained the cross-system storage contrast.

### Historical leverage within the microbiome was distributed but uneven

The placebo ensemble nevertheless yielded a prospective clue: every one of its five highest-scoring microbiome mappings preserved Alternaria-to-Alternaria while reassigning the other histories. A separate treatment-independent deletion analysis supported this clue.

Full five-history rank-abundance memory was (E=+0.1486). Removing Alternaria reduced it to (E=+0.0875) ((p=0.0086)), giving deletion leverage (D=+0.0611), the largest of the five histories. Removing Cladosporium produced a smaller positive leverage ((+0.0264)), whereas removing Aureobasidium, Fusarium, or Dioszegia increased null-calibrated retained history.

The direct Alternaria-versus-rest contrast on all 233 plants retained (E=+0.0803) ((p=0.0004)). Alternaria therefore had disproportionate leverage on identity-free architecture, but it was not the sole source: significant rank-abundance memory remained after all Alternaria-history plants were removed.

### Alternaria-associated history was concentrated more strongly in dominance than in lower-rank structure

Across all five histories, rank-1 dominance retained (E=+0.1759) ((p=0.0002)), while the normalized structure of ranks 2–5 retained (E=+0.1258) ((p=0.0005)).

After removing Alternaria, dominance retention declined to (E=+0.0895) ((p=0.0241)) and lower-rank retention to (E=+0.0862) ((p=0.0252)). Alternaria deletion leverage was therefore (+0.0865) for dominance and (+0.0396) for the lower-rank tail.

The full-panel binary history test independently showed the same structure. For Alternaria versus the other four histories, rank-1 dominance retained (E=+0.1181) ((p=0.0002)), whereas the normalized lower-rank tail retained (E=+0.0472) ((p=0.0316)). The frozen contrast was (Delta E_{mathrm{dominance-tail}}=+0.0709).

Alternaria-history plants had a mean rank-1 share of 0.778 and median 0.793, compared with 0.711 and 0.713 among the other histories. These identity-free statistics do not identify which fungal taxon occupied rank 1 in any individual plant.

### The dominance shift was broadly shared across host genotypes

The Alternaria-associated dominance shift was positive in 11 of 12 host genotypes. The equal-genotype-weighted mean Alternaria-minus-Other difference in rank-1 dominance was +0.0610 ((p=0.0001)), with median +0.0714.

Model decomposition showed that the genotype-shared binary-history component accounted for (R^2=0.1353) ((p=0.0001)), whereas the additional genotype-specific interaction component accounted for (R^2=0.0342) and was not unusually large relative to the frozen randomization null ((p=0.7548)). The shared component represented 79.8% of the observed total binary-history sum of squares.

All five East genotypes and six of seven West genotypes showed positive contrasts descriptively. Thus the dominance-centered Alternaria signature was not principally generated by one or two host backgrounds.

## Discussion

### Historical contingency is target specific, not a single system-level quantity

Priority-effects research has traditionally asked whether arrival history changes a community, a function, or an ecosystem property. That framing remains necessary, but our results show why it is incomplete. In both independent experiments, the same manipulated history was strongly detectable in one present-state description and weak or close to null in another measured on the same experimental units. The phenomenon is therefore not simply that one system has “strong” priority effects and another has “weak” priority effects. Historical contingency can be redistributed across properties of the present.

This distinction matters because prior work already shows that assembly-history effects need not attenuate monotonically with ecological level. Fukami et al. (2010) demonstrated large history-dependent differences in wood decomposition, and Dickie et al. (2012) found little support for universal attenuation from species or community responses to ecosystem properties. Our results are consistent with that literature and do not propose an attenuation law. Instead, they show that within a given manipulated history, different present-state targets can retain very different amounts of the historical signal. The relevant question is therefore not whether higher-level variables necessarily erase history, but which variables preserve which aspects of it.

### The same compositional history can be stored in different structural coordinates

The identity-stripping analysis provides the cleanest evidence for a deeper distinction. By sorting each composition vector while preserving every abundance value and the number of response dimensions, we removed ecological identity without replacing a multivariate target with a scalar one.

In the microbiome, this operation left retained history essentially unchanged. Arrival history had altered the shape of the abundance distribution strongly enough that the identities of the fungi were unnecessary for distinguishing histories. In the grassland, by contrast, most historical retention vanished after functional-group labels were removed. Here, the dominant historical signature was largely the assignment of biomass positions to forbs, grasses, and legumes.

We therefore use “storage channel” as a descriptive term for the structural component of the present state in which history remains distinguishable. The microbiome is architecture-rich: history persists in unlabeled dominance and evenness structure. The grassland is more identity-rich: much of the signal depends on which functional group occupies each abundance position. These are not proposed as universal community types. They are empirical descriptions of two experiments that demonstrate why historical contingency cannot always be summarized by a single endpoint or by a single compositional effect size.

### Prospective falsification prevented a convenient mechanism from becoming the story

A major risk in storage-style analyses is that a transformation chosen after inspecting the outcome can be given a compelling ecological interpretation even when the transformation itself induces separation. That risk became concrete in the first-arriver-role analysis.

The role-aligned transformation initially appeared to explain the cross-system contrast: the microbiome showed a very large signal after aligning communities by the first-arriving fungus, whereas the grassland did not. Yet the transformation used treatment labels to choose a response coordinate. Complete enumeration of equally complex placebo mappings showed that the biologically correct mapping was not special. It was near the middle of the microbiome ensemble and last in the grassland ensemble.

This negative result is central rather than peripheral. It shows that the storage-channel result survives a failed mechanism hypothesis, while the proposed explanation does not. It also illustrates a general principle for analyses in which responses are re-expressed using treatment information: biological specificity should be demonstrated against transformations with the same mathematical flexibility before mechanistic interpretation is assigned.

### In the microbiome, the strongest historical leverage is dominance centered

After rejecting the role-mapping mechanism, the subsequent prospective chain localized a narrower and more defensible pattern. Alternaria history had the largest leave-one-history-out leverage on identity-free rank-abundance memory. That leverage was more strongly concentrated in rank-1 dominance than in the normalized structure of lower ranks, and the same dominance-centered structure was recovered with a direct Alternaria-versus-rest history contrast on the full panel.

The dominance signal was also broadly shared across host genotypes. Eleven of twelve genotype-specific contrasts were positive, and approximately four fifths of the observed binary-history sum of squares was captured by the genotype-shared component rather than by additional genotype-specific interaction.

This does not mean that Alternaria alone generates microbiome historical memory. The remaining four histories retained significant architecture memory after Alternaria was removed, and the lower-rank tail retained history both with and without Alternaria. The appropriate interpretation is therefore heterogeneous leverage: historical storage is distributed across arrival histories, but one history contributes disproportionately to a broadly shared dominance signature.

### Dominance leverage is not the same as an exceptionally strong species-specific priority effect

Reconciliation with the source study places an important limit on interpretation. Leopold and Busby (2020) reported that Alternaria had the greatest relative abundance across treatments, but its own species-specific benefit from arriving early was relatively modest. Only three of the five early colonists consistently benefited from pre-emptive colonization.

The EOG result should therefore not be rewritten as “Alternaria has the strongest priority effect.” A history level can have large leverage on final community dominance even when the focal species' own early-arrival log-ratio is not the largest. Alternaria-first history may interact with a species that is already intrinsically competitive, occupy a distinct niche, alter competitors, alter the host environment, or combine several of these processes.

This distinction separates a **structural legacy** from a **mechanistic effect size**. The former describes how strongly a randomized history changes a present structural feature. The latter asks how and why a particular early colonist changes its own performance or the performance of others. The current data resolve the first but not the second.

### The present archive has a hard mechanistic ceiling

The current microbiome archive cannot distinguish the main mechanisms that could generate the Alternaria-associated dominance shift. Amplicon sequencing provides relative composition rather than absolute fungal population sizes. No pairwise growth or competition matrix, reduced-community interaction experiment, or host-response trajectory between inoculations is archived. The second community time point is not a clean later assembly state because the source analysis explicitly excluded it after rust reads overwhelmed the community data during pathogen sampling.

Consequently, the same observed increase in relative dominance could arise because the dominant fungus expanded absolutely, because competitors declined, because total fungal load changed, because the host was modified, or because several of these processes occurred together. Additional transformations of the final relative-abundance table cannot separate those possibilities.

The next mechanistic experiment should therefore measure process directly. Useful designs would include absolute taxon abundance through assembly, pairwise or reduced-community arrival-order manipulations, host-response measurements between inoculation events, or clean pre-pathogen temporal sampling. Such data could discriminate intrinsic growth advantage, competitor suppression, niche pre-emption, niche modification, and host-mediated effects.

### Implications for studying ecological history

The broader implication is methodological only in service of a biological point: studies of historical contingency should distinguish the existence of an historical effect from the present-state variable in which that effect is retained. Measuring one endpoint can make a community appear historically contingent while another endpoint makes the same experimental history appear nearly erased. Likewise, community composition can preserve history through different structural components in different systems.

This perspective complements, rather than replaces, mechanistic priority-effects theory. Niche pre-emption and niche modification remain candidate processes explaining how early arrivals alter later assembly (Fukami 2015), and microbiome research has emphasized the importance of scale, host context, and species identity in generating priority effects (Debray et al. 2022). The storage perspective identifies the phenotype of historical contingency that such mechanisms must explain.

For restoration, microbiome management, and other applied settings, this distinction is consequential. If a historical intervention is evaluated only by total biomass, host disease, or another aggregate response, a persistent compositional legacy may be missed. Conversely, strong compositional divergence does not imply that every function or spatial state remains equally history dependent. Choosing a monitoring endpoint is therefore also choosing which part of ecological history is observable.

## Conclusion

Across two independent randomized assembly experiments, the same kind of historical perturbation was retained unevenly across present ecological states. Community composition preserved strong history while another ecological state was close to its randomized baseline in each system. Removing ecological identity then showed that the compositional legacy itself was stored differently: strongly in unlabeled abundance architecture in the microbiome and much more in identity-to-abundance assignment in the grassland.

A plausible role-based mechanism failed a complete placebo-mapping audit, and the subsequent microbiome analyses localized the strongest history-level contribution to a broadly host-genotype-shared, dominance-centered Alternaria legacy. The archive does not reveal the interaction process that generates that pattern.

The main result is therefore structural rather than mechanistic:

> **Assembly history is not stored in one universal feature of the present. Different communities can retain the same kind of past perturbation in different components of present organization, and identifying that storage channel is logically prior to assigning a mechanism.**

## Data and code availability

All analyses use publicly available source data from the original experiments and versioned analysis code in the EOG repository. Source files were pinned by repository commit and, where used in scoring pipelines, by file-level blob identity.

The analysed plant-microbiome source data and code are archived with the source repository in Zenodo: **https://doi.org/10.5281/zenodo.3872145** (v1.2); the original amplicon reads are deposited under NCBI BioProject **PRJNA605581**. The grassland source data and code are archived in Zenodo: **https://doi.org/10.5281/zenodo.5713397**.

The complete EOG analysis code, frozen protocols, machine-readable result summaries and CI provenance are publicly available at **https://github.com/zuizui0223/eog**. A permanent DOI for the exact submission release should be minted before journal submission and inserted here.

## References cited in this draft

Alonso-Crespo, I. M., Weidlich, E. W. A., Temperton, V. M., & Delory, B. M. (2023). Assembly history modulates vertical root distribution in a grassland experiment. *Oikos*. https://doi.org/10.1111/oik.08886

Debray, R., Herbert, R. A., Jaffe, A. L., Crits-Christoph, A., Power, M. E., & Koskella, B. (2022). Priority effects in microbiome assembly. *Nature Reviews Microbiology*, 20, 109–121. https://doi.org/10.1038/s41579-021-00604-w

Dickie, I. A., Fukami, T., Wilkie, J. P., Allen, R. B., & Buchanan, P. K. (2012). Do assembly history effects attenuate from species to ecosystem properties? A field test with wood-inhabiting fungi. *Ecology Letters*, 15, 133–141. https://doi.org/10.1111/j.1461-0248.2011.01722.x

Fukami, T. (2015). Historical contingency in community assembly: integrating niches, species pools, and priority effects. *Annual Review of Ecology, Evolution, and Systematics*, 46, 1–23. https://doi.org/10.1146/annurev-ecolsys-110411-160340

Fukami, T., Dickie, I. A., Wilkie, J. P., Paulus, B. C., Park, D., Roberts, A., Buchanan, P. K., & Allen, R. B. (2010). Assembly history dictates ecosystem functioning: evidence from wood decomposer communities. *Ecology Letters*, 13, 675–684. https://doi.org/10.1111/j.1461-0248.2010.01465.x

Leopold, D. R., & Busby, P. E. (2020). Host genotype and colonist arrival order jointly govern plant microbiome composition and function. *Current Biology*, 30, 3260–3266.e5. https://doi.org/10.1016/j.cub.2020.06.011

Weidlich, E. W. A., Nelson, C. R., Maron, J. L., Callaway, R. M., Delory, B. M., & Temperton, V. M. (2021). Priority effects and ecological restoration. *Restoration Ecology*, 29, e13317. https://doi.org/10.1111/rec.13317

## Figure legends

## Figure 1. Where assembly history remains visible in the present

Conceptual framework for the storage problem. A manipulated assembly history can remain
distinguishable in different descriptions of the final system, including ecological
identity (which taxa or functional groups are abundant), identity-free abundance
architecture (the distribution of abundance among ranks), and downstream host, spatial or
aggregate states. The two empirical benchmarks use the same logic in different systems:
fungal arrival history is compared across final microbiome composition and host rust state,
whereas plant functional-group arrival history is compared across shoot composition and
belowground root distribution. “Storage” is used descriptively: a present-state target
retains history when randomized assembly histories remain distinguishable in that target
after the experimental design structure is respected.

## Figure 2. Assembly history is retained unevenly across present-state targets

Observed nested partial history (R^2) values are shown relative to their frozen
design-respecting randomization baselines. Horizontal pale intervals show the 2.5–97.5%
range of the permutation null, vertical ticks show the null median, and circles show the
observed partial (R^2). Retained-history excess is
(E=R^2_{observed}-median(R^2_{null})); permutation (p)-values are diagnostic tail
fractions under the frozen randomization contract. **A**, Plant microbiome: fungal
community composition retains substantial arrival-history information
((E=+0.1467), (p=0.0001)), whereas plant-level rust lesion state measured on the same
plants is close to its null baseline ((E=+0.0153), (p=0.3893)). Treatment labels were
permuted within host genotype. **B**, Grassland: final shoot functional-group composition
retains a very strong arrival-history signal ((E=+0.8034), (p=0.0001)), whereas the
six-layer root-biomass distribution retains little signal beyond its blocked null
((E=+0.0344), (p=0.3765)). History labels were permuted within replicate block. Each
analysis used 9,999 frozen permutations.

## Figure 3. Removing ecological identity reveals contrasting storage channels

Each line connects the same system before and after ecological identity is removed while
preserving the exact abundance multiset, experimental units, response dimensionality and
history model. “Labeled composition” retains the taxon or functional-group attached to
each abundance; “identity-stripped rank abundance” sorts those same values from largest to
smallest within each experimental unit. The y-axis is null-calibrated retained-history
excess (E). In the microbiome, identity stripping leaves the history signal essentially
unchanged (labeled (E=+0.1467); rank-abundance (E=+0.1486); 101.3% of labeled excess
retained). In the grassland, rank abundance retains only 24.3% of the labeled-composition
excess (labeled (E=+0.8034); rank-abundance (E=+0.1949)). Open circles show Shannon
entropy as a secondary label-invariant scalar sensitivity (microbiome (E=+0.2523);
grassland (E=+0.3800)). The universal prediction that compositional memory would be
identity based in both systems was prospectively refuted.

## Figure 4. Falsification and localization of the microbiome structural legacy

**A**, Specificity audit of the treatment-indexed first-arriver-role transformation.
Circles mark the biologically correct history-to-coordinate mapping; open squares and
triangles show the median and maximum (R^2) among equally complex incorrect mappings.
The correct mapping ranks 53/120 in the microbiome ((p_{map}=0.442)) and 6/6 in the
grassland ((p_{map}=1.000)). Here (p_{map}) is an exact finite
transformation-specificity fraction, not a causal randomization (p)-value. **B**,
Prospective leave-one-history-out leverage in the microbiome. For history (h),
(D_h=E_{full}-E_{-h}); positive values indicate that removing that randomized history
weakens identity-free rank-abundance memory. Alternaria has the largest positive leverage
((+0.0611)). **C**, Direct Alternaria-versus-rest component test on the full 233-plant
panel. Rank-1 dominance retains more null-calibrated history
((E=+0.1181), (p=0.0002)) than the normalized lower-rank tail
((E=+0.0472), (p=0.0316)); (Delta E=+0.0709). **D**, Within-host-genotype
Alternaria-minus-Other differences in rank-1 dominance. Eleven of 12 genotypes are
positive; the dashed line marks the equal-genotype-weighted mean contrast
(+0.0610), and the solid line marks zero. The genotype-shared component accounts for
79.8% of the observed binary-history sum of squares. Panels B–D localize a
dominance-centered structural legacy but do not identify the interaction mechanism that
produces it.
