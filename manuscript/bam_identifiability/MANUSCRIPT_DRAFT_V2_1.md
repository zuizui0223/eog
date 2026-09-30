# Distributions are lossy intersections: exact identifiability limits for abiotic, biotic and movement mechanisms

## Abstract

Species distributions are often interpreted as evidence about the abiotic, biotic and movement processes that generated them, yet the inverse problem is not guaranteed to be identifiable. We formulate finite BAM inference as a partial-identification problem in which each candidate world has abiotic support A, biotic permissibility B, movement accessibility M and realised distribution G = A ∩ B ∩ M. Under complete positive occurrence evidence, the exact survivor set is the worlds satisfying G* ⊆ G; under complete perfect presence/absence it is the worlds satisfying G = G*. Thus even a complete realised distribution can fail to identify its BAM decomposition. More strongly, when one truth support is nested inside another, its compatible-world set is necessarily equal or larger, so stronger ecological restriction can increase ambiguity under positive-only inference.

We tested these statements in preregistered known-truth simulations. Across 12 activation-qualified deterministic BAM systems and 768 truth cases, complete positive occurrence maps uniquely identified 0/768 BAM states. Progressive evidence increased unique recovery to 25/768 with complete realised distributions, 159/768 with occupied-node arrival times, 275/768 after direct abiotic evidence, 565/768 after direct biotic evidence and 768/768 after direct movement-accessibility evidence. An independently implemented stochastic generator reproduced truth retention and positive-superset logic while refuting stronger expectations that every structural difference must realise a positive witness and that unordered accumulated occurrence history must outperform the final snapshot. Across 304/304 strict support-inclusion pairs, narrower positive support retained equal or more compatible worlds. First-occurrence timing nevertheless refined static support in 256/384 stochastic runs.

The inferential object is therefore not a selected “true process” but an evidence-dependent fiber of compatible BAM worlds. Distinguishing the remaining alternatives is an exact finite hitting-set problem; within the frozen deterministic programme, at most one direct A measurement, two B measurements, three joint A+B measurements or two M-accessibility measurements were required. This reframes distribution-to-process inference from best-model selection toward explicit non-identification and targeted evidence design.

## 1. Introduction

Species distributions are commonly used to reason backward from pattern to process. Observed ranges motivate claims about climatic tolerance, dependence on interacting species, dispersal limitation and geographic barriers. The Biotic–Abiotic–Movement (BAM) framework makes the forward logic explicit: realised distribution depends jointly on abiotic conditions, biotic permissibility and accessibility (Soberón & Peterson, 2005; Soberón & Nakamura, 2009). In its simplest finite-set form,

$$
G = A ∩ B ∩ M.
$$

BAM is therefore naturally generative. Given A, B, M and an initial condition, one asks what distribution follows. Dynamic BAM theory has extended this logic to explicit movement, niche-tolerance and biotic-interaction processes, and has already emphasized that movement and niche effects can become difficult to disentangle (Soberón & Osorio-Olvera, 2023). Virtual-species studies likewise use known causal configurations to evaluate ecological niche and distribution models (Saupe et al., 2012).

The inverse problem is different. Given an observed distribution, which combinations of A, B and M are actually identified? The same realised intersection can be produced by multiple decompositions. A missing site can reflect abiotic unsuitability, absence of a required partner, presence of an antagonist, inaccessibility, or several constraints acting together. Conversely, a positive site only shows that all necessary conditions were jointly satisfied there. It does not reveal which mechanism would have limited occurrence elsewhere.

This many-to-one problem is an ecological instance of a broader equifinality and pattern-to-process problem. Distinct mechanisms can generate indistinguishable observable patterns, and simulation-based method evaluation has repeatedly shown that good fit need not imply unique process identification (Yanco et al., 2020; Lotterhos et al., 2022). Our contribution is therefore not the generic claim that ecological mechanisms can be non-identifiable. We ask the narrower BAM-specific inverse question: for explicit evidence types, what is the exact finite set of BAM worlds that remains compatible?

