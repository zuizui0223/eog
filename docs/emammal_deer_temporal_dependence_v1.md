# Real deer camera traps: temporal-order sensitivity

## Question

The prior real 87-site, up to 22-day deer camera-trap occupancy
fit estimated daily p=0.367906 and ψ=0.720140 under independent
daily detection and site closure assumptions. These assumptions
were not verified. This analysis checks whether consecutive
detections cluster relative to a *within-site fixed-count
permutation null*, then fits the same model to odd/even days.

## Frozen analysis

Protocol commit `6646c777305e1ee7259825b5e73d003ec852a203`.
Original source SHA256
`bcfeb04683e572d0ded79fd40917a546188b4e2df64c043d9e1ea8720d524e34`.
Exactly 1,999 permutations, seed 20261108; each site's observed
0/1 values are shuffled only among its own observed days, while
NA positions are held fixed. This preserves per-site detection
frequency and availability but destroys day ordering.

The four predeclared transition metrics are same-state,
11, 00 and switching; report two-sided exploratory Monte
Carlo tails. Separately fit the constant-p/ψ model to the
original 22 days, odd-numbered days and even-numbered days.

## Verified exploratory results

Canonical CI:
https://github.com/zuizui0223/eog/actions/runs/42464957540

Among 1,612 consecutive pairs with valid observations on
both days, 234 were 11, 940 were 00, 1,174 had equal states,
and 438 switched.

| Metric | Observed | Null mean | Exploratory two-sided p |
|---|---:|---:|---:|
| 11 consecutive detections |234|222.884|0.127|
| same detection state |1174|1162.479|0.419|
| 00 consecutive nondetections |940|939.594|1.000|
| switched state |438|449.521|0.419|

The permutation test did **not** reject the fixed-count
within-site random time-order null at 0.05 for these four
statistics. This does not demonstrate independence or closure.

| Occasions | Valid site-days | p MLE | ψ MLE |
|---|---:|---:|---:|
| All 22 |1699|0.367906|0.720140|
| Odd-numbered days |861|0.404830|0.660632|
| Even-numbered days |837|0.398635|0.677925|

Odd/even splitting changes the observation window and
amount of information, not just dependence; the difference
is a sensitivity result, not an estimate of serial correlation
or a trend in deer ecology.

The exact result fingerprint is
`c076813ef5789484d8aa9ee58998621e6bbb59100f57cb9024b088d6f392831e`.
Original source and artifact checksums are preserved in
`validation/emammal_deer_temporal_dependence_v1/result_receipt.json`.

## Scientific boundary

The null conditions on each site's observed detection total.
It does not model time-varying effort, camera malfunction,
weather, season, heterogeneity or site closure. Failure to
reject does not validate the original independent-day
assumption. No independent A/B/M measurements, causal
constraint release or EOG geometric response is estimated.
This remains an exploratory field-data detection diagnostic
and adds no EOG-WF endpoint.
