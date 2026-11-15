"""Composite grouping-key contract tests (no model fit)."""
import pytest
from benchmarks import wetland_survey_grain_v1 as m

def test_group_key_not_unique_row_id():
    fields=["surv","site","method","doy","date","num"]
    a={"surv":"alpha:bottletrap:89","site":"alpha","method":"bottletrap",
       "doy":"89","date":"2024-03-29","num":"1"}
    b=dict(a)
    c={"surv":"alpha:visual:89","site":"alpha","method":"visual",
       "doy":"89","date":"2024-03-29","num":"1"}
    p=m.describe_grain([a,b,c],fields)
    assert p["native_rows"]==3
    assert p["distinct_composite_occasion_keys"]==2
    assert p["repeated_occasion_keys"]==1
    assert p["rows_in_repeated_occasion_keys"]==2
    assert p["by_method"]["bottletrap"]=={"native_rows":2,"distinct_occasion_keys":1}


def test_non_composite_group_key_fails_closed():
    a={"surv":"madeup","site":"alpha","method":"bottletrap",
       "doy":"89","date":"2024-03-29","num":"1"}
    with pytest.raises(ValueError,match="site:method:doy"):
        m.describe_grain([a],list(a))
