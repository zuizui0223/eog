#!/usr/bin/env python3
"""Uploaded Dryad archive: lossless source audit and bounded station response.

Research status: post-source-exposure structural audit, *not* a new pre-registered
EOG/BAM forecast. Does not infer missing seed outcomes, silently repair duplicate
seed labels, treat seeds as independent landscapes, or claim that introduced seed
success proves natural dispersal caused historical absence.

This script implements the +/- 0.025 signed treatment-response target frozen in
EOG PR #706. It declares SOURCE_QUALITY_STOP for the complete primary analysis
when conflicting seed identities occur and reports explicitly labelled, strictly
unaffected-unit descriptive bounds separately.
"""
from __future__ import annotations
import argparse
import hashlib
from fractions import Fraction
import io
import json
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd

DOI = '10.5061/dryad.t1g1jwtg3'
MUST_INCLUDE = frozenset({
    'sowing_experiment.csv', 'soil_physicochemical.csv',
    'soil_moisture_vwc_values.csv', 'planting_experiment.csv', 'README.md',
})
EXPECTED_MEMBER_NAMES = frozenset({
    *MUST_INCLUDE, 'vegetation_cover.csv',
    *('code_%d_%s.R' % (n, s) for n, s in [
        (1,'sowing_demographic_analysis'),(2,'temporal_trends'),
        (3,'planting'),(4,'soil_analyses'),(5,'soil_moisture_analyses'),
        (6,'vegetation_cover')]),
})
KEY_STATION = ['species','site','year','microhabitat','station','site_type']
KEY_SEED = KEY_STATION + ['treatment','point','seed']
KEY_UNIT = ['species','site','year','site_type']
TOL = 0.025


def safe_zip(zp):
    if not zipfile.is_zipfile(zp):
        raise ValueError('SOURCE_STOP_INVALID_ZIP')
    with zipfile.ZipFile(zp) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or frozenset(names) != EXPECTED_MEMBER_NAMES:
            raise ValueError('SOURCE_STOP_UNEXPECTED_OR_DUPLICATE_ZIP_MEMBER')
        for i in z.infolist():
            if i.is_dir() or i.flag_bits & 1 or i.file_size > 12_000_000:
                raise ValueError('SOURCE_STOP_ENCRYPTED_DIR_OR_OVERSIZE')
            if i.filename not in EXPECTED_MEMBER_NAMES or '/' in i.filename or '\\' in i.filename:
                raise ValueError('SOURCE_STOP_UNSAFE_ZIP_PATH')
            if i.external_attr >> 16 & 0o170000 == 0o120000:
                raise ValueError('SOURCE_STOP_SYMLINK')
        if z.testzip() is not None:
            raise ValueError('SOURCE_STOP_ZIP_CRC_FAILURE')
        data = {n:z.read(n) for n in names}
    members = {n:{'size':len(b),'md5':hashlib.md5(b, usedforsecurity=False).hexdigest(),
                  'sha256':hashlib.sha256(b).hexdigest()} for n,b in data.items()}
    return data,members


def validate_official_manifest(members, meta):
    if meta is None:
        return {'status':'AWAITING_AUTHORITATIVE_PROVIDER_DIGEST',
                'note':'User-supplied ZIP identity and per-member hashes are fixed, not yet independently matched to provider SHA/MD5'}
    lookup={}
    for row in meta:
        name=row.get('name')
        if name in lookup:
            raise ValueError('SOURCE_STOP_PROVIDER_DUPLICATE_FILENAME')
        lookup[name]=row
    diffs={}
    for name in EXPECTED_MEMBER_NAMES:
        r=lookup.get(name)
        if not r:
            diffs[name]='NOT_IN_AUTHORITATIVE_MANIFEST';continue
        algo=str(r.get('digest_type','')).lower().replace('-','')
        expected=r.get('digest')
        if algo not in ('md5','sha256'):
            diffs[name]='UNSUPPORTED_DIGEST_ALGORITHM';continue
        if not isinstance(r.get('size'),int):
            diffs[name]='MISSING_PROVIDER_SIZE';continue
        if int(r['size'])!=members[name]['size'] or str(expected).lower()!=members[name][algo]:
            diffs[name]='SIZE_OR_DIGEST_MISMATCH'
    if diffs:
        return {'status':'SOURCE_STOP_OFFICIAL_DIGEST_MISMATCH','failures':diffs}
    return {'status':'ALL_12_FILES_MATCH_OFFICIAL_DIGEST_AND_SIZE'}


