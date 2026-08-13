# EOG v2 occurrence-conditioned transition-rule compatibility result

## Status

The frozen synthetic confirmation defined by `benchmarks/occurrence_rule_compatibility_confirmation_contract.json` was executed once on the predeclared seed set without changing source policy, candidate rule construction, or gates after outcome inspection.

Authoritative workflow run: `31693738735`.

- head: `ea5ad5fb4e928f2fe5234000113070981c0ffbd7`;
- artifact: `9178446646`;
- artifact digest: `sha256:67fbe6b3b12439b0fb0879b56199c3729510cc7084af079bd417aa77e33a9137`;
- contract fingerprint: `cd792c4aa5f3e1e7cdd5b4d4b9e61be8d8f191d00733ff53eac5f0a16a7f29ba`;
- result fingerprint: `50ddb917312822ebafa5c2557633803654916533ce8532f5f9484737bfb0246a`.

Frozen decision: **PASS**.

## Fixed-source true chain

A prospectively declared ancestral source `A` was connected by a one-way chain to observed downstream occurrences `B`, `C`, and `D`.

Across all `8/8` confirmation seeds:

- fixed-source occurrence coverage = `1.0`;
- no downstream observed occurrence was unsupported.

This confirms that the compatibility diagnostic preserves a valid directional fixed-source history when the source anchor is known.

## Broken candidate rule

The broken rule removed the final transition needed to reach `D`.

Across all `8/8` seeds:

- fixed-source occurrence coverage = `2/3`;
- the disconnected observed target was unsupported.

This establishes the intended positive use of occurrence configuration: under a frozen node universe and source policy, observed occurrences can falsify or constrain a candidate transition rule that cannot support them.

## Over-permissive candidate rule

A fully connected rule also supported all observed occurrences:

- minimum fixed-source coverage = `1.0`;
- active-edge fraction = `1.0` versus `0.25` for the true chain;
- the minimum active-edge-fraction advantage over the true chain was `0.75`;
- mean outgoing transition mass was also higher for the permissive rule in every seed.

Therefore occurrence compatibility alone does **not** identify the generating rule. A rule can fit the occurrence pattern simply by being too permissive.

The API intentionally does not return a winner score or reward this permissiveness.

## Self-excluded peer-source boundary

For the same true one-way chain, self-excluded peer-source compatibility yielded:

- coverage = `0.75` in every seed;
- ancestral source `A` was the unsupported held-out target.

This is expected: descendants need not reach their ancestor in a directional colonisation history.

Therefore self-excluded compatibility is a source-uncertain mutual-reachability diagnostic, not a directional historical reconstruction method.

## Scientific consequence

This confirmation supports a narrower and more useful interpretation of the information hidden in occurrence records:

> occurrence configuration can constrain candidate reachability rules because some rules are structurally incapable of supporting observed states, but occurrence-only compatibility is insufficient to identify a unique historical transition process when multiple rules remain compatible.

This is the intended bridge from `occurrence = local viability label` toward `occurrence = viability + accessibility constraint` without overclaiming historical reconstruction.

## Next development gate

The next step should add **discriminating evidence** rather than make the compatibility rule more permissive or search more empirical datasets. Candidate sources include:

- independently surveyed non-detections/effort;
- known colonisation order;
- directional movement or dispersal observations;
- historical or extinct stepping-stone evidence;
- genetics used only as independent external validation;
- hypothesis-discriminating survey observations.

No frozen empirical NO-GO result is reopened by this synthetic confirmation.