We treat this survivor set, or evidence fiber, as the primary inferential object. This formulation has three consequences. First, exact non-identification can be stated without arbitrary score thresholds. Second, different evidence types can be compared by how they contract the same survivor fiber. Third, remaining ambiguity can be converted into a diagnostic-measurement problem. Experiment design for discriminating among rival models is itself established statistical methodology (Atkinson & Cox, 1974) and is increasingly used adaptively in ecology (e.g. Papanikolaou et al., 2023); here, the BAM-specific contribution is to derive the survivor sets to which that design problem applies.

We address four questions:

1. What does complete positive occurrence evidence identify?
2. Does complete presence/absence recover the BAM decomposition?
3. Can stronger ecological restriction make inverse identification harder rather than easier?
4. Which additional evidence is sufficient to break the remaining ambiguity?

We answer these questions with exact finite-set identities and a preregistered known-truth simulation programme. The deterministic generality panel contains 12 activation-qualified heterogeneous BAM systems and 768 truth worlds. We then challenge the results with an independently implemented stochastic BAM generator, a temporal-evidence analysis and an eight-landscape stochastic panel in which failed activation systems remain DESIGN_STOP rather than being repaired or replaced.

## 2. Theory

### 2.1 Finite BAM worlds

Let X be a finite node universe and W a declared finite candidate-world set. Each world w ∈ W has:

- abiotic support A_w ⊆ X;
- biotic permissibility B_w ⊆ X;
- movement accessibility M_w ⊆ X;
- movement first-arrival state τ_w;
- optional parameter labels θ_w.

The realised distribution is

$$
G_w = A_w ∩ B_w ∩ M_w.
$$

Let w* denote the generating truth. All conclusions below are conditional on the declared finite universe W and on the evidence semantics. A surviving world is compatible with the evidence; survival does not establish historical truth.

### 2.2 Complete positive occurrence evidence

Suppose every truly occupied node is observed and no absence information is available. A candidate survives iff it contains every observed positive:

$$
S_0(w*) = { w ∈ W : G* ⊆ G_w }.
$$

This yields the positive-superset ceiling. If G* ⊆ G_w, then no valid positive occurrence sampled from G* can eliminate w. The limitation remains even under complete positive sampling of G*.

### 2.3 Complete perfect presence/absence

If every node in X is surveyed perfectly, positive evidence gives G* ⊆ G_w and negative evidence gives G_w ⊆ G*. Therefore

$$
S_1(w*) = { w ∈ W : G_w = G* }.
$$

A complete distribution map identifies the realised G inside W. It need not identify which A, B and M produced G. Absence information within BAM is itself established prior work (Bariotakis & Pirintsos, 2018); the present point is the exact inverse fiber that complete absence information leaves.

### 2.4 Progressive evidence fibers

We condition the same survivor set on increasingly direct evidence:

$$
S_2 = { w ∈ S_1 : τ_w|_{G*} = τ*|_{G*} },
$$

$$
S_3 = { w ∈ S_2 : A_w = A* },
$$

$$
S_4 = { w ∈ S_3 : B_w = B* },
$$

$$
S_5 = { w ∈ S_4 : M_w = M* },
$$

$$
S_6 = { w ∈ S_5 : τ_w = τ* }.
$$

Hence

$$
S_6 ⊆ S_5 ⊆ S_4 ⊆ S_3 ⊆ S_2 ⊆ S_1 ⊆ S_0.
$$

Adding valid evidence can contract or preserve the survivor fiber but cannot restore a contradicted world.

### 2.5 BAM-state equivalence and parameter aliases

Two parameter worlds are BAM-state equivalent when A_w = A*, B_w = B*, M_w = M* and τ_w = τ*. At E6, the survivor set is exactly the BAM-state equivalence class of truth. Multiple parameter labels can therefore remain after the complete finite BAM state is identified. This separates distribution identification, BAM-state identification and parameter identification.

