"""Purely synthetic tests for the stage-specific, one-sided witness contract."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import pandas as pd
import pytest

HERE=Path(__file__).resolve().parents[1]
PATH=HERE/'benchmarks'/'mediterranean_sowing_planting_stage_witness_v1.py'
import sys
sys.path.insert(0,str(HERE/'benchmarks'))
spec=importlib.util.spec_from_file_location('stage_witness',PATH)
stage=importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)


def sow_fixture():
    rows=[]
    # Four forest sites, ten taxa; artificially encode all forty site×taxon
    # combinations and all three nested sowing stages.
    for sp in range(10):
        for site in range(4):
            status='absent' if site in (0,1) else 'present'
            for station in range(1,4):
                for treatment in ('protected','unprotected'):
                    for seed in range(1,3):
                        early= (sp==0 and site==0 and treatment=='unprotected')
                        germ=1 if (early and seed==1) else 0
                        rows.append({
                          'species':f'sp{sp}','site':f'site{site}',
                          'year':2021,'microhabitat':'shrub','station':station,
                          'site_type':status,'treatment':treatment,'point':seed,
                          'seed':1,'germ':germ,
                          'seedling_surv':1 if (early and station==1 and seed==1) else 0,
                          'sapling_surv_sd':0,
                        })
    return pd.DataFrame(rows)


def plant_fixture():
    return pd.DataFrame([{
      'species':f'sp{sp}', 'fruit_type':'fleshy', 'site':f'site{site}',
      'site_type':'absent' if site in (0,1) else 'present',
      'station':i+1, 'id':1, 'microhabitat':'shrub',
      'survival':1 if (sp==0 and site==1 and i==0) else 0,
    } for sp in range(4) for site in range(4) for i in range(3)])


def test_planted_witness_rescues_only_evidence_not_causal_mechanism():
    r=stage.witness_matrix(sow_fixture(),plant_fixture())
    assert r['n_sowing_species_patch_combinations']==40
    assert r['n_planting_rows']==48
    missing=[x for x in r['per_species_patch'] if x['species']=='sp0' and x['site']=='site1'][0]
    assert missing['planted_first_summer'] is True
    assert missing['sown_unprotected_first_summer'] is False
    assert missing['cross_stage_class']=='planting_only_witnessed'
    unsown=[x for x in r['per_species_patch'] if x['species']=='sp0' and x['site']=='site0'][0]
    assert unsown['cross_stage_class']=='sown_only_witnessed'
    assert r['status_summary']['absent']['cross_stage_counts']['planting_only_witnessed']==1
    assert r['status_summary']['absent']['cross_stage_counts']['sown_only_witnessed']==1
    assert r['status_summary']['absent']['n_planted_species_patch_combinations']==8
    assert r['status_summary']['absent']['n_sown_species_patch_combinations']==20


def test_sow_anomaly_is_whole_station_pair_quarantine():
    sow=sow_fixture()
    bad=sow.iloc[[0]].copy()
    bad.loc[:,'germ']=1
    new=pd.concat([sow,bad],ignore_index=True)
    r=stage.witness_matrix(new,plant_fixture())
    assert r['source_quality']['sowing_duplicate_seed_key_groups']==1
    # Both arm rows plus the appended duplicated source record are quarantined.
    assert r['source_quality']['sowing_quarantined_rows_both_treatments']==5


def test_duplicate_planting_key_rejected_without_repair():
    sow=sow_fixture()
    plant=plant_fixture()
    padded=pd.concat([plant]*7,ignore_index=True).iloc[:299].copy()
    with pytest.raises(ValueError,match='DUPLICATE_INDIVIDUAL_KEY'):
        stage.planting_frame(padded.to_csv(index=False).encode(),sow)


def test_planted_natural_status_conflict_is_hard_stop():
    sow=sow_fixture()
    plant=plant_fixture()
    # 299 individuals with unique station IDs, including a source-label conflict.
    expanded=[]
    for i in range(299):
        orig=plant.iloc[i % len(plant)].to_dict()
        orig['station']=i+1
        expanded.append(orig)
    d=pd.DataFrame(expanded)
    d.loc[0,'site_type']='present'
    with pytest.raises(ValueError,match='STATUS_CONFLICT'):
        stage.planting_frame(d.to_csv(index=False).encode(),sow)


def test_unknown_survival_not_converted_to_death_or_success():
    df=plant_fixture()
    df['survival']=float('nan')
    r=stage.witness_matrix(sow_fixture(),df)
    assert r['status_summary']['absent']['n_planted_first_summer_witnesses']==0
    assert r['status_summary']['absent']['n_planted_unknown_survival']==24
    assert all(x['planted_first_summer'] is False for x in r['per_species_patch'] if x['planting_sampled'])