# Shared scaling contract benchmark result

## Decision

The frozen contract passed.

- maximum independent-span AUC deviation from chance: 0.124375;
- minimum shared-reference span AUC: 1.000;
- minimum matched-path tree-inefficiency AUC: 1.000;
- across-support path comparison performed: false;
- contract gate: passed.

## Breadth comparison

When compact and broad clouds were robust-scaled independently, broad-versus-compact span AUCs were:

- n=60: 0.4975;
- n=120: 0.375625;
- n=240: 0.5250.

This confirms that within-cloud scaling removes global dilation and that the frozen default `span` cannot be used as absolute comparative breadth.

With one predeclared external reference transformation, broad-versus-compact span AUC was 1.000 at n=60, 120, and 240. Shared-reference `span` therefore recovers comparative extent in the declared reference units.

## Tree comparison

Curved-versus-straight tree-inefficiency AUC was 1.000 at n=60, 120, and 240 when both generators used the same path-like support class, point count, coordinate units, and noise scale.

No compact-cloud-versus-path contrast was performed. This is intentional: `continuity` or tree inefficiency is not treated as a universal quantity across different intrinsic support classes.

## Reporting rule

- independently scaled `span`: standardized within-cloud dispersion;
- shared-reference `span`: comparative extent in the declared reference units;
- `continuity`: MST compactness, compared only under support-matched designs;
- every reference transformation must retain fitted parameters and provenance.