"""Independent synthetic integrity tests for frozen NutNet Y3 scorer."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

MODULE=Path(__file__).resolve().parents[1]/"benchmarks"/"nutnet_hodapp_y3_score_v1.py"
spec=importlib.util.spec_from_file_location("nutnet_hodapp_y3_scorer",MODULE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def test_positive_distance_q90_and_zero_case():
    x=np.array([[0.,0.],[3.,4.],[6.,8.]])
    assert abs(mod.positive_span(x)-9.0)<1e-12
    assert mod.positive_span(np.array([[1.,1.],[1.,1.],[1.,1.]]))==0.

def test_frozen_sign_tolerance_and_jaccard():
    assert [mod.sign(v) for v in [-0.021,-0.02,0.,0.02,0.021]] == [-1,0,0,0,1]
    assert abs(mod.jaccard({"a","b"},{"b","c"}) - (2./3.))<1e-12
    assert mod.jaccard(set(),set())==0.

def test_strict_matched_block_eligibility():
    d=[]
    for block in ("1","2","3"):
        for trt,plot in (("Control","10"),("Fence","20")):
            for y in (0,3):
                d.append({"site_code":"s1","block":block,"plot":plot,
                          "year_trt":y,"trt":trt,"Taxon":"plant", "cov":20.})
    df=pd.DataFrame(d)
    valid,flow=mod.eligible_match(df)
    assert valid["s1"]==["1","2","3"]
    assert flow["minimum_3_matched_site_count"]==1
    df=pd.concat([df,pd.DataFrame([{"site_code":"s1","block":"1","plot":"11","year_trt":y,
                                   "trt":"Control","Taxon":"plant","cov":10.} for y in (0,3)])],ignore_index=True)
    valid,flow=mod.eligible_match(df)
    assert valid=={}
    assert flow["one_control_one_fence_blocks"]==2

def test_training_only_ridge_reproducible_and_missingness_safe():
    rows=[
        {"D_site":val,"predictors":{"y0_richness":4+i,"y0_span":0.4+i/100,"y0_mean_jaccard":0.2,
                                  "E_pH":float("nan") if i==1 else 4+i/10}}
        for i,val in enumerate((.1,-.05,.2,.0,.03))
    ]
    train=[0,1,2,3];test=[4]
    for f in mod.FAMILIES:
        pred=mod.predict_family(rows,train,test,f)
        assert np.isfinite(pred).all()
        assert np.array_equal(pred,mod.predict_family(rows,train,test,f))
    assert mod.predict_family(rows,train,test,"mean").item()==np.mean([.1,-.05,.2,.0])