### 2.6 Restrictiveness and ambiguity

For a complete positive support R define

$$
C(R) = { w ∈ W : R ⊆ G_w }.
$$

If R_1 ⊂ R_2, every world containing R_2 also contains R_1. Therefore

$$
R_1 ⊂ R_2  ⇒  C(R_1) ⊇ C(R_2).
$$

A narrower positive support cannot have fewer compatible positive-superset worlds. Stronger ecological restriction can therefore increase, rather than decrease, ambiguity under positive-only inverse inference.

### 2.7 Targeted measurements as a finite hitting-set problem

Let S be the current survivor set and T ⊆ S the target fiber to retain. Each possible direct measurement m eliminates a finite subset D_m ⊆ S. A measurement set Q reproduces T exactly when it does not eliminate members of T and when

$$
S \ T ⊆ ⋃_{m ∈ Q} D_m.
$$

The minimum diagnostic design is therefore an exact finite hitting-set problem. The hitting-set algorithm is generic prior art; the BAM-specific contribution is the survivor fiber and disagreement structure that define the hitting-set instance.

## 3. Methods

### 3.1 Validation philosophy

All simulations used known generating truth. Within each stage, primary hypotheses, activation gates and terminal rules were frozen before scoring. Systems failing pre-scoring activation remained in the denominator as DESIGN_STOP; parameters, seeds and landscapes were not repaired or replaced after outcome inspection. The simulations test finite-world information limits rather than estimate real ecological parameter distributions.

### 3.2 Canonical finite-world benchmark

The initial benchmark first verified four logical operations: retaining truth under valid positive evidence; eliminating false worlds when positive witnesses exist; falsifying an omitted-truth finite universe when every candidate is contradicted; and remaining unresolved under observational equivalence. A larger 64-case factorial then tested the stronger hypothesis that complete positive occurrence coverage would recover the generating process.

### 3.3 Orthogonal BAM generation

The focal state was generated as G = A ∩ B ∩ M. A comprised two focal abiotic niche breadths. B comprised four interaction modes constructed from independently generated partner and antagonist virtual species. M comprised combinations of dispersal radius, barrier permeability and finite movement horizon. Before scoring, each system was required to contain A-only, B-only and M-only witness contrasts, at least one exact-G equivalence pair and at least one positive-superset/diagnostic-negative pair.

### 3.4 Deterministic 12-system generality panel

The deterministic panel contained 12 frozen systems: six 7×3 and six 9×5 landscapes, alternating closed barriers and middle-row barrier gaps, with deterministic local environmental heterogeneity indexed by seeds 0–11. No replacement was allowed. Each system contained 64 candidate BAM worlds: 2 A states × 4 B states × 8 M states. Partner and antagonist occupancy fractions were required to fall between 0.15 and 0.85, and all witness/equivalence activation gates had to pass before scoring.

For each eligible truth, we evaluated the fixed evidence ladder:

- E0: complete positive occurrence set;
- E1: E0 + complete perfect surveyed negatives;
- E2: E1 + exact arrival time on truth-positive nodes;
- E3: E2 + complete direct A state;
- E4: E3 + complete direct B state;
- E5: E4 + complete direct M accessibility;
- E6: E5 + complete direct first-arrival state.

The primary identification target was BAM-state equivalence, not parameter-label uniqueness. The preregistered generality claims included a universal 0% E0 uniqueness bound, a universal “M is the final bottleneck” claim, and targeted measurement bounds of at most three A+B nodes and at most two M-accessibility nodes.

### 3.5 Independent stochastic BAM challenge

To reduce dependence between generator and evaluator, the stochastic generator used NumPy and the Python standard library only and was prohibited from importing EOG reconstruction code. It operated on a 12×8, 96-node landscape with two environmental gradients, an environmental bottleneck at column 5, and a hard barrier between columns 6 and 7 with one gap.

