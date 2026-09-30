# Target-specific identifiability in biogeography: when unresolved BAM mechanisms still support robust ecological decisions

**Running headline:** Target-specific BAM identifiability

## Abstract

1. **Ecological systems can be mechanistically ambiguous without being decision-ambiguous.** In species biogeography, the Biotic–Abiotic–Movement (BAM) framework represents a realised distribution as the intersection of abiotic suitability, biotic permissibility and movement accessibility. The forward mapping is many-to-one: multiple BAM worlds can reproduce the same current distribution. Existing work on structural uncertainty and partial identification shows broadly that unresolved models need not prevent useful prediction or decision-making. What remains unclear in BAM inference is how to distinguish mechanism, counterfactual and decision identifiability while making the dependence on the declared world universe explicit.

2. **We formulate target-specific identifiability over occurrence-conditioned finite BAM survivor fibers.** For a declared target \(T\), current evidence identifies the target when every surviving BAM world lies in one \(T\)-equivalence class. We derive an exact evidence-burden ordering under target coarsening and a monotonicity rule for nested world-universe expansion. We then test the framework in 12 preregistered known-truth BAM systems comprising 768 truth cases, using both idealised axis-release probes and three prospectively frozen ecological transformations. A structured universe expansion increases each system from 64 to 2,592 BAM parameter worlds; an unrestricted same-distribution decomposition closure provides a logical stress-test envelope.

3. **Mechanism, forecast and decision identifiability separated sharply.** Under complete current presence/absence, the BAM state was identified in only 25/768 cases, whereas all three idealised binary release decisions were jointly identified in 636/768. Among 743 mechanism-nonidentified cases, 462 retained disagreement in at least one exact counterfactual map while agreeing on all three binary decisions. Target-specific direct-measurement burden never exceeded the burden for a finer target. Under structured climate, biotic-stress and barrier-restoration transformations, binary decisions were identified in 646, 603 and 744 cases in the original 64-world universe and in 636, 498 and 700 cases after expansion to 2,592 worlds. One expanded climate fiber contained 36 parameter worlds with an identical current BAM state but two future maps and two binary loss outcomes, demonstrating dormant parameter reactivation.

4. **The relevant inferential endpoint is therefore target- and universe-specific.** A unique current mechanism is neither generally necessary nor always sufficient for a future ecological conclusion. We propose reporting a target certificate together with its declared world universe, evidence burden and nested-universe erosion profile. The framework does not replace model selection or adaptive management; it provides a BAM-specific exact accounting of which occurrence-compatible explanations disagree about the ecological target that matters.

**Keywords:** biogeography; counterfactuals; decision robustness; equifinality; identifiability; model uncertainty; species distributions; structural uncertainty

## Data/code for peer review

All protocols, frozen result summaries, exact finite-state implementations and benchmark scripts are versioned in the associated repository. The present manuscript uses only synthetic known-truth systems; no named-species empirical data are analysed. A double-anonymous review bundle should be generated from a frozen repository snapshot before submission.

## 1. Introduction

Species-distribution inference serves at least two distinct purposes. One is descriptive or predictive: where can a species occur, and how might its range change? The other is mechanistic or decision-oriented: which ecological constraints generated the observed distribution, which of those constraints matter under a perturbation, and what evidence would change a management-relevant conclusion? These questions are often treated as if resolving the upstream mechanism were a prerequisite for resolving the downstream decision. That implication is not generally valid.

The Biotic–Abiotic–Movement (BAM) framework provides a useful setting in which to make the distinction explicit. In geographical space, a realised distribution can be represented as the intersection

\[
G=A\cap B\cap M,
\]

where \(A\) denotes abiotic support, \(B\) biotic permissibility and \(M\) movement accessibility (Soberón & Peterson, 2005; Barve et al., 2011). BAM is established forward theory, and dynamic BAM formulations already model changes in niche, interactions and movement through time (Soberón & Osorio-Olvera, 2023). Virtual species and known-truth causal configurations are likewise established tools for evaluating distribution models (Saupe et al., 2012). The contribution here is therefore not the BAM decomposition itself, dynamic distribution modelling, or simulation with known truth.

