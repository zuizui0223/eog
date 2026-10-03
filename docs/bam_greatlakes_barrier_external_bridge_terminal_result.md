# Great Lakes A/M external bridge — terminal result

## Outcome

The once-only real-data execution reached the checksum-bound Dryad version archive and
opened **110,096 bytes**.  It then stopped during frozen physical-schema validation.

The catch RDS schema did not match the preregistered exact schema.

Expected:

```text
pair_id, pair_id_num, Year, Stream.Name, stream_id, barrier, position,
segment, survey_length, species, total_caught, yearBuilt,
barrierAgeAtSample, period
```

Observed:

```text
pair_id, Year, Stream.Name, stream_id, barrier, position, segment,
nrecords, survey_length, species, total_caught, yearBuilt,
barrierAgeAtSample, period, pair_id_num
```

The observed table contains an undeclared `nrecords` column and places
`pair_id_num` at the end rather than in the frozen second position.

## Consequence

The protocol is **terminal**.  The raw payload had already been opened, so accepting
`nrecords`, changing expected column order, dropping the extra field, or rerunning
would be a post-response parser repair.

No such repair is authorized.

- model fits: **0**;
- BAM survivor-fiber scoring: **not reached**;
- empirical BAM evidence: **none**;
- retry: **forbidden**.

The authoritative artifact is GitHub Actions run `36792320740`, artifact
`11132259192`, digest
`sha256:d71a1dd085ee41c90383138ba4d6e9f68257a06f9b7621af1b3f7d9e3a5a3631`.

## Important provenance clarification

The raw result records `rds_values_parsed=false`.  That flag means the scientific
bridge analysis was never reached.  It must **not** be interpreted as “the RDS payload
was unread.”  The RDS objects were deserialized to inspect their physical schema before
the mismatch was detected.

## Scientific interpretation

This is not evidence for or against BAM target identifiability in the Great Lakes fish
system.  It is a fail-closed schema stop.

Together with the round-goby transport stop, it shows that the synthetic finite-world
programme is ahead of the empirical bridge in one mundane but important respect:
real-data source contracts need physical schema to be independently knowable before
response-bearing files are opened.

The next empirical candidate must satisfy that stronger acquisition condition rather
than repairing this one.