Partner and antagonist species were independently simulated for 30 steps. Focal occupancy evolved stochastically within the structural A×B×M support for 40 steps. Colonization probability at an eligible unoccupied node was 1 − (1 − β)^k for k occupied accessible neighbors; persistence was stochastic and the focal source was retained. Positive occurrences were observed perfectly at horizons 5, 10, 20 and 40; absence was never used in this primary stochastic experiment.

The finite candidate universe contained 32 worlds: 2 A states × 4 B modes × 4 M modes. Six frozen truth scenarios were evaluated with 64 replicates each, for 384 planned runs. Seeds were SHA-256 functions of scenario and replicate. Associate degeneracy or source invalidity triggered DESIGN_STOP rather than replacement.

### 3.6 Restrictiveness–ambiguity audit

For every strict complete-support inclusion pair R_1 ⊂ R_2 in the stochastic candidate universe, we tested the exact implication C(R_1) ⊇ C(R_2). The frozen audit contained 304 strict support-inclusion pairs. Cardinality-based correlations were treated as descriptive only; set inclusion was the exact ordering.

### 3.7 Temporal positive evidence

The successor temporal analysis kept the same stochastic generator and runs but retained each observed node’s first-occurrence time. For each candidate world we computed the earliest structurally possible arrival t_min. A candidate remained compatible when t_min ≤ t_obs at every observed node. Earlier possible arrival did not falsify a candidate because stochastic colonization could be delayed; later possible arrival than an observed occurrence was impossible. Absence and extinction time were not used.

### 3.8 Multilandscape stochastic panel

Generality was challenged across eight preregistered 12×8 landscapes spanning open-smooth, barrier-gap, environmental-bottleneck and joint-fragmented structures. Each landscape had 32 candidate worlds, six truth scenarios and 32 replicates per truth, for 192 planned runs per landscape and 1,536 total planned runs. Landscape-specific associate degeneracy, invalid source, missing truth world or structural mismatch caused DESIGN_STOP. No replacement landscape was permitted.

### 3.9 Exact targeted-measurement audit

For the 12 deterministic systems and 768 truths, direct A, B, joint A+B, M-accessibility and M-arrival measurement design was solved exactly as a finite bit-mask hitting-set problem. The exact solver was audited against brute-force subset enumeration on small fixtures. Earlier greedy stagewise counts were not called minima until equality with the exact solver had been established.

## 4. Results

### 4.1 Complete positive occurrence did not identify generating BAM states

In the initial 64-case factorial, complete positive occurrence coverage uniquely identified the generating process in 0/64 cases. The same result generalized across the deterministic panel: 0/768 truth BAM states were uniquely identified at E0. Because E0 contained every true positive node, this failure cannot be attributed to insufficient positive sampling.

### 4.2 A, B and M were all independently informative, but their intersection remained non-identifying

All preregistered orthogonal BAM activation gates passed. A-only, B-only, M-only and multi-axis witness contrasts were all realized. Nevertheless, unique recovery in the canonical orthogonal system was 0/64 from complete positives, 2/64 after complete perfect negatives and 6/64 after adding occupied-node arrival time. The ambiguity therefore did not arise because B or M was omitted from the generative system.

### 4.3 The deterministic evidence ladder contracted ambiguity monotonically

Across 768 deterministic truths, unique BAM-state recovery was 0 at E0, 25 at E1, 159 at E2, 275 at E3, 565 at E4, and 768 at both E5 and E6. Information addition was monotone in all 12 systems. The preregistered universal claim that movement accessibility must always be the final identification bottleneck was refuted: at least one system reached complete BAM-state identification by E4 before direct M evidence.

### 4.4 Stronger ecological restriction increased positive-only ambiguity

The stochastic audit contained 304 strict positive-support inclusions and zero nesting violations. In every pair, the narrower support retained an equal-or-larger compatible-world set. The descriptive correlation between support size and compatible-world count was r = −0.672. The jointly constrained A+B+M truth had support size 33 and remained compatible with all 32 candidate worlds, whereas the distance- and barrier-limited truths each had support size 96 and only four compatible worlds.