def source_frame(data):
    d=pd.read_csv(io.BytesIO(data['sowing_experiment.csv']),low_memory=False)
    columns=frozenset(d.columns)
    required=frozenset(KEY_SEED+['station_id','fruit_type','germ','seedling_surv','sapling_surv_sd','seedling_monitoring'])
    if not required.issubset(columns):
        raise ValueError('SOURCE_STOP_MISSING_SOWING_COLS')
    if len(d)!=61000:
        raise ValueError('SOURCE_STOP_UNEXPECTED_SOWING_ROW_COUNT')
    if not set(d.treatment.unique())=={'protected','unprotected'} or not set(d.site_type.unique())=={'present','absent'}:
        raise ValueError('SOURCE_STOP_TREATMENT_OR_NATURAL_STATUS')
    if not d.germ.dropna().isin([0,1]).all() or not d.seedling_surv.dropna().isin([0,1]).all() or not d.sapling_surv_sd.dropna().isin([0,1]).all():
        raise ValueError('SOURCE_STOP_UNKNOWN_LIFE_STAGE_CODE')
    if d[KEY_SEED].isna().any().any():
        raise ValueError('SOURCE_STOP_MISSING_SEED_ID')
    expected_ids=(d['species'].astype(str)+'-'+d['site'].astype(str)+'-'+d['station'].astype(str)+'-'+
                  d['treatment'].astype(str)+'-'+d['year'].astype(str))
    if not (expected_ids == d.station_id).all():
        raise ValueError('SOURCE_STOP_STATION_ID_INCONSISTENCY')
    if (d[(d.germ==0) & (d.seedling_surv==1)].shape[0]!=0):
        raise ValueError('SOURCE_STOP_SURVIVED_WITHOUT_GERMINATION')
    return d


