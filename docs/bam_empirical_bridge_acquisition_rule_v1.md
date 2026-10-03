# Empirical BAM bridge acquisition rule v1

This rule is frozen after three fail-closed real-system attempts and before the Sweden
raw response payload is opened.

## Why the rule changed

Three retrospective bridge candidates failed before scientific survivor scoring:

1. **Rouge River round goby** — source identity passed, but response-blind header access
   stopped on transport.
2. **Great Lakes low-head-dam fish** — response payload opened once, then physical RDS
   schema disagreed with the frozen documentation-derived parser; no rerun.
3. **Penobscot restoration** — archive architecture failed before payload because the
   exact prospectively required passage database file was absent.

These failures do not count as empirical evidence for or against BAM. They are
acquisition-contract failures.

## Mandatory conditions for a new bridge

A source is eligible for once-only response opening only when all of the following are
true before payload access:

1. the exact source/version identity is frozen;
2. the complete file roster is frozen from repository metadata;
3. the response-bearing file has exact byte size and cryptographic digest pinned;
4. the physical response-file schema and column order are independently documented
   before the response file is opened;
5. the parser treats any extra/missing/reordered field as terminal;
6. the ecological world universe, target, cohort and temporal split are frozen;
7. the response-bearing transport route is known to be available or has an anonymous
   checksum-verifiable package fallback;
8. only one payload-consuming execution is authorized.

## Preferred source class

Prefer simple CSV/TSV sources whose physical schema is published in README metadata.

Avoid Access/RDS or opaque binary containers unless the exact internal physical schema
can be frozen independently from documentation before payload opening.

## Scientific boundary

This rule improves auditability; it does not make a retrospective source fresh or
independent confirmatory evidence.

A bridge that fails acquisition gates remains a documented stop, not a failed ecological
hypothesis test.
