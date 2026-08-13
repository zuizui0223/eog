# Frozen Ryukyu mangrove response-free predictors

These files are a byte copy of the response-free predictor artifact created **before** the published genetic response was attached to EOG v2.

Authoritative CI provenance:

- workflow run: `31610691970`;
- workflow head: `5a8449f51480dd127311a1befe0cae98e1272ce7`;
- artifact ID: `9147048185`;
- artifact name: `ryukyu-mangrove-response-free-genetic-predictors`;
- artifact digest: `sha256:23725655494ff7ba09fd764186a675e4f13190d92f0605e601d9b3cc4737a681`.

Frozen file identities, read directly from that archived artifact:

- `populations.csv` SHA-256: `6de60475209e49927c68d2467bdac253a0e2777c39a9f4df49dde4832ee3495e`;
- `predictors.csv` SHA-256: `b5485e42c8c884bf31f3d8b76fd71db04a93c377bc9836f085a4c65b6f62aa7f`;
- predictor-manifest fingerprint: `8bef3ea33d24f1f124aab5e023cbfac087f74b2e5584546b9da50adaf2de7d31`;
- operator fingerprint: `61b4794914976bd1ac5687fd814a2d2878d397a2feac02314031feb68c249e35`;
- exact-eventual connectivity fingerprint: `d0261069e634cb21068a45ff59c5bb891ce573ec9a6d01e75308b7b8e2215c38`.

The files are archived rather than regenerated for published-response sensitivity analyses. This prevents later numerical implementation drift from changing the response-free predictors after the external genetic outcome has become visible.

The corresponding predictor construction is retrospective external validation infrastructure, not a new blinded confirmation. The strong current-flow values in this original artifact are retained exactly even if later numerical implementations would produce slightly different floating-point values; they are not recalculated to improve validation performance.