### 4.5 Independent stochastic generation reproduced the core logic and refuted stronger expectations

Across 384 eligible stochastic runs, truth-retention failures, EOG/evaluator parity mismatches, positive-superset violations and omitted-truth witness-criterion mismatches were all zero. Unique truth recovery remained zero in every truth scenario at horizon 40.

Two stronger preregistered expectations failed. Structural difference did not guarantee a realized positive witness: the jointly constrained A+B+M truth produced complete positive support contained in every candidate reachable set. Unordered accumulated positive history also failed to show any strict discrimination gain over the final positive snapshot.

### 4.6 First-occurrence timing recovered information that unordered history lost

Retaining first-occurrence time refined eight static support classes into 20 temporal signature classes. Among 48 static M-equivalent pairs, 19 were split by temporal signature. Temporal evidence strictly contracted the compatible set in 256/384 stochastic runs. However, unique truth recovery remained zero in every scenario. Time therefore supplied genuinely new movement information without guaranteeing complete inverse identification.

### 4.7 The stochastic principles generalized across landscapes

Of eight preregistered landscapes, six passed activation gates and two joint-fragmented landscapes remained DESIGN_STOP. The six eligible landscapes contributed 1,152 stochastic runs. Truth retention, positive contraction, restrictiveness nesting and evaluator parity all held. Every eligible landscape contained temporal strict-gain runs, while at least one horizon-40 run remained non-identifiable under temporal positive evidence. The jointly constrained A+B+M scenario retained median compatible-world count 32 under both static and temporal evidence in every eligible landscape.

### 4.8 Exact diagnostic measurement requirements were small in the frozen deterministic programme

Across 768 truths, the exact maximum number of targeted direct measurements was one node for A, two for B, three for joint A+B and two for M accessibility. The joint A+B distribution was 206 truths requiring zero nodes, 323 requiring one, 191 requiring two and 48 requiring three. For M accessibility, 565 truths required zero nodes, 200 one node and three two nodes. Once M accessibility was known, no additional full-arrival measurement was required in this frozen programme.

## 5. Discussion

### 5.1 BAM is generative, but its inverse is partially identified

The BAM framework explains how ecological constraints generate a realised distribution. The inverse map is different because intersections lose information about which component excluded which nodes. General ecological equifinality is already well recognized (Yanco et al., 2020; Lotterhos et al., 2022). The BAM-specific contribution here is to make the inverse fiber exact for explicit evidence types.

### 5.2 Complete occurrence data are not complete process data

The 0/768 E0 result is not a sampling-effort result. Any positive-superset candidate containing all truth positives remains compatible by construction. Complete perfect presence/absence reduces the fiber to worlds with the same realised G, but G can still have multiple A/B/M decompositions.

### 5.3 Strong ecological restriction can make the inverse problem harder

The restrictiveness result is the most counterintuitive consequence of the positive-only fiber. A restrictive mechanism can shrink the realised distribution, yet a smaller positive support provides fewer possible witnesses against permissive alternatives. In the frozen stochastic universe this ordering held for all 304 strict support inclusions. Thus stronger ecological constraint can make mechanism inference less identifiable even while making the realised distribution more restricted.

### 5.4 Temporal ordering is evidence, not merely more occurrence

The stochastic programme separated unordered accumulation from time-stamped occurrence history. Unordered accumulation added no strict discrimination beyond the final snapshot, whereas first-occurrence time split movement-equivalent classes and contracted the survivor set in two thirds of runs. The important question is therefore not how many occurrences are collected but whether the evidence exposes a disagreement among surviving mechanisms.

### 5.5 Non-identification should be reported, not optimized away

When several BAM worlds occupy the same evidence fiber, selecting one best-fitting world does not create information. A faithful result is the unresolved fiber itself. This distinction matters whenever the scientific claim concerns mechanism rather than prediction.

### 5.6 Ambiguity can guide evidence collection