The inverse BAM problem is different from the forward one. Given a realised distribution, multiple combinations of \(A\), \(B\) and \(M\) can produce the same \(G\). Ecological equifinality is not a new observation: distinct mechanisms can generate indistinguishable patterns, and multiple-working-hypothesis approaches explicitly warn against selecting a single process when the data do not distinguish among alternatives (Yanco et al., 2020; Lotterhos et al., 2022). Likewise, statistical partial-identification theory distinguishes the set of structural models compatible with observations from lower-dimensional targets that may be more tightly identified, and systems-biology work shows that useful predictions can remain possible when parameters are poorly identified. Adaptive-management and Value-of-Information frameworks similarly ask whether structural uncertainty actually changes the preferred action. Thus our aim is not to rebrand these general principles as new ecology.

Instead, we ask a narrower biogeographic question. Suppose current occurrence evidence leaves a finite set of BAM worlds compatible. Which of those worlds disagree about a specific ecological target? How much additional evidence is required to resolve the target rather than the complete mechanism? And how does that target certificate change when the admissible BAM world family itself is expanded?

This distinction matters because an occurrence-conditioned survivor set can be mechanistically heterogeneous while being homogeneous for a declared target. For example, several combinations of niche, biotic constraint and accessibility may reproduce the same current range but agree that removing a barrier produces no range gain. In that case, identifying which mechanism is historically correct adds no information to that binary target. Conversely, worlds that are indistinguishable under current conditions may diverge after a future perturbation if dormant parameter differences become active. Current-state identification can therefore be either unnecessarily strong or unexpectedly weak, depending on the target.

We develop an exact finite-world framework for this problem. First, we define target equivalence over the BAM worlds that survive current evidence. Second, we show that, under a common evidence library, the minimum evidence burden cannot increase when the inferential target is coarsened. Third, we make world-family dependence explicit: expanding the declared universe can preserve or destroy a target certificate but cannot resolve disagreement that was already present. Fourth, we quantify universe-boundary sensitivity at two levels: an unrestricted same-\(G\) decomposition closure and a preregistered ecological parameter neighbourhood. Finally, we replace idealised axis-release targets with structured climate, biotic-stress and barrier-restoration transformations.

The study uses an existing preregistered known-truth BAM benchmark: 12 activation-qualified heterogeneous finite landscapes and 768 truth cases. We do not add systems after inspecting the target-identifiability results. The analysis was developed in sequential frozen phases; refuted preregistered hypotheses are retained rather than repaired. Our questions are:

1. Can a BAM mechanism remain unidentified while a counterfactual ecological target is identified?
2. Does a coarser decision target require less evidence than an exact future map or full mechanism state?
3. How rapidly do target certificates erode as the BAM world universe is expanded?
4. Do the same conclusions persist under structured ecological transformations rather than only idealised axis deletion?
5. Can a future perturbation reactivate parameter differences that are invisible in the complete current BAM state?

## 2. Materials and Methods

### 2.1 Finite BAM worlds and current survivor fibers

Let \(X\) be a finite set of geographical nodes. A BAM parameter world \(w\in W\) contains an abiotic set \(A_w\subseteq X\), a biotic set \(B_w\subseteq X\), a movement-accessibility set \(M_w\subseteq X\), movement first-arrival state \(\tau_w\), and the parameter labels used to generate these states. Its realised current distribution is

\[
G_w=A_w\cap B_w\cap M_w.
\]

The present study conditions on complete perfect current presence/absence, denoted evidence level E1 in the parent benchmark. For truth world \(w_*\), the exact current survivor fiber is

\[
S_1(w_*)=\{w\in W:G_w=G_*\}.
\]

A survivor is compatible with the evidence inside the declared universe; survival is not interpreted as historical truth.

The parent deterministic panel contains 12 independently generated systems: six 7×3 and six 9×5 landscapes, spanning closed-barrier and one-gap configurations. Each system contains 64 BAM parameter worlds formed from two A states, four B interaction modes and eight M states. All 12 systems passed preregistered response-free activation gates before scoring, yielding 768 eligible truth cases. We reuse this frozen panel without replacement or tuning.

### 2.2 Four distinct identifiability targets

For any mapping

