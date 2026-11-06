import numpy as np
import pandas as pd
import pytest
from benchmarks import charaxes_empirical_geometry_v1 as m

def test_zero_inflated_variable_not_erased_by_shared_reference():
    x=np.array([[0.,0.],[0.,1.],[0.,2.],[0.,3.],[0.,4.],[2.,5.]])
    z,ref=m.transform(x)
    assert np.median(abs(x[:,0]-np.median(x[:,0])))==0
    assert z[-1,0]>0 and not ref['constant'][0]
    assert np.allclose(z.std(0),1)
def test_scalar_geometry_matches_known_triangle_and_duplicates():
    x=np.array([[0.,0.],[0.,3.],[4.,0.]])
    r=m.geometry(x)
    assert r['span']==pytest.approx(4.8)
    assert r['mst_compactness']==pytest.approx(5/7)
    assert r['gap_strength']==pytest.approx(4/3.5)
    assert m.geometry(np.vstack([x,x[0]]))['gap_strength']==pytest.approx(r['gap_strength'])
def test_stratified_samples_preserve_counts_without_duplicates():
    d=pd.DataFrame({'district_ID':[1]*4+[2]*4,'year':[2018]*8,'oak_species':['E']*8})
    positive=np.array([True,True,False,False,True,False,False,False])
    strata=m.make_strata(d,positive)
    for _ in range(5):
        ids=m.draw_indices(strata,np.random.default_rng(42))
        assert len(ids)==len(set(ids))==3
        assert (ids<4).sum()==2 and (ids>=4).sum()==1
def test_true_constant_is_only_constant_column():
    x=np.column_stack([np.arange(4),np.ones(4)])
    z,r=m.transform(x)
    assert r['constant']==[False,True]
    assert np.all(z[:,1]==0)
def test_original_eog_parity_when_installed():
    c=pytest.importorskip('eog.comparative')
    x=np.random.default_rng(3).normal(size=(15,3))
    z,r=m.transform(x)
    reference=c.RobustReference(median=np.asarray(r['center']),scale=np.asarray(r['scale']),constant=np.asarray(r['constant']),provenance='external full survey reference')
    original=c.infer_comparative_geometry(x,reference)
    measured=m.geometry(z)
    assert measured['span']==pytest.approx(original.span)
    assert measured['mst_compactness']==pytest.approx(original.continuity)
    assert measured['gap_strength']==pytest.approx(original.gap_strength)
