import numpy as np
import pytest
from benchmarks import bam_geometry_response_envelopes_v1 as m

def test_hull_extent_handles_duplicates_collinear_and_inclusion():
    assert m.hull_area(np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.],[0.,0.]])) == 1.
    assert m.hull_area(np.array([[0.,0.],[1.,0.],[2.,0.]])) == 0.
    assert m.hull_area(np.array([[0.,0.],[1.,0.],[1.,1.],[0.,2.]])) >= 1.

def test_original_span_on_triangle():
    values=m.measure(np.array([[0.,0.],[0.,3.],[4.,0.]]),0b111,3,1)
    assert values['span'] == pytest.approx(4.8)
    assert values['hull_area'] == 6.
    assert values['components'] == 1

def test_ideal_release_keeps_other_axes_and_rejects_bad_G():
    r={'A_bits':0b011,'B_bits':0b111,'M_bits':0b101,'G_bits':0b001}
    assert m.release(r,'A')==0b101
    assert m.release(r,'B')==0b001
    assert m.release(r,'M')==0b011
    with pytest.raises(ValueError):m.release({**r,'G_bits':0b111},'A')
    with pytest.raises(ValueError):m.release(r,'Q')

def test_same_current_map_can_hide_opposite_geometric_response():
    x=np.array([[0.,0.],[10.,0.],[0.1,0.],[20.,0.]])
    rows=[{'world_id':'w1','A_bits':3,'B_bits':7,'M_bits':15,'G_bits':3},
          {'world_id':'w2','A_bits':3,'B_bits':11,'M_bits':15,'G_bits':3}]
    s=m.fibre_summary('toy',rows,x,4,1,'A')
    assert not s['map_identified']
    assert s['targets']['span']['directions']==[-1,1]
    assert not s['targets']['span']['direction_identified']
    refined=m.refine_fibre(rows,'B')
    assert len(refined)==2
    for group in refined:
        small=m.fibre_summary('toy',group,x,4,1,'A')
        assert small['targets']['span']['direction_identified']
        assert small['targets']['span']['minimum_change']>=s['targets']['span']['minimum_change']
        assert small['targets']['span']['maximum_change']<=s['targets']['span']['maximum_change']

def test_target_can_be_identified_without_identifying_map():
    x=np.array([[-1.,0.],[1.,0.],[0.,1.],[0.,-1.]])
    rows=[{'world_id':'w1','A_bits':3,'B_bits':7,'M_bits':15,'G_bits':3},
          {'world_id':'w2','A_bits':3,'B_bits':11,'M_bits':15,'G_bits':3}]
    s=m.fibre_summary('toy',rows,x,4,1,'A')
    assert not s['map_identified']
    assert s['targets']['span']['magnitude_identified']
    assert s['targets']['span']['direction_identified']

def test_singleton_map_is_identified_and_invalid_geometry_rejected():
    rows=[{'world_id':'w','A_bits':3,'B_bits':7,'M_bits':7,'G_bits':3}]
    s=m.fibre_summary('toy',rows,np.array([[0.,0.],[1.,0.],[2.,1.]]),3,1,'A')
    assert s['map_identified']
    assert all(t['magnitude_identified'] and t['direction_identified'] for t in s['targets'].values())
    with pytest.raises(ValueError):m.measure(np.zeros((3,2)),8,3,1)
    with pytest.raises(ValueError):m.measure(np.zeros((3,2)),1,3,1)