\[
T:W\rightarrow\mathcal Y,
\]

define target equivalence by

\[
w\sim_Tv \iff T(w)=T(v).
\]

The target is identified under current evidence when it is constant over the survivor fiber:

\[
|T(S_1)|=1.
\]

We distinguish four objects.

**Parameter-world identity.** The exact declared parameter world, including parameter distinctions that may be inactive under current conditions.

**Current BAM-state identity.** Equality of current \(A\), \(B\), \(M\) and complete movement-arrival state \(\tau\).

**Exact counterfactual-map identity.** Equality of the complete future occupied set under a declared transformation \(F\).

**Binary decision identity.** Equality of a coarser decision function \(D=d\circ F\), such as whether a transformation produces range gain or loss.

Parameter identity is the finest target. Exact future map and binary decision form a deterministic refinement chain,

\[
\text{parameter world}
\rightarrow
\text{exact future map}
\rightarrow
\text{binary decision}.
\]

Current BAM state is deliberately not inserted into this chain because a future transformation can depend on latent parameter distinctions that are inactive in the current state.

### 2.3 Exact target-specific evidence burden

Let \(S\) be a current survivor fiber, \(w_*\in S\) the known truth, and \(T\) the declared target. Worlds whose target differs from truth are

\[
N_T=\{w\in S:T(w)\neq T(w_*)\}.
\]

The finite direct-measurement library includes node-level A, B, M-accessibility and movement-arrival measurements. Given the truth outcome, each measurement \(m\) eliminates a finite subset \(D_m\subseteq S\). A measurement set \(Q\) is sufficient for target \(T\) when

\[
N_T\subseteq \bigcup_{m\in Q}D_m.
\]

We solve exactly for the minimum cardinality

\[
b(T)=\min\{|Q|:N_T\subseteq\cup_{m\in Q}D_m\}.
\]

The optimization is a finite set-cover/hitting-set problem; that algorithmic formulation is established prior art. Here it is used only after the BAM survivor fiber and target-discordant set have been defined.

If target \(U\) is finer than \(T\), so that \(T=f\circ U\), then \(N_T\subseteq N_U\). Under the same evidence library,

\[
b(T)\leq b(U).
\]

We preregistered and audited the hierarchy

\[
b(\text{binary decision})
\leq
b(\text{exact counterfactual map})
\leq
b(\text{full BAM state})
\]

for idealised release targets.

### 2.4 Idealised BAM release probes

The first target-identifiability benchmark used three mechanism probes:

\[
F_A(w)=B_w\cap M_w,
\]

\[
F_B(w)=A_w\cap M_w,
\]

\[
F_M(w)=A_w\cap B_w.
\]

The corresponding binary target asks whether the released map contains any node outside current \(G\). These are finite mechanism probes, not literal management interventions.

For each truth and probe we recorded exact-map class count, binary-decision class count, target identification status and minimum direct-measurement burden. No new landscape or truth case was added after scoring.

### 2.5 Unrestricted same-\(G\) completion and logical flip margin

Target identification is conditional on the declared world family. To expose this dependence, define the complete same-current-distribution decomposition closure

\[
\mathcal C(G)=\{(A,B,M):A\cap B\cap M=G\}.
\]

For every proper \(G\subset X\), both binary outcomes can be constructed for each single-axis release. Thus no nontrivial release decision is identified from \(G\) alone without restrictions on admissible BAM decompositions.

We define Hamming distance across all A/B/M node states and calculate the minimum distance from any target-identified survivor to an opposite-decision same-\(G\) completion. This logical completion flip margin is a stress-test measure, not an ecological plausibility score.

For an expansion decision, every node in the released support outside \(G\) is a witness, and every witness must be removed to reverse the decision. For a no-expansion decision, reversal requires constructing only one new outside-\(G\) witness. Closed-form margins were exhaustively checked against brute-force enumeration in all three-node BAM states before use in the 768-truth panel.

### 2.6 Structured ecological universe expansion

The unrestricted completion envelope intentionally admits biologically incoherent BAM states. We therefore preregistered an intermediate ecological parameter neighbourhood \(W_1\) that exactly embeds the original 64-world family \(W_0\).

For A, the original narrow and broad niche-radius levels were expanded by one linear radius step on either side while retaining the frozen common niche center. For B, the original four interaction-mode combinations were retained, while partner and antagonist ranges each received one 4-neighbour erosion level, the frozen baseline and one dilation level. For M, the two declared movement radii and horizons were supplemented with one larger movement-radius level and one extra-long horizon; barrier permeability remained the original closed/open binary factor.

This yields 2,592 parameter worlds per system. For a given current E1 fiber, only expanded worlds satisfying the exact same \(G\) are eligible. Ecological parameter distance is unit-weight Manhattan distance in the preregistered coordinates

\[
(A,\;P_{req},\;A_{exc},\;P_{range},\;A_{range},\;D,\;Barrier,\;H).
\]

The minimum distance to an opposite-decision same-\(G\) expanded world is the structured ecological expansion margin.

### 2.7 Nested-universe target monotonicity

For fixed evidence \(e\) and nested world universes

\[
W_0\subseteq W_1,
\]

the compatible sets satisfy

\[
S(e;W_0)\subseteq S(e;W_1).
\]

Therefore, for any fixed target \(T\),

\[
T(S(e;W_0))\subseteq T(S(e;W_1)).
\]

Adding admissible worlds can preserve or destroy target identification, but cannot remove already-existing target disagreement. We report target-identification counts across the original world family, the structured ecological expansion and, for the idealised probes, complete logical same-\(G\) closure.

### 2.8 Structured ecological counterfactuals

To test whether target-specific identifiability depends on axis deletion, three transformations were frozen before implementation.

**Climate shift.** Each node's synthetic environmental state was shifted by temperature +0.08 and moisture −0.04. Each world's niche center and radius were held fixed and A was recomputed; B and M were unchanged. The binary target is net range loss, defined by fewer occupied nodes than current \(G\).

**Biotic stress.** The world's current partner range received one additional 4-neighbour erosion, and its antagonist range one additional dilation. Interaction-mode bits were unchanged; A and M were fixed. The binary target is strict range loss.

**Barrier restoration.** M was recomputed with the world's same dispersal radius and time horizon but barrier permeability forced to true. A and B were fixed. The binary target is range gain outside current \(G\).

These transformations are synthetic fixtures. The climate shift is not an emissions scenario, the associate-range operations are not demographic forecasts and forced permeability is not a calibrated restoration project.

The transformations were evaluated in both \(W_0\) and \(W_1\), each filtered to exact current \(G\).

### 2.9 Pre-implementation protocol amendment and dormant aliases

Before implementation or outcome scoring, we recognized that exact future outcomes need not be functions of current BAM-state equivalence. A transformation may use a parameter distinction that was inactive under present conditions. The protocol was therefore amended before implementation to separate

\[
\theta\rightarrow C_{current}(\theta)
\]

from

\[
\theta\rightarrow F(\theta)\rightarrow D(\theta).
\]

A dormant alias activation occurs when two parameter worlds share the complete current BAM state but differ in exact or binary counterfactual outcome. The amended preregistered benchmark explicitly tested whether such a fiber exists.

### 2.10 Preregistration and fail-closed rules

Each development phase was committed before its implementation and scoring. The Phase-V protocol amendment was also committed before implementation or outcome access and records the reason for changing the target hierarchy. Refuted hypotheses were retained; in particular, a preregistered directional-margin hypothesis in the structured universe expansion was refuted and no post-score operator was added to rescue it.

All numerical claims below are conditional on the frozen systems, world families, evidence library and transformations. The synthetic programme is explicitly stopped after the structured-counterfactual phase; additional synthetic perturbations are not added to improve apparent generality.

## 3. Results

### 3.1 Mechanism nonidentification did not imply decision nonidentification

Under complete current presence/absence in the original 64-world universe, full current BAM state was identified in only

\[
25/768=3.3\%
\]

of truth cases.

The idealised release targets were much more frequently identified. The joint exact signature of all three release probes was identified in 174/768 cases, and all three binary release decisions were simultaneously identified in 636/768.

Among the 743 BAM-state-nonidentified truths:

- 149 were invariant across all three exact release maps;
- 462 retained disagreement in at least one exact release map but agreed on all three binary decisions;
- 132 retained at least one binary decision disagreement.

Thus 611/743 mechanism-nonidentified truths agreed on every frozen binary release decision.

### 3.2 Coarser targets required no more direct evidence

Across every truth and idealised release probe,

\[
b(\text{binary})
\leq
b(\text{exact map})
\leq
b(\text{BAM state}),
\]

with zero violations across 2,304 truth-by-probe comparisons.

Full BAM-state identification required a median of two direct node measurements and as many as four. In contrast, most binary release decisions were already identified without any additional measurement: 652/768 for release A, 705/768 for release B and 732/768 for release M.

Strict savings in measurement burden relative to full BAM-state identification occurred in 730/768 A-release cases, 738/768 B-release cases and 741/768 M-release cases.

### 3.3 Logical same-\(G\) completion exposed the conditional nature of decision certificates

For every proper \(G\subset X\), unrestricted same-\(G\) decomposition closure contained both binary release outcomes. Thus every nontrivial release certificate can be broken if the BAM world universe is expanded far enough.

The distance to the nearest logical reversal was nevertheless heterogeneous. Among proper-\(G\) decisions identified in \(W_0\), median Hamming completion margins were 1 for release A and 2 for releases B and M. Maxima were 13, 29 and 31 respectively.

No-expansion conclusions were especially close to a logical counterexample: every finite no-expansion margin was 1 or 2. Expansion conclusions could be much farther from reversal because all existing outside-\(G\) witnesses had to be removed.

### 3.4 Most target certificates survived the preregistered ecological neighbourhood

Logical fragility did not imply fragility inside the structured ecological expansion.

Binary release identification eroded as follows:

| Target | Original \(W_0\) | Ecological \(W_1\) | Complete \(\mathcal C(G)\) |
|---|---:|---:|---:|
| Release A | 652 | 646 | 34 |
| Release B | 705 | 693 | 34 |
| Release M | 732 | 691 | 34 |

Thus \(W_1\) retained 99.1%, 98.3% and 94.4% of the corresponding \(W_0\) certificates.

Structured same-\(G\) counterexamples were rare. Only 6 A-release truth cases, 12 B-release cases and 41 M-release cases acquired opposite decisions in the preregistered 2,592-world neighbourhood. At the unique-fiber level these represented only 1/119, 3/124 and 5/126 originally identified fibers respectively.

The preregistered hypothesis that expansion-true conclusions would show larger median structured margins than expansion-false conclusions in at least two targets was refuted. Finite A and B counterexamples all originated from no-expansion decisions, whereas finite M counterexamples all originated from expansion decisions. No new operator was introduced after this result.

### 3.5 Structured ecological transformations preserved target-specific identifiability

The climate, biotic-stress and barrier-restoration transformations reproduced the central separation without relying on axis deletion.

In \(W_0\), exact parameter-world identity was achieved in only 13/768 truth cases and current BAM state in 25/768. Yet:

| Transformation | Exact future map identified | Binary decision identified |
|---|---:|---:|
| Climate shift | 622 | 646 |
| Biotic stress | 558 | 603 |
| Barrier restoration | 604 | 744 |

Thus parameter-world nonidentification coexisted with binary decision identification in 633 climate, 590 biotic-stress and 731 barrier-restoration cases.

### 3.6 World-universe expansion removed target certificates without eliminating target usefulness

In \(W_1\), no truth case had a unique parameter world and only 8/768 identified the complete current BAM state. Nevertheless, binary decisions remained identified in 636 climate, 498 biotic-stress and 700 barrier-restoration cases.

Expansion from \(W_0\) to \(W_1\) removed:

- 10 of 646 climate binary certificates;
- 105 of 603 biotic-stress certificates;
- 44 of 744 barrier-restoration certificates.

Retention was therefore 98.5%, 82.6% and 94.1% respectively.

Exact-map identification showed a different erosion pattern: climate 622→610, biotic stress 558→442 and barrier restoration 604→604. Barrier restoration therefore lost binary certificates even though no previously exact future-map certificate was lost: the affected \(W_0\) fibers were already exact-map ambiguous but agreed on the coarser gain/no-gain target.