Once the survivor fiber is explicit, diagnostic measurement becomes a standard model-discrimination problem on a BAM-specific disagreement structure. Optimal experimental design itself is long-standing (Atkinson & Cox, 1974) and adaptive ecological design is not new (Papanikolaou et al., 2023). The contribution here is the mapping from BAM inverse ambiguity to the finite set of measurements that separate its surviving worlds. In the frozen deterministic programme, the exact designs were often small despite substantial global ambiguity.

### 5.7 EOG v3 is an implementation of the inverse logic

The EOG v3 joint-world engine generalizes the same bookkeeping. It keeps ecological and observation-process worlds separate, conditions their Cartesian product on evidence, projects the surviving uncertainty onto ecological and observation axes, and supports robust and adaptive evidence design over declared finite action libraries. This software consolidates the inverse-fiber logic; it is not the primary novelty claim of this paper.

### 5.8 Limits

All exact statements are conditional on finite declared world and evidence universes. The simulations do not imply that real A, B, M or movement states are directly observable without error. Perfect negatives and direct mechanism measurements are idealized evidence contracts used to establish information boundaries. The numerical targeted-measurement bounds are properties of the frozen simulation programme, not universal constants. A surviving world is evidence-compatible, not certified historical truth.

## 6. Conclusion

A species distribution is a compressed outcome of multiple ecological processes. Treating it as if it uniquely records those processes confuses the forward and inverse problems. In finite BAM worlds, complete positive occurrence evidence identifies a positive-support fiber, complete presence/absence identifies the realised intersection G, and only evidence that exposes disagreements among surviving worlds can identify finer BAM state.

The same logic yields a practical consequence. Residual ambiguity is not merely a limitation to report; it defines which observations would be diagnostic. The inverse problem can therefore be reframed from selecting the most plausible single process to characterizing what the current evidence actually distinguishes and designing the next measurement around what remains unresolved.

## Core references

Atkinson, A.C. & Cox, D.R. (1974). Planning Experiments for Discriminating between Models. Journal of the Royal Statistical Society: Series B 36:321–334. DOI: 10.1111/j.2517-6161.1974.tb01010.x.

Bariotakis, M. & Pirintsos, S.A. (2018). Mapping absences within the BAM concept: Towards a new generation of ecological and environmental indicators. Ecological Indicators 90:564–568. DOI: 10.1016/j.ecolind.2018.03.043.

Lotterhos, K.E., Fitzpatrick, M.C. & Blackmon, H. (2022). Simulation Tests of Methods in Evolution, Ecology, and Systematics: Pitfalls, Progress, and Principles. Annual Review of Ecology, Evolution, and Systematics 53:113–136. DOI: 10.1146/annurev-ecolsys-102320-093722.

Papanikolaou, N.E. et al. (2023). Adaptive experimental design produces superior and more efficient estimates of predator functional response. PLOS ONE 18:e0288445. DOI: 10.1371/journal.pone.0288445.

Saupe, E.E. et al. (2012). Variation in niche and distribution model performance: The need for a priori assessment of key causal factors. Ecological Modelling 237–238:11–22. DOI: 10.1016/j.ecolmodel.2012.04.001.

Soberón, J. & Nakamura, M. (2009). Niches and distributional areas: Concepts, methods, and assumptions. Proceedings of the National Academy of Sciences 106(Suppl. 2):19644–19650. DOI: 10.1073/pnas.0901637106.

Soberón, J. & Osorio-Olvera, L. (2023). A dynamic theory of the area of distribution. Journal of Biogeography 50:1037–1048. DOI: 10.1111/jbi.14587.

Soberón, J. & Peterson, A.T. (2005). Interpretation of Models of Fundamental Ecological Niches and Species' Distributional Areas. Biodiversity Informatics 2. DOI: 10.17161/bi.v2i0.4.

Yanco, S.W. et al. (2020). A modern method of multiple working hypotheses to improve inference in ecology. Royal Society Open Science 7:200231. DOI: 10.1098/rsos.200231.