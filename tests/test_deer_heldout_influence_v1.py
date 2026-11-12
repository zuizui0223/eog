"""Influence audit must preserve all site scores and rank deterministically."""
import numpy as np
import pytest
from benchmarks import deer_heldout_influence_v1 as m

def fixture():
    rows=[{"site_id":f"s{i:02d}","beta_minus_constant":float(44-i)} for i in range(87)]
    total=sum(x["beta_minus_constant"] for x in rows)
    rows[0]["beta_minus_constant"]+=95.57045328909554-total
    # Synthetic fixture uses a self-consistent baseline score for its own site rows.
    return {"fingerprint":m.EXPECTED,"source_sha256":"bcfeb04683e572d0ded79fd40917a546188b4e2df64c043d9e1ea8720d524e34","per_site":rows,
            "beta_minus_constant_total_log_score":95.57045328909554,
            "folds":[{"fold":1,"heldout_beta_log_score":-1,"heldout_constant_log_score":-2,"n_test":87}]}

def test_site_ranking_and_robustness():
    r=m.audit(fixture())
    assert r["sites"]==87
    assert r["top_site"]["site_id"]=="s00"
    assert len(r["top_k_removal"])==4
    assert r["top_k_removal"][0]["remaining_total_gain"]==pytest.approx(r["total_gain"]-r["top_site"]["gain"])
    assert r["symmetric_trimmed"][0]["n_remaining"]==79

def test_fail_on_source_change():
    r=fixture();r["source_sha256"]="changed"
    with pytest.raises(ValueError,match="source"):m.audit(r)

def test_fail_on_duplicate_sites():
    r=fixture();r["per_site"][1]["site_id"]=r["per_site"][0]["site_id"]
    with pytest.raises(ValueError,match="roster"):m.audit(r)
