# EOG v2 ecological traversability synthetic confirmation result

## Status

The frozen prospective synthetic confirmation defined by `benchmarks/traversability_confirmation_contract.json` was executed without changing the confirmation seeds or gates after outcome inspection.

Authoritative workflow run: `31693122698`.

- head: `a682d95ffab69d43de350c07f245129a12b08232`;
- artifact: `9178210087`;
- artifact digest: `sha256:26d7613b3dd9ca72e47d1c53640faa77c255a3e77865b163a709ca5ce5103a19`;
- contract fingerprint: `e40dd8807a3ca51b3d228cf29ef6d8c9ee66caf4837dd29ec2e85479b34fb034`;
- result fingerprint: `bfd5afd87eff31a96a593ba8c579a7c5bdb0fdf63405d0792066a772efd43181`.

Frozen decision: **PASS**.

## Negative control: endpoint IBE truth

When the generating truth was already contained in endpoint environmental distance, endpoint viability and geographic distance, adding the full traversability feature set did not produce a spurious gain.

Mean held-out `R3 - R0` log-loss difference:

`+0.03352338011536377`

The predeclared retreat gate required the mean difference to be at least `-0.010`; it passed. The extra path features were therefore adverse rather than falsely promoted when endpoint information was sufficient.

## Path-discontinuity truth

Adding cumulative environmental crossing and maximum environmental bottleneck to the endpoint reference produced:

`mean R1 - R0 = -0.22701673339503556`

All `8/8` confirmation seeds were favourable. The predeclared gate was `<= -0.035` with at least `6/8` favourable seeds.

This confirms the intended estimand distinction: endpoint environmental similarity can omit information carried by the environmental states that must be traversed between endpoints.

## Niche-desert truth

Adding minimum intermediate viability and the niche-desert penalty beyond the endpoint + path-environment reference produced:

`mean R2 - R1 = -0.20248787721145578`

All `8/8` confirmation seeds were favourable. The predeclared gate was `<= -0.035` with at least `6/8` favourable seeds.

This confirms that environmental transition size and intermediate viability are distinct synthetic information sources.

## Long-jump truth

Adding the explicitly declared direct long-jump support beyond the continuous-path reference produced:

`mean R3 - R2 = -0.11232784525425349`

All `8/8` confirmation seeds were favourable. The predeclared gate was `<= -0.025` with at least `6/8` favourable seeds.

The result supports keeping continuous propagation and long-jump hypotheses separate rather than forcing both through one transit-viability rule.

## Claim boundary

This is **known-truth synthetic estimand confirmation**, not empirical validation and not evidence that EOG generally outperforms SDMs, IBD/IBE models, resistance/current-flow models, dynamic occupancy, or mechanistic spread models.

The result supports only the following prospective method statement:

> pathwise environmental discontinuity, explicit intermediate viability, and declared long-jump support can contain held-out information that is absent from an endpoint-only reference, while the added traversability features retreat when endpoint information already contains the generating truth.

No new empirical dataset should be searched merely to turn prior NO-GO results into positive evidence. The next development step is occurrence-conditioned comparison of candidate transition rules/histories, with a new contract frozen before any empirical promotion attempt.