### 3.7 A dormant current-state alias reactivated under climate shift

One \(W_1\) fiber provided a direct counterexample to the idea that identifying the complete current BAM state necessarily identifies future response.

In system S11_9x5_gap, the current \(G\) contained 29 nodes. The same-\(G\) \(W_1\) fiber contained 36 parameter worlds but only one complete current \(A/B/M/\tau\) state. Under the frozen climate transformation, these worlds split into two exact future maps and two binary net-loss outcomes.

Thus

\[
C_{current}(\theta_1)=C_{current}(\theta_2)
\]

did not imply

\[
F_{climate}(\theta_1)=F_{climate}(\theta_2).
\]

The parameter difference was dormant under present conditions and active under the counterfactual.

## 4. Discussion

### 4.1 Identifiability should be defined for the ecological target, not inherited from the mechanism

The main result is not that ecological mechanisms are uncertain. Nor is it the general decision-theory observation that competing models can recommend the same action. Both are established. The BAM-specific result is that the exact occurrence-conditioned survivor fiber can be partitioned differently depending on whether the target is the current mechanism, an exact future distribution or a decision threshold.

This distinction is operational. A non-singleton mechanism fiber is not automatically a reason to collect more data. If every survivor lies in the same decision-equivalence class, additional mechanism discrimination cannot change that declared decision. Conversely, identifying the current BAM state is not automatically sufficient if future response depends on parameter distinctions that the current state does not express.

The relevant statement is therefore conditional: current evidence identifies target \(T\) within world universe \(W\). That sentence contains both the inferential target and the model-universe boundary that makes the claim meaningful.

### 4.2 Target-specific evidence design gives a principled stopping rule

The exact evidence-burden result formalizes a simple but important stopping principle. Under a common truth-consistent evidence library, any design that distinguishes all worlds at a finer target is sufficient for a coarser target, but the reverse need not hold.

For BAM inference, the practical consequence is that measuring A, B or M merely to identify a complete mechanism can waste effort if the ecological target is already invariant. The benchmark frequently found large savings: in more than 95% of truth cases for each idealised release target, the binary decision required strictly fewer direct measurements than complete BAM-state recovery.

This is not a new set-cover algorithm or a general theory of Value of Information. Its role is narrower: once the BAM inverse fiber is explicit, the nuisance worlds are exactly those that disagree with the declared target, and evidence design can ignore surviving aliases that cannot change it.

### 4.3 World-universe semantics are part of the result

Phase III and IV show why a finite-world certificate should not be reported without its universe semantics. Unrestricted same-\(G\) completion always destroys nontrivial single-axis release identification, but the first preregistered ecological parameter expansion preserved most certificates.

These are not contradictory conclusions. The complete decomposition closure asks whether any logically possible same-\(G\) BAM state can reverse the target. The structured lattice asks whether a counterexample exists within a specific, preregistered ecological neighbourhood. Robustness therefore has an erosion profile rather than one absolute status.

The exact monotonicity rule provides a simple audit: as admissible worlds are added while evidence is fixed, target disagreement can appear but cannot disappear. This suggests reporting nested universes explicitly—such as core declared models, prespecified ecological expansions and a worst-case logical envelope—rather than hiding model-family sensitivity behind one ensemble average.

### 4.4 Logical proximity and ecological proximity are different

A striking feature of the results is the contrast between logical and structured margins. Many release decisions were one A/B/M bit from an opposite logical completion, yet very few acquired a counterexample in the 2,592-world ecological lattice.

This means that a small combinatorial change in latent state is not equivalent to a small ecological change in parameter space. A useful robustness statement must specify the expansion operator and metric. Hamming completion provides a worst-case logical boundary; ecological-lattice distance provides sensitivity to a declared family of coherent perturbations. Neither is a probability that the counterexample is true.

This distinction is particularly important when model-set expansion is itself a scientific choice. Recent adaptive-management work similarly emphasizes that candidate model sets can be structurally incomplete and that expanding the effective model set can change robust decisions. Our framework complements rather than replaces that literature by locating the issue inside the occurrence-conditioned BAM inverse fiber.

