# Structural testability does not imply predictable contraction in finite ecological world sets

## Provisional title

Structural testability does not imply predictable contraction in finite ecological world sets

## Alternative titles

1. When structural adequacy cannot predict evidential contraction
2. An identifiability boundary for occurrence-conditioned ecological world sets
3. Testable before observation, unpredictable before placement: a boundary for finite-world ecological inference

## One-sentence claim

A finite ecological world universe can be certified as structurally testable before response access, yet the amount of later evidence-driven contraction is not generally identifiable from response-blind global graph structure because compatibility depends on where positive observations occur.

## Abstract

Finite sets of alternative ecological transition worlds provide an auditable way to represent uncertainty about accessibility without collapsing competing mechanisms into one fitted route. A remaining problem is whether the informativeness of such a declared world universe can itself be assessed before biological responses are opened. We separated two questions: structural adequacy, meaning whether a world family spans the graph scales required to make a claim testable, and survival regime, meaning whether later positive occurrence evidence falsifies all worlds, contracts the set, or leaves it saturated. We first developed a response-blind structural gate and a prospectively frozen three-state survival-regime rule. A first version failed before response access because graph-closure horizons made high-connectivity worlds survive by construction. We therefore froze a corrected one-transition rule, deduplicated identical adjacency operators, and tested it prospectively across 16 fixed sites from the NEON small-mammal trapping programme. All 16 sites were forecast to contract before response access. A once-only response query produced nine scorable sites and seven registry-mismatch stops. Only two of nine scored sites matched the frozen regime forecast; seven saturated, two contracted, and none falsified the entire world set. Exact-match frequency was 0.222, below the predeclared simple three-class reference of one third, and mean absolute error in surviving-world fraction was 0.417. Importantly, two sites showed genuine intermediate contraction, demonstrating that the finite-world formulation itself does not force endpoint outcomes. We then formalized the deeper limit. Under the one-step self-excluded positive-evidence rule, a world survives exactly when every positive node has a positive neighbour in the induced positive subgraph. Any nonempty, noncomplete undirected graph therefore admits both survival and failure for the same graph and the same number of positive nodes, depending only on their placement. Structural testability can thus be audited response-blindly, but later epistemic contraction is not generally identifiable from global graph structure alone without additional assumptions about response location.

## 1. Introduction

Ecological inference often distinguishes whether a location is locally suitable from whether it is reachable. Finite-world approaches make that distinction explicit by retaining several declared accessibility or transition worlds and asking which remain compatible with observed positive occurrences. The resulting compatible set is auditable: a later positive observation can eliminate declared worlds, preserve several alternatives, or falsify the entire finite universe. What remains unclear is whether that later contraction can itself be anticipated from the response-blind structure of the declared world set.

This question matters because a finite-world framework can be structurally valid yet empirically uninformative. If every declared world always survives, the update is saturated. If every world always fails, the declaration may be too restrictive at the relevant scale. A tempting solution is to tune thresholds until an intermediate number of worlds survives. That is not a legitimate confirmatory strategy because it uses the response to choose the world universe. The valid alternative is prospective: define adequacy using response-free structural criteria, freeze a regime forecast before outcome access, and then test whether the predicted contraction occurs.

We therefore separated structural adequacy from survival regime. Structural adequacy asks whether the declared world family contains the structural scales required to make the intended claim testable. Survival regime asks what happens after positive evidence is opened. These are different objects and must not share outcome-tuned thresholds.

The Environmental Occupancy Geometry framework provided the required infrastructure: response-blind graph audits, adequacy-complete scale ladders, exact finite-world reconstruction, positive-evidence contraction, deterministic fingerprints, and once-only response authorization. Previous EOG applications had shown both complete falsification and complete saturation, but no independently scored intermediate contraction. This raised two linked questions. First, are endpoint outcomes a property of the finite-world formulation itself? Second, can response-blind graph structure predict which regime will occur?

