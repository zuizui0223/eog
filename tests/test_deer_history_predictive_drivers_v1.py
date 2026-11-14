"""History feature tests preserve missingness and observed adjacency."""
import numpy as np
from benchmarks import deer_history_predictive_drivers_v1 as m

def test_NA_breaks_zero_run():
    row=np.array([0,0,np.nan,0,0,0,1,0],float)
    assert m.longest_zero_run(row)==3
    assert m.adjacent_switches(row)==2

def test_missing_is_not_nondetection():
    row=np.array([0,np.nan,1,0],float)
    x=m.feature(row)
    assert x["observed_days"]==3 and x["missing_days"]==1
    assert x["detected_days"]==1
    assert x["detection_fraction_valid"]==1/3
    assert x["longest_zero_run"]==1

def test_groups_preserve_total():
    rows=[{"delta":1.,"detected_days":0},{"delta":-2.,"detected_days":1},{"delta":3.,"detected_days":2}]
    g=m.group(rows,"detected_days",lambda n:"none" if n==0 else "some")
    assert sum(x["sites"] for x in g)==3
    assert sum(x["total_delta"] for x in g)==2.
