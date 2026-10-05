# Original EOG cost-information value — v17 result

## Result

All eight preregistered hypotheses were supported.

This closes the synthetic measurement-cost subseries.

Authoritative execution:

- workflow run: `37211149304`;
- job: `111462442951`;
- artifact: `11307510794`;
- artifact digest:
  `sha256:03cf1747b2874968b67e8a3d41ce222f8f54666aaba0e73b5af92abbe015c369`;
- result fingerprint:
  `02a86be67dd2fdfa50eb3b6ac94d587269871933d218b016a9728396832248d4`.

## Perfect cost-world information always had value

Across 144 random-topology rows × 6 ecological targets = **864 row-targets**:

- zero perfect-information value: **0**;
- negative information value: **0**.

The mean perfect-information value across the six target classes was approximately
**2.02 synthetic cost units**.

This quantity is also the exact break-even cost of a hypothetical perfect calibration
step under the frozen minimax-regret definition.

## One bit of cost information was often enough

The three frozen binary diagnostics asked whether REL, FP or KO was the expensive
measurement family.

Across all row-targets:

- positive best-binary value: **836/864**;
- one binary diagnostic recovered all perfect-information value: **783/864**;
- every binary diagnostic remained incomplete: **81/864**.

So coarse cost information often recovered nearly all of the value of knowing the
entire cost world, but not universally.

## Which diagnostic mattered was target dependent

Canonical best diagnostic counts:

- `is_FP_expensive`: **834**;
- `is_KO_expensive`: **16**;
- `is_REL_expensive`: **14**.

The dominance of FP is strong but not universal, and the amount of value captured by
one bit varied by ecological target.

Mean fraction of perfect-information value captured by the best binary diagnostic:

- pairwise relation: **0.962**;
- first passage: **0.972**;
- intervention: **0.920**;
- critical-node count: **0.853**;
- full topology identity: **0.962**;
- joint relational suite: **0.962**.

The critical-node target was the least compressible with one-bit cost information:
27/144 rows retained positive residual regret under every binary diagnostic.

## Scientific meaning

v15 showed that the optimal ecological measurement path changes when measurement costs
change.

v16 showed that if the cost world is unknown, every row-target pays irreducible
cross-cost regret.

v17 now shows that learning the cost world has an exact positive value, and often only
coarse information about which measurement family is expensive is enough to recover
most or all of that value.

The evidence-design object is therefore:

```text
surviving ecological worlds
× ecological target
× ecological measurement outcomes
× measurement-cost uncertainty
× optional cost-world information
```

But this is now a closed synthetic subseries.

## Stop rule

Do not add:

- a fifth cost world;
- another post-result cost ratio;
- another binary cost diagnostic;
- an arbitrary synthetic calibration price.

The next virtual-world question must return to an unresolved ecological property of
EOG rather than extending the cost model.