We addressed these questions in a preregistered NEON small-mammal programme and then derived the corresponding identifiability boundary. The empirical test rejected the frozen structure-only regime forecast while producing two genuine intermediate contractions. The theoretical result explains why a universal structure-only predictor cannot exist under the stated positive-evidence rule: world survival depends on the placement of positive nodes, not only on the global graph in which they are embedded.

## 2. Methods

### 2.1 Finite world sets and positive-evidence compatibility

Let W be a finite declared set of transition worlds on a common node universe. For a positive occurrence set O, the compatible world set is

W(O) = { w in W : every required positive occurrence is supported under w }.

World identities are retained for audit but are not treated as historical truth. Non-detection does not eliminate a world in the present programme.

The primary empirical regime uses only falsifiable worlds. A sentinel world that is defined prospectively to support every node cannot enter the survival denominator because doing so would make complete finite-universe falsification impossible by construction.

### 2.2 Structural adequacy before response access

For each response-blind node registry, we built a distance-threshold ladder targeting largest weak-component fractions of 0.25, 0.50, 0.75 and 0.90, with finite-node completion when required to make the declared criteria testable. Structural adequacy required at least one world with largest weak-component fraction at least 0.90 and isolated-node fraction at most 0.05.

Adequacy used no biological response values. Horizon reachability was deliberately excluded from the adequacy gate because it was reserved for the survival-regime forecast.

Exact duplicate adjacency operators were collapsed to one canonical world before survival fractions were calculated. Alias labels were retained for provenance but carried no additional denominator weight.

### 2.3 A failed pre-response v1 forecast

The first frozen regime rule used a structural horizon of n minus 1 steps. Before biological response access, response-blind execution revealed a degeneracy: in an undirected graph, n minus 1 steps reach an entire connected component. Any world whose largest component contains more than half the nodes therefore has median horizon reachability equal to its largest-component fraction and a horizon-realization ratio of one. Because the adequacy-complete ladder contains high-connectivity worlds, complete predicted falsification became structurally impossible. The v1 programme was stopped before response access and retained as a method falsification.

### 2.4 Frozen v2 one-transition regime forecast

The successor changed only two structural defects: the horizon was fixed to one admitted transition, and duplicate adjacency operators were deduplicated. The original cutoff was not retuned.

For each distinct falsifiable world w, we defined

H_w = median one-step reachable fraction / largest weak-component fraction.

A world was predicted to survive if H_w was at least 0.5. The system-level forecast was then:

- zero predicted survivors: falsified_universe;
- some but not all predicted survivors: contracting;
- all predicted survivors: saturated.

The 0.5 cutoff was frozen before any v2 candidate forecast or biological response access.

### 2.5 Prospective NEON validation

The empirical family was NSF NEON Small mammal box trapping, data product DP1.10072.001, RELEASE-2026. Candidate sites were selected response-blindly by site code order, with a maximum of 16 fixed sites. The individual mammal trap was the graph node. Trap locations and coordinates were frozen from NEON location metadata before biological response access.

The focal response was the NEON target-small-mammal species guild rather than a hand-picked focal species. Eligible taxa were defined from the response-blind SMALL_MAMMAL taxonomy endpoint using species rank and taxonProtocolCategory equal to target. Two species whose public capture-distribution counts were exposed during source-design work were excluded prospectively.

All 16 fixed sites passed the structural gate. Their v2 forecasts were frozen before response access. Every site was predicted to be contracting, with predicted surviving-world fractions from 0.25 to 0.667.

### 2.6 Once-only response access and integrity stops

Biological response access was authorized once. The final successful run used one authenticated frozen NEON data query, selected only mam_pertrapnight CSV files from RELEASE-2026 basic packages, verified checksums, and joined response rows to frozen trap nodes using the official namedLocation plus trapCoordinate rule.

The run consumed one authenticated query, 605 response files and 283,386,654 biological-response bytes. No statistical learner was fit.

