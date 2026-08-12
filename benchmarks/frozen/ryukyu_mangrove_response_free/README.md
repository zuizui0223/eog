# Frozen Ryukyu mangrove response-free predictors

These files are a byte copy of the response-free predictor artifact created **before** the published genetic response was attached to EOG v2.

Authoritative CI provenance:

- workflow run: `31610691970`;
- workflow head: `5a8449f51480dd127311a1befe0cae98e1272ce7`;
- artifact ID: `9147048185`;
- artifact name: `ryukyu-mangrove-response-free-genetic-predictors`;
- artifact digest: `sha256:23725655494ff7ba09fd764186a675e4f13190d92f0605e601d9b3cc4737a681`.

Frozen file identities:

- `populations.csv` SHA-256: `0edd135771e8339074b456a311efd02202d0309d81b539206160bad212236fb4`;
- `predictors.csv` SHA-256: `b5484727b4e690ef880384408a7283964ede593a788b093c74777886bec9851f`;
- predictor-manifest fingerprint: `8bef3ea334eb99610f04ac4eb38e411731b59649ac926f2b60278a732aad1449`;
- operator fingerprint: `61ba283a6d33cfd85fd3b187de88c47e154acd8da0c6c31082aca1c647219830`;
- exact-eventual connectivity fingerprint: `d026ca7a6f4a948ee465ab14b7419cdddea97943886d03ebc18b2429a63bdcfe`.

The files are archived rather than regenerated for published-response sensitivity analyses. This prevents later numerical implementation drift from changing the response-free predictors after the external genetic outcome has become visible.

The corresponding predictor construction is retrospective external validation infrastructure, not a new blinded confirmation. The strong current-flow values in this original artifact are retained exactly even if later numerical implementations would produce slightly different floating-point values; they are not recalculated to improve validation performance.