def calculate(d):
    duplicate_mask=d.duplicated(KEY_SEED,keep=False)
    flagged=d.loc[duplicate_mask,KEY_STATION].drop_duplicates()
    flagged_keys=set(map(tuple,flagged.itertuples(index=False,name=None)))
    affected=d[KEY_STATION].apply(tuple,axis=1).isin(flagged_keys)
    clean=d.loc[~affected].copy()
    groups=clean.groupby(KEY_STATION+['treatment'],dropna=False,sort=True).agg(
        n=('germ','size'),
        succ=('germ',lambda s:int((s==1).sum())),
        miss=('germ',lambda s:int(s.isna().sum())),
    ).reset_index()
    p=groups[groups.treatment=='protected'].drop(columns='treatment').rename(columns={k:k+'_p' for k in ['n','succ','miss']})
    u=groups[groups.treatment=='unprotected'].drop(columns='treatment').rename(columns={k:k+'_u' for k in ['n','succ','miss']})
    paired=p.merge(u,on=KEY_STATION,validate='one_to_one',indicator=True)
    if not (paired._merge == 'both').all() or len(paired)!=len(p) or len(paired)!=len(u):
        raise ValueError('SOURCE_STOP_MISSING_TREATMENT_STATION_PAIR')
    paired['lower']=paired.succ_p/paired.n_p-(paired.succ_u+paired.miss_u)/paired.n_u
    paired['upper']=(paired.succ_p+paired.miss_p)/paired.n_p-paired.succ_u/paired.n_u
    if not (paired.lower <= paired.upper+1e-12).all():
        raise ValueError('CALCULATION_STOP_INVALID_INTERVAL')
    unit=paired.groupby(KEY_UNIT,as_index=False).agg(
        lower=('lower','mean'),upper=('upper','mean'),n_station_pairs=('lower','size')
    )
    # Assign the frozen +/-1/40 threshold using exact integer rational
    # arithmetic. A binary floating-point approximation of 0.025 can turn a
    # threshold-equal effect into a spurious increase/decrease.
    exact_directions = {}
    for k,group in paired.groupby(KEY_UNIT,sort=False):
        lo = sum((Fraction(int(r.succ_p),int(r.n_p)) -
                  Fraction(int(r.succ_u)+int(r.miss_u),int(r.n_u))
                  for r in group.itertuples(index=False)),Fraction())/len(group)
        hi = sum((Fraction(int(r.succ_p)+int(r.miss_p),int(r.n_p)) -
                  Fraction(int(r.succ_u),int(r.n_u))
                  for r in group.itertuples(index=False)),Fraction())/len(group)
        threshold = Fraction(1,40)
        exact_directions[k] = ('increase' if lo>threshold else
                               'decrease' if hi< -threshold else
                               'operational_zero' if lo>=-threshold and hi<=threshold
                               else 'unresolved')
    unit['direction']=[exact_directions[tuple(x)] for x in
                       unit[KEY_UNIT].itertuples(index=False,name=None)]
    # Identify whole species-site-year units that contain an anomalous station.
    affected_units={tuple(x) for x in flagged[KEY_UNIT].itertuples(index=False,name=None)}
    unit['data_quality_status']=['AFFECTED_UNIT_NOT_ELIGIBLE' if tuple(v) in affected_units else 'CLEAN'
                                 for v in unit[KEY_UNIT].itertuples(index=False,name=None)]
    unaffected=unit[unit.data_quality_status=='CLEAN'].copy()
    if not (unaffected.n_station_pairs>=3).all():
        raise ValueError('SOURCE_STOP_TOO_FEW_STATION_PAIR_SAMPLES')
    # Make witness counts *only from unambiguously labelled station pairs*.
    absent=clean[clean.site_type=='absent'].copy()
    def witnessed(col,treatment):
        x=absent[(absent.treatment==treatment)&(absent[col]==1)]
        keys=x[['species','site']].drop_duplicates()
        return {'individual_seed_records':int(len(x)),
                'unique_species_site_combinations':int(len(keys)),
                'independent_patches':int(keys.site.nunique()),
                'unique_species':int(keys.species.nunique())}
    all_absent_pairs=int(len(d[d.site_type=='absent'][['species','site']].drop_duplicates()))
    counts={}
    for status in ('absent','present'):
        sub=unaffected[unaffected.site_type==status]
        counts[status]={'site_species_year_units':int(len(sub)),
                        'patches':int(sub.site.nunique()),
                        'signs':{sign:int((sub.direction==sign).sum()) for sign in ('increase','decrease','operational_zero','unresolved')}}
    out={
        'schema':'eog.mediterranean_seed_uploaded_archive_audit.v1',
        'source_doi':DOI,
        'scientific_status':'PRIMARY_SOURCE_QUALITY_STOP_DUPLICATE_SEED_KEY; UNAFFECTED_EXPLORATORY_RESULTS_ONLY',
        'primary_protocol':'EOG PR #706 pre-outcome protocol; +/-0.025 rule retained',
        'strict_source_stop':{'duplicate_seed_key_groups':int(d[duplicate_mask].groupby(KEY_SEED).ngroups),
                              'duplicate_seed_key_rows':int(duplicate_mask.sum()),
                              'affected_station_pairs':[dict(zip(KEY_STATION,k)) for k in sorted(flagged_keys)],
                              'affected_original_seed_rows':int(affected.sum()),
                              'affected_species_site_year_units':[dict(zip(KEY_UNIT,k)) for k in sorted(affected_units)],
                              'status':'BLOCK_PRIMARY_GLOBAL_INFERENCE'},
        'observations':{'seed_rows':int(len(d)),'species':int(d.species.nunique()),
                        'forest_patches':int(d.site.nunique()),
                        'distinct_station_ids':int(d.station_id.nunique()),
                        'germination_known_positives':int((d.germ==1).sum()),
                        'germination_missing':int(d.germ.isna().sum()),
                        'natural_absent_species_site_combinations':all_absent_pairs,
                        'usable_clean_matched_station_pairs':int(len(paired)),
                        'unaffected_species_site_year_units':int(len(unaffected))},
        'unaffected_robust_germination_direction':counts,
        'unaffected_natural_absence_witnesses':{
             'first_summer_witnesses_with_missing_germination_field':int(len(absent[(absent.seedling_surv==1) & (absent.germ.isna())])),
             'unprotected_first_summer_witnesses_with_missing_germination_field':int(len(absent[(absent.treatment=='unprotected') & (absent.seedling_surv==1) & (absent.germ.isna())])),
             'unprotected_germination':witnessed('germ','unprotected'),
             'unprotected_survived_first_summer':witnessed('seedling_surv','unprotected'),
             'unprotected_survived_second_summer':witnessed('sapling_surv_sd','unprotected'),
             'protected_survived_first_summer':witnessed('seedling_surv','protected'),
             'protected_survived_second_summer':witnessed('sapling_surv_sd','protected')},
        'target_semantics':{
            'direction':'Species × patch × sowing-year equal-station mean germination-fraction protected-minus-unprotected; missing germinations bounded [0,1] at seed level; +/-0.025 decision tolerance',
            'witness':'Confirmed individual survivals in original seed rows at naturally absent patches, excluding the entire anomalous station-pair; not survival probability or population persistence',
            'claim_limit':'Direct established seedlings in introduced-seed conditions demonstrate nonzero early-stage viability despite natural absence. They do NOT identify causal historical M, A/B/M worlds, whole-population occupancy or generalize beyond 10 patches.',
            'inference_unit':'10 forest patches, not 61,000 independent trials',
            'artifact_type':'Post-source-exposure diagnostic and partial logical certificate, not independent model-predictive validation'},
        'unaffected_unit_results':[{
            'species':str(r.species),'site':str(r.site),'year':int(r.year),
            'site_type':str(r.site_type),'n_station_pairs':int(r.n_station_pairs),
            'lower':float(r.lower),'upper':float(r.upper),'direction':str(r.direction)
        } for r in unaffected.itertuples(index=False)]
    }
    return out,unit


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source-zip',type=Path,required=True)
    ap.add_argument('--official-manifest',type=Path)
    ap.add_argument('--output-dir',type=Path,required=True)
    args=ap.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    data,members=safe_zip(args.source_zip)
    official=json.loads(args.official_manifest.read_text()) if args.official_manifest else None
    integrity=validate_official_manifest(members,official)
    if integrity['status'] != 'ALL_12_FILES_MATCH_OFFICIAL_DIGEST_AND_SIZE':
        raise ValueError('SOURCE_STOP_UNVERIFIED_OFFICIAL_DIGEST: '+integrity['status'])
    report,unit=calculate(source_frame(data))
    report['provenance']={
        'upload_basename':args.source_zip.name,
        'uploaded_zip_sha256':hashlib.sha256(args.source_zip.read_bytes()).hexdigest(),
        'official_manifest_comparison':integrity,
        'original_member_hashes':dict(sorted(members.items())),
        'README_sha256':members['README.md']['sha256']}
    outfile=args.output_dir/'result.json'
    outfile.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n')
    unit.to_csv(args.output_dir/'all_52_unit_quality_flow.csv',index=False)
    cleanunits=report['unaffected_unit_results']
    pd.DataFrame(cleanunits).to_csv(args.output_dir/'unaffected_51_unit_bounds.csv',index=False)
    # A machine-readable ready/not-ready distinction for external workflows.
    (args.output_dir/'status.txt').write_text(report['scientific_status']+'\n')
    print(json.dumps({'status':report['scientific_status'],
        'provider_digest_status':integrity['status'],
        'strict_quality_stop':report['strict_source_stop'],
        'n_unaffected':len(cleanunits),
        'robust_directions':report['unaffected_robust_germination_direction'],
        'naturally_absent_witnesses':report['unaffected_natural_absence_witnesses']},
        indent=2))

if __name__=='__main__':main()