### 4.5 Structured transformations show that the result is not an artefact of axis deletion

The structured climate, interaction and barrier transformations preserve the central pattern: parameter worlds were almost never uniquely identified, yet many future binary targets were. The amount of target erosion under \(W_1\) differed strongly among transformations, with the synthetic biotic-stress target most sensitive in this benchmark.

We do not interpret this as a universal ranking of abiotic, biotic and movement uncertainty. The transformations have different geometries and were not calibrated to real taxa. The useful conclusion is methodological: target robustness must be evaluated for the transformation actually relevant to the question. Results from one counterfactual cannot be transferred automatically to another.

### 4.6 Dormant aliases separate present-state inference from future-response inference

The climate example reveals a deeper boundary. Two parameter worlds can be identical in the complete current BAM state yet differ under intervention. This occurs when the intervention activates a parameter distinction that is currently silent.

The distinction is familiar in dynamical systems more broadly, but its consequence for BAM inference is concrete. Current-state reconstruction and counterfactual prediction are different projections of the parameter world. Unless the future transformation is proven to factor through the current state, identifying \(A\), \(B\), \(M\) and current movement timing is not necessarily enough to identify the future target.

This also changes experimental design. If the scientific objective is a future intervention, evidence should be chosen to separate worlds that disagree under that intervention, not necessarily worlds that differ in current-state variables.

### 4.7 Relation to partial identification and adaptive management

Partial-identification theory already asks what functionals are identified when the structural model is not, and adaptive management has long quantified whether structural uncertainty changes decisions. Our contribution is not to duplicate those theories.

The specific object here is an exact finite BAM survivor fiber conditioned by occurrence evidence. BAM provides mechanistically interpretable A, B and M state components; the inverse construction preserves every occurrence-compatible world rather than fitting one weighted compromise. Target equivalence is then evaluated directly on this same fiber, and nested universe expansions show exactly which added biogeographic worlds destroy a certificate.

The method is therefore best understood as an interface between inverse biogeographic inference and decision-focused model uncertainty: it tells the analyst which BAM explanations are still alive, which of them matter for the declared target and how sensitive that agreement is to the definition of the model universe.

### 4.8 Limitations and next empirical boundary

All numerical results are synthetic and conditional. The 12 landscapes were designed to activate A, B and M contrasts, not to represent a probability distribution over real ecosystems. The 64- and 2,592-world universes are finite design objects, not claims about the complete ecological hypothesis space. The climate delta, associate-range shells and barrier restoration are synthetic transformations.

For that reason, synthetic operator proliferation is now stopped. The next substantive validation should not add further deltas or parameter levels after seeing these results. It should define one ecological transformation independently of the focal BAM outcome—for example from an external climate product, documented interaction perturbation or independently specified restoration scenario—and then apply the same target- and universe-specific identifiability audit prospectively.

Observation error is also simplified here because the target study conditions on complete current \(G\). The broader EOG joint-world framework can include observation-process worlds, but doing so here would mix a separate uncertainty axis into a study whose purpose is to isolate target and world-family dependence. Extending target identifiability to ecological × observation-process universes is therefore a future problem rather than an unreported sensitivity analysis.

### 4.9 Conclusions

A realised species distribution can leave its ecological mechanism deeply unresolved without leaving every ecological conclusion unresolved.

In finite BAM worlds, the correct inferential question is not simply whether the generating process has been identified. It is whether the BAM worlds still compatible with current evidence agree on the ecological target that matters. Coarser targets can require substantially less evidence than full mechanism recovery; target certificates can survive substantial structured expansion of the world family; and those same certificates can disappear when the admissible universe is broadened further.

The framework also exposes the opposite danger: a complete current mechanism state need not identify a future response if dormant parameter aliases are activated by intervention.

We therefore recommend reporting BAM inference as a target-specific, universe-conditional certificate:

\[
(\text{evidence},\;W,\;T)
\rightarrow
\text{identified / unresolved target}
\]

together with the target-specific evidence burden and, where possible, an explicit universe-expansion audit. This shifts the goal from forcing one historical explanation to determining exactly which ecological conclusions the surviving explanations do and do not support.

## References

Atkinson, A.C. & Cox, D.R. (1974). Planning Experiments for Discriminating between Models. *Journal of the Royal Statistical Society: Series B* 36:321–334. https://doi.org/10.1111/j.2517-6161.1974.tb01010.x

Barve, N., Barve, V., Jiménez-Valverde, A., Lira-Noriega, A., Maher, S.P., Peterson, A.T., Soberón, J. & Villalobos, F. (2011). The crucial role of the accessible area in ecological niche modeling and species distribution modeling. *Ecological Modelling* 222:1810–1819. https://doi.org/10.1016/j.ecolmodel.2011.02.011

Beale, C.M., Brewer, M.J. & Lennon, J.J. (2014). A new statistical framework for the quantification of covariate associations with species distributions. *Methods in Ecology and Evolution* 5:421–432. https://doi.org/10.1111/2041-210X.12174

Beven, K. & Freer, J. (2001). Equifinality, data assimilation, and uncertainty estimation in mechanistic modelling of complex environmental systems using the GLUE methodology. *Journal of Hydrology* 249:11–29. https://doi.org/10.1016/S0022-1694(01)00421-8

Bolam, F.C., Grainger, M.J., Mengersen, K.L., Stewart, G.B., Sutherland, W.J., Runge, M.C. & McGowan, P.J.K. (2019). Using the Value of Information to improve conservation decision making. *Biological Reviews*. https://doi.org/10.1111/brv.12471

Elith, J. & Leathwick, J.R. (2009). Species Distribution Models: Ecological Explanation and Prediction Across Space and Time. *Annual Review of Ecology, Evolution, and Systematics* 40:677–697. https://doi.org/10.1146/annurev.ecolsys.110308.120159

Lotterhos, K.E., Fitzpatrick, M.C. & Blackmon, H. (2022). Simulation Tests of Methods in Evolution, Ecology, and Systematics: Pitfalls, Progress, and Principles. *Annual Review of Ecology, Evolution, and Systematics* 53:113–136. https://doi.org/10.1146/annurev-ecolsys-102320-093722

Manski, C.F. (2007). Partial identification of counterfactual choice probabilities. *International Economic Review*. https://doi.org/10.1111/j.1468-2354.2007.00467.x

Metcalf, C.J.E. et al. (2014). Seven challenges in modeling vaccine preventable diseases. *PLOS Biology* 12:e1001970. https://doi.org/10.1371/journal.pbio.1001970

Rozowski, C. & Fackler, P.L. (2025). Adaptive management under structural uncertainty: A linear opinion pool approach to expanding the model set. *Methods in Ecology and Evolution* 16:1992–2009. https://doi.org/10.1111/2041-210X.70137

Saupe, E.E., Barve, V., Myers, C.E., Soberón, J., Barve, N., Hensz, C.M., Peterson, A.T., Owens, H.L. & Lira-Noriega, A. (2012). Variation in niche and distribution model performance: The need for a priori assessment of key causal factors. *Ecological Modelling* 237–238:11–22. https://doi.org/10.1016/j.ecolmodel.2012.04.001

Soberón, J. & Nakamura, M. (2009). Niches and distributional areas: Concepts, methods, and assumptions. *Proceedings of the National Academy of Sciences* 106(Suppl. 2):19644–19650. https://doi.org/10.1073/pnas.0901637106

Soberón, J. & Osorio-Olvera, L. (2023). A dynamic theory of the area of distribution. *Journal of Biogeography* 50:1037–1048. https://doi.org/10.1111/jbi.14587

Soberón, J. & Peterson, A.T. (2005). Interpretation of models of fundamental ecological niches and species' distributional areas. *Biodiversity Informatics* 2. https://doi.org/10.17161/bi.v2i0.4

Williams, B.K., Eaton, M.J. & Breininger, D.R. (2011). Adaptive resource management and the value of information. *Ecological Modelling*. https://doi.org/10.1016/j.ecolmodel.2011.07.003

Yanco, S.W., McDevitt, A., Trueman, C.N., Hartley, L. & Wunder, M.B. (2020). A modern method of multiple working hypotheses to improve inference in ecology. *Royal Society Open Science* 7:200231. https://doi.org/10.1098/rsos.200231