A site was scorable only if it had at least two known target-positive nodes and no target-positive coordinate outside the frozen response-blind registry. Seven sites stopped after response consumption because positive rows contained trap coordinates absent from the frozen registry. Those sites were not repaired, replaced or assigned a regime.

### 2.7 Observed survival regime

For each canonical one-step world, every positive node was treated once as a target while all other positive nodes formed the peer-source set. A world survived if every positive target had at least one positive peer connected by an admitted edge.

Observed regime was classified from the surviving distinct falsifiable worlds:

- zero: falsified_universe;
- partial: contracting;
- all: saturated.

The primary endpoint was exact three-state regime match. A fixed simple reference of one third was reported because three labels were declared, while observed class prevalence was reported separately. Secondary endpoints were absolute error in surviving-world fraction and the empirical regime distribution.

### 2.8 Identifiability theorem

For an undirected adjacency graph G and positive-node set P, the one-step self-excluded rule is equivalent to

minimum degree of the induced subgraph G[P] is at least one.

For exactly two positives, compatibility is therefore equivalent to adjacency of the positive pair.

If G contains at least one edge and at least one non-edge, choose an adjacent pair as the positive set and the world survives. Choose a non-adjacent pair as the positive set and the world fails. G is unchanged, as are every graph-only summary and the number of positive nodes. Consequently world survival is not universally identifiable from response-blind global graph structure alone.

Synthetic exhaustive tests additionally verify that the same non-identifiability can occur at larger fixed positive-set cardinalities.

## 3. Results

### 3.1 The prospective regime forecast failed

All 16 fixed NEON sites were prospectively forecast as contracting. Nine sites were scorable after once-only response access. Only two matched the frozen prediction.

Observed regimes among scored sites were seven saturated, two contracting and zero falsified_universe. Exact-match frequency was 2/9 = 0.222. The one-sided binomial upper-tail probability relative to the fixed one-third reference was 0.857.

Mean absolute error in surviving-world fraction was 0.417. Mean observed survival fraction was 0.935, compared with a mean frozen forecast of 0.519. Every scored site had an observed survival fraction greater than its frozen forecast.

### 3.2 Intermediate contraction exists empirically

Two sites produced genuine intermediate contraction rather than an endpoint.

DELA retained 3 of 4 distinct falsifiable worlds, an observed survival fraction of 0.75. DSNY retained 2 of 3, an observed survival fraction of 0.667.

These observations reject the idea that the finite-world formulation itself mathematically forces complete falsification or complete saturation.

### 3.3 Saturation dominated the scored systems

Seven of nine scored sites saturated despite all nine having been forecast to contract. The saturated mismatches were ABBY, BARR, BLAN, CPER, DCFS, GRSM and GUAN.

The two exact matches were DELA and DSNY.

### 3.4 Seven fixed sites terminated on frozen registry mismatch

BART, BONA, CLBJ, DEJU, HARV, HEAL and JERC contained target-positive response rows whose trap coordinates were absent from the frozen response-blind node registry. These were terminal response-consumed integrity stops, not biological regime outcomes.

### 3.5 Global structure cannot generally identify later world survival

The two-positive witness establishes a structural impossibility result. In any nonempty, noncomplete undirected world graph, the same graph and same positive-set cardinality admit both world survival and world failure, depending only on positive-node placement.

Thus no deterministic graph-only function can universally recover later world survival under the declared one-step observation rule without additional assumptions about response location.

## 4. Discussion

The central result is a separation of structural testability from predictable epistemic contraction.

EOG can legitimately certify response-blind properties of a declared finite world universe: whether it contains sufficiently spanning structural scales, whether isolation criteria are testable, whether duplicate worlds exist, and whether the declaration is internally auditable. Positive observations can then eliminate worlds, preserve alternatives, or falsify the declared finite universe.

What cannot generally be certified from global structure alone is how much contraction will occur after the positive pattern is revealed.

