# EOG v2 implementation issue draft

See `docs/eog_v2_dynamic_island_reachability.md` for the full prospective concept.

Implementation order:

1. Dynamic archipelago simulator with known viability, dispersal and extinction truth.
2. `dynamic_island_reachability.py` implementing sub-stochastic graph propagation from training-only occurrence sources.
3. Node/edge outputs: reachability curve, arrival depth, source attribution, bottleneck, redundancy and route entropy.
4. Frozen comparator suite: SDM/support only, nearest source, IFM/source pressure, least-cost/resistance, circuit/current-flow, static EOG.
5. Synthetic neutral-genetic simulator and pairwise `D_eog` validation beyond IBD/IBE.
6. Independent empirical genetic validation without tuning EOG-R on genetic outcomes.
7. Separate method manuscript only if predeclared go/no-go criteria are met.

Hard rule: do not alter or rescue the frozen v0.1 manuscript outcomes.
