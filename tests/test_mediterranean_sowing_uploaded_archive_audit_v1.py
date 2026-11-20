"""Offline integrity and classifier unit tests; entirely invented fixtures."""
from __future__ import annotations
from importlib import util
from io import BytesIO
from pathlib import Path
import hashlib
import json
import zipfile
import pandas as pd
import pytest

HERE = Path(__file__).parent
MODULE = HERE.parent / 'benchmarks' / 'mediterranean_sowing_uploaded_archive_audit_v1.py'
spec = util.spec_from_file_location('upload_audit', MODULE)
audit = util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_zip_checksum_roundtrip(tmp_path):
    zpath=tmp_path/'fixture.zip'
    with zipfile.ZipFile(zpath,'w') as z:
        for name in audit.EXPECTED_MEMBER_NAMES:
            z.writestr(name,'name,value\na,b\n')
    raw,member=audit.safe_zip(zpath)
    assert len(member)==12
    meta=[dict(name=n,size=x['size'],digest_type='sha-256',digest=x['sha256']) for n,x in member.items()]
    assert audit.validate_official_manifest(member,meta)['status']=='ALL_12_FILES_MATCH_OFFICIAL_DIGEST_AND_SIZE'
    meta[0]['digest']='f'*64
    assert audit.validate_official_manifest(member,meta)['status']=='SOURCE_STOP_OFFICIAL_DIGEST_MISMATCH'
    with zipfile.ZipFile(zpath,'a') as z:z.writestr('../evil.csv','1')
    with pytest.raises(ValueError,match='SOURCE_STOP_UNEXPECTED_OR_DUPLICATE_ZIP_MEMBER'):
        audit.safe_zip(zpath)


def make_data(stations=3,n=40,p_succ=3,u_succ=0):
    rows=[]
    for st in range(stations):
        for arm,success in [('protected',p_succ),('unprotected',u_succ)]:
            for seed in range(1,n+1):
                rows.append(dict(species='sp1',site='patch1',year=2021,microhabitat='tree',
                                 station=st+1,site_type='absent',treatment=arm,point=seed,seed=1,
                                 station_id='sp1-patch1-%d-%s-2021'%(st+1,arm),fruit_type='fleshy',
                                 germ=1. if seed<=success else 0.,
                                 seedling_surv=1. if seed==1 and seed<=success else float('nan'),
                                 sapling_surv_sd=float('nan'),seedling_monitoring=1))
    return pd.DataFrame(rows)


def test_one_model_free_fixed_direction_with_three_paired_stations():
    result,_=audit.calculate(make_data(p_succ=4))
    group=result['unaffected_robust_germination_direction']['absent']
    assert group['signs']['increase']==1
    assert group['site_species_year_units']==1
    witness=result['unaffected_natural_absence_witnesses']
    assert witness['protected_survived_first_summer']['unique_species_site_combinations']==1
    assert witness['unprotected_survived_first_summer']['unique_species_site_combinations']==0


def test_exact_point_025_is_zero_not_increase():
    result,_=audit.calculate(make_data(p_succ=1))
    assert result['unaffected_robust_germination_direction']['absent']['signs']['operational_zero']==1


def test_conflicting_duplicate_seed_stops_primary_globally():
    df=make_data()
    duplicated=df.iloc[[0]].copy()
    duplicated.loc[:,'germ']=0.
    df=pd.concat([df,duplicated],ignore_index=True)
    result,_=audit.calculate(df)
    assert result['strict_source_stop']['status']=='BLOCK_PRIMARY_GLOBAL_INFERENCE'
    assert result['strict_source_stop']['duplicate_seed_key_groups']==1
    assert result['strict_source_stop']['affected_species_site_year_units'][0]['site']=='patch1'
    assert result['observations']['unaffected_species_site_year_units']==0