The NEON validation shows this empirically. The frozen v2 rule systematically underpredicted world survival, with seven of nine scored sites saturating and every observed survival fraction exceeding its forecast. This is not a reason to search for a better cutoff on the consumed systems. The prospectively frozen hypothesis failed.

At the same time, the two intermediate NEON contractions are important. Earlier EOG applications had produced complete falsification or complete saturation, raising concern that finite-world updating might collapse to endpoints in practice. DELA and DSNY show that intermediate survival sets are empirically realizable. The failure therefore belongs to the structure-only forecasting hypothesis, not to the existence of contraction as an EOG state.

The theoretical witness explains the deeper issue. World survival is a property of the induced positive subgraph, not merely of the whole graph. Before the response is opened, global structural summaries do not tell us where positives will occur. Any attempt to forecast survival probabilistically must therefore add assumptions about positive-node placement, such as an occupancy distribution, source prior, environmental occurrence model, mechanistic colonisation model or explicit sampling distribution.

Those additions may be scientifically useful, but they define a different product. They cannot be described as pure response-blind structural adequacy.

The result sharpens the EOG boundary. Local suitability is not accessibility; accessibility is not realized distribution; realized positive evidence constrains but does not uniquely identify history. We now add a further distinction: structural testability is not predictable future contraction.

## 5. Relationship to the N1-N4 spine

This paper remains inside N3: WHERE can it become real?

N3 retains alternative accessibility worlds rather than collapsing realization to one route. The present result defines the inferential limit of that step. Before evidence, EOG can audit whether the alternative-world declaration is structurally testable. After evidence, it can report which worlds survive. But it cannot generally infer the future contraction state from global structure alone.

This boundary is compatible with the handoff to N4. Remaining uncertainty after world contraction can still inform where new observations would be most discriminating. The new result only forbids pretending that the amount of future contraction is already encoded in response-blind global graph structure.

## 6. Claim boundary

Supported:

- structural adequacy and later world survival are distinct inferential objects;
- the fixed NEON structure-only survival-regime rule failed prospectively;
- intermediate finite-world contraction occurred empirically;
- under the one-step self-excluded rule, graph-only structure does not universally identify later world survival;
- positive-node placement is required to determine compatibility in the general nontrivial case.

Not supported:

- a universal calibrated survival-regime predictor;
- retuning the consumed cutoff;
- a biological regime for any registry-mismatch site;
- taxon-level generalization from the guild-level NEON endpoint;
- causal interpretation of why a particular NEON site saturated;
- any change to the closed EOG-WF Layer-B conclusion;
- historical truth of any surviving world.

## 7. Figure plan

Figure 1. Structural adequacy versus evidence-driven survival.
Left: response-blind world construction and adequacy gate. Right: later positive observations induce falsification, contraction or saturation. The figure emphasizes that adequacy is a property of the declared world family, whereas survival is conditional on observed positive placement.

Figure 2. Prospective NEON validation.
Panel A: frozen predicted surviving-world fractions for the nine scored sites. Panel B: observed fractions on the same axis with a 1:1 reference. Panel C: observed regime counts, showing seven saturated and two contracting systems. Registry-mismatch sites are shown separately as integrity stops and are not assigned biological regimes.

Figure 3. Identifiability witness.
The same nonempty, noncomplete graph is drawn twice. In the first copy, the two positive nodes occupy the endpoints of an edge and the world survives. In the second, two non-adjacent nodes are positive and the world fails. Graph structure and positive-set size are identical; only placement changes.

## 8. Reproducibility anchors

Empirical closure:
validation/world_survival_regime_v2/neon_small_mammal_response_lock_v2_3.json

Programme closure:
validation/world_survival_regime_v2/neon_small_mammal_programme_closure_v2_3.json

Identifiability implementation:
src/eog/v2/world_survival_identifiability.py

Identifiability tests:
tests/test_world_survival_identifiability.py

Boundary document:
docs/world_survival_identifiability_boundary.md
