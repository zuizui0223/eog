#!/usr/bin/env python3
"""Retrospective cross-stage witness matrix in original, SHA-pinned Dryad data.

A positive sowing or planting outcome can certify realized survival at one
experimentally supplied life stage. Zero observed positives do not certify
inviability, causal historical dispersal restriction, or future population
persistence. This post-exposure analysis retains the original sowing-source
quality STOP and never repairs the five duplicate seed identities.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path

import pandas as pd

from mediterranean_sowing_uploaded_archive_audit_v1 import (
    DOI, KEY_SEED, KEY_STATION, calculate, safe_zip,
    source_frame, validate_official_manifest,
)

EXPECTED_ARCHIVE_SHA256 = (
    'e05646c628caed63c7f169a53c52e3977f5c11dff3f5d1b1d7e7e32bcd871e26'
)
KEY = ['species', 'site']
PLANT_KEY = ['species', 'site', 'station', 'id']
PLANT_FIELDS = frozenset({
    'species', 'fruit_type', 'site', 'site_type', 'station', 'id',
    'microhabitat', 'survival',
})
STAGES = ('sown_unprotected_germ', 'sown_unprotected_first_summer',
          'sown_unprotected_second_summer', 'planted_first_summer')


def planting_frame(raw: bytes, sow_roster: pd.DataFrame) -> pd.DataFrame:
    d = pd.read_csv(io.BytesIO(raw), low_memory=False)
    if not PLANT_FIELDS.issubset(d.columns):
        raise ValueError('SCHEMA_STOP_PLANTING_MISSING_COLUMNS')
    if len(d) != 299:
        raise ValueError('SCHEMA_STOP_PLANTING_UNEXPECTED_ROW_COUNT')
    if d[PLANT_KEY + ['site_type']].isna().any().any():
        raise ValueError('SCHEMA_STOP_PLANTING_MISSING_ID')
    if d.duplicated(PLANT_KEY, keep=False).any():
        raise ValueError('SCHEMA_STOP_PLANTING_DUPLICATE_INDIVIDUAL_KEY')
    for field in ('station','id'):
        nums = pd.to_numeric(d[field], errors='coerce')
        if nums.isna().any() or (nums <= 0).any() or (nums != nums.round()).any():
            raise ValueError('SCHEMA_STOP_PLANTING_INVALID_POSITIVE_INTEGER_ID:'+field)
    if not d.survival.dropna().isin((0, 1)).all():
        raise ValueError('SCHEMA_STOP_PLANTING_UNKNOWN_SURVIVAL_CODE')
    if not d.site_type.isin(('absent', 'present')).all():
        raise ValueError('SCHEMA_STOP_PLANTING_UNKNOWN_NATURAL_STATUS')
    labels = sow_roster[KEY + ['site_type']].drop_duplicates()
    if labels.duplicated(KEY).any():
        raise ValueError('SCHEMA_STOP_SOWING_CONFLICTING_SITE_STATUS')
    annotated = d.merge(labels, on=KEY, how='left', validate='many_to_one',
                        indicator=True, suffixes=('_planting', '_sowing'))
    if (annotated['_merge'] != 'both').any():
        raise ValueError('SCHEMA_STOP_PLANTING_NOT_IN_SOWING_ROSTER')
    if (annotated.site_type_planting != annotated.site_type_sowing).any():
        raise ValueError('SCHEMA_STOP_PLANTING_SOWING_STATUS_CONFLICT')
    return d


def witness_matrix(sown: pd.DataFrame, planting: pd.DataFrame) -> dict:
    duplicate = sown.duplicated(KEY_SEED, keep=False)
    anomalous = sown.loc[duplicate, KEY_STATION].drop_duplicates()
    contaminated = set(map(tuple, anomalous.itertuples(index=False, name=None)))
    keep = ~sown[KEY_STATION].apply(tuple, axis=1).isin(contaminated)
    clean = sown.loc[keep]
    unprotected = clean.loc[clean.treatment == 'unprotected']

    sow_combos = sown[KEY + ['site_type']].drop_duplicates()
    if sow_combos.duplicated(KEY).any():
        raise ValueError('SCHEMA_STOP_INCONSISTENT_SOWING_NATURAL_STATUS')
    if len(sow_combos) != 40:
        raise ValueError('SCHEMA_STOP_SOWING_UNEXPECTED_COMBO_COUNT')

    planted_groups = {k:g for k,g in planting.groupby(KEY, sort=False)}
    sown_groups = {k:g for k,g in unprotected.groupby(KEY, sort=False)}
    combos = []
    for row in sow_combos.sort_values(KEY).itertuples(index=False):
        species, site, status = row.species, row.site, row.site_type
        k = (species, site)
        sow = sown_groups.get(k)
        plant = planted_groups.get(k)
        result = {'species':str(species), 'site':str(site),
                  'site_type':str(status), 'planting_sampled':plant is not None}
        if sow is None:
            raise ValueError('SCHEMA_STOP_NO_CLEAN_UNPROTECTED_SEEDS')
        result.update({
            'unprotected_sown_seed_rows':int(len(sow)),
            'unprotected_sown_first_summer_positive_records':int((sow.seedling_surv==1).sum()),
            'unprotected_sown_second_summer_positive_records':int((sow.sapling_surv_sd==1).sum()),
        })
        for stage, column in [('sown_unprotected_germ','germ'),
                              ('sown_unprotected_first_summer','seedling_surv'),
                              ('sown_unprotected_second_summer','sapling_surv_sd')]:
            result[stage] = bool((sow[column] == 1).any())
        result['planted_first_summer'] = (bool((plant.survival == 1).any())
                                          if plant is not None else None)
        result['planted_n'] = int(len(plant)) if plant is not None else None
        result['planted_known_survivors'] = int((plant.survival == 1).sum()) if plant is not None else None
        result['planted_unknown_survival'] = int(plant.survival.isna().sum()) if plant is not None else None
        result['cross_stage_class'] = (
            ('both_witnessed' if result['sown_unprotected_first_summer'] else 'planting_only_witnessed')
            if result['planted_first_summer'] else
            ('sown_only_witnessed' if result['sown_unprotected_first_summer'] else 'neither_confirmed')
            if plant is not None else 'not_planted'
        )
        combos.append(result)

    status_summary = {}
    for status in ('absent','present'):
        rows = [c for c in combos if c['site_type'] == status]
        observed = [c for c in rows if c['planting_sampled']]
        stage_counts = {stage:sum(c[stage] is True for c in rows) for stage in STAGES}
        stage_counts['planted_first_summer_among_planted'] = sum(c['planted_first_summer'] is True for c in observed)
        status_summary[status] = {
            'n_sown_species_patch_combinations':len(rows),
            'n_planted_species_patch_combinations':len(observed),
            'n_sown_unprotected_germination_witnesses':stage_counts['sown_unprotected_germ'],
            'n_sown_unprotected_first_summer_witnesses':stage_counts['sown_unprotected_first_summer'],
            'n_sown_unprotected_second_summer_witnesses':stage_counts['sown_unprotected_second_summer'],
            'n_planted_first_summer_witnesses':stage_counts['planted_first_summer_among_planted'],
            'n_planted_individuals':sum(c['planted_n'] or 0 for c in observed),
            'n_planted_known_survivors':sum(c['planted_known_survivors'] or 0 for c in observed),
            'n_planted_unknown_survival':sum(c['planted_unknown_survival'] or 0 for c in observed),
            'n_patches_with_planted_survival_witness':len({c['site'] for c in observed if c['planted_first_summer']}),
            'cross_stage_counts':{stage:sum(c['cross_stage_class']==stage for c in observed)
                                  for stage in ('both_witnessed','planting_only_witnessed',
                                                'sown_only_witnessed','neither_confirmed')},
            'n_patches_all_sown_combos':len({c['site'] for c in rows}),
        }
        assert sum(status_summary[status]['cross_stage_counts'].values()) == len(observed)
    return {
        'schema':'eog.mediterranean_sowing_planting_stage_witness_v1',
        'scientific_status':'POST_EXPOSURE_CROSS_STAGE_DIRECT_WITNESS_ONLY; SOWING_PRIMARY_SOURCE_QUALITY_STOP_UNCHANGED',
        'source_doi':DOI,
        'source_quality':{
            'sowing_duplicate_seed_key_groups':int(sown[duplicate].groupby(KEY_SEED).ngroups),
            'sowing_quarantined_rows_both_treatments':int((~keep).sum()),
            'planting_duplicate_individual_keys':0,
        },
        'n_sowing_species_patch_combinations':len(combos),
        'n_distinct_forest_patches':len({c['site'] for c in combos}),
        'n_planting_rows':len(planting),
        'status_summary':status_summary,
        'per_species_patch':combos,
        'interpretation_limits':[
            'Positive life-stage survival after human arrival bypass directly witnesses viability at planted microsites only.',
            'Missing or zero positive records cannot certify absolute ecological impossibility.',
            'Transplanted saplings and sown seeds bypass different life-history transitions; their survival rates cannot be equated.',
            'This is post-exposure follow-up to the published study and prior PR709, not an independent blinded external confirmation.',
            'Ten forest patches, not 299 saplings or 61000 seeds, bound geographic replication.',
            'Neither natural dispersal history nor the causal mechanism producing natural absence is identified.',
            'The original one-plot source anomaly blocks the complete primary sowing contrast, unchanged.'
        ],
    }


def run(source_zip:Path, manifest_path:Path, parent_receipt_path:Path) -> dict:
    digest = hashlib.sha256(source_zip.read_bytes()).hexdigest()
    if digest != EXPECTED_ARCHIVE_SHA256:
        raise ValueError('SOURCE_STOP_UPLOADED_ARCHIVE_SHA256_MISMATCH')
    data,members=safe_zip(source_zip)
    manifest=json.loads(manifest_path.read_text())
    if validate_official_manifest(members,manifest)['status']!='ALL_12_FILES_MATCH_OFFICIAL_DIGEST_AND_SIZE':
        raise ValueError('SOURCE_STOP_OFFICIAL_MANIFEST_MISMATCH')
    prior=json.loads(parent_receipt_path.read_text())
    if prior['provenance']['uploaded_zip_sha256']!=digest:
        raise ValueError('SOURCE_STOP_PARENT_SOURCE_RECEIPT_MISMATCH')
    sown=source_frame(data)
    old,_=calculate(sown)
    if old['strict_source_stop']['status']!='BLOCK_PRIMARY_GLOBAL_INFERENCE':
        raise ValueError('SOURCE_STOP_PARENT_QUALITY_GATE_CHANGED')
    if old['unaffected_natural_absence_witnesses']!=prior['unaffected_natural_absence_witnesses']:
        raise ValueError('SOURCE_STOP_PARENT_SOWING_WITNESSES_CHANGED')
    sow_labels=sown[KEY+['site_type']].drop_duplicates()
    planted=planting_frame(data['planting_experiment.csv'],sow_labels)
    report=witness_matrix(sown,planted)
    report['provenance']={
        'original_zip_sha256':digest,
        'planting_file_sha256':members['planting_experiment.csv']['sha256'],
        'sowing_file_sha256':members['sowing_experiment.csv']['sha256'],
        'source_and_parent_receipt_parity':True,
        'pre_planting_outcome_protocol_commit':'fee2041b2ef9aa09449b1c8538251ef5c92ca716',
    }
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source-zip',type=Path,required=True)
    p.add_argument('--official-manifest',type=Path,required=True)
    p.add_argument('--parent-receipt',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    args=p.parse_args()
    report=run(args.source_zip,args.official_manifest,args.parent_receipt)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/'result.json').write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n')
    pd.DataFrame(report['per_species_patch']).to_csv(args.output_dir/'cross_stage_40_species_patch.csv',index=False)
    print(json.dumps({k:report[k] for k in ('scientific_status','n_planting_rows','status_summary','source_quality')},indent=2))

if __name__=='__main__':main()