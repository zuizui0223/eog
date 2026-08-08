"""Execute the pre-outcome-frozen A-Islands bottleneck secondary analysis."""
from __future__ import annotations

import argparse, csv, json
from pathlib import Path
import numpy as np

import run_aislands_authoritative_benchmark as runner
import run_aislands_authoritative_benchmark_fast as fast
from eog.conditional_reachability import _rank_bins
from eog.prepared_island_bottleneck import prepare_island_bottleneck, evaluate_prepared_bottleneck
from eog.support_model import SupportModelError, fit_penalized_logistic_support

BOOTSTRAP_REPLICATES = 10_000
SIGN_FLIP_REPLICATES = 100_000
RANDOM_SEED = 20260808
_CACHE = {}


def _conditional_bottleneck(labels, support, distance, bottleneck):
    y = np.asarray(labels, dtype=int)
    support = np.asarray(support, dtype=float)
    distance = np.asarray(distance, dtype=float)
    bottleneck = np.asarray(bottleneck, dtype=float)
    sb = _rank_bins(support, 5)
    db = _rank_bins(distance, 5)
    numerator = 0.0; denominator = 0; informative = 0
    # Direction was frozen before outcomes: smaller bottleneck is better, so score=-bottleneck.
    score = -bottleneck
    finite = np.isfinite(score)
    for s in range(5):
        for d in range(5):
            mask = (sb == s) & (db == d) & finite
            pos = score[mask & (y == 1)]
            neg = score[mask & (y == 0)]
            if pos.size == 0 or neg.size == 0:
                continue
            informative += 1
            delta = pos[:, None] - neg[None, :]
            numerator += float(np.sum(delta > 0) + 0.5 * np.sum(delta == 0))
            denominator += int(delta.size)
    return (None if denominator == 0 else numerator / denominator), denominator, informative, int(np.sum(finite))


def _summary(values):
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(RANDOM_SEED)
    bootstrap = np.mean(rng.choice(values, size=(BOOTSTRAP_REPLICATES, len(values)), replace=True), axis=1)
    centered = values - 0.5
    obs = abs(float(np.mean(centered))); exceed = 0
    for start in range(0, SIGN_FLIP_REPLICATES, 1000):
        size = min(1000, SIGN_FLIP_REPLICATES - start)
        signs = rng.choice(np.array([-1.0, 1.0]), size=(size, len(values)))
        exceed += int(np.sum(np.abs(np.mean(signs * centered[None, :], axis=1)) >= obs))
    return {
        "n_species_estimable": int(len(values)),
        "mean_conditional_concordance": float(np.mean(values)),
        "bootstrap_95_ci": [float(np.quantile(bootstrap, .025)), float(np.quantile(bootstrap, .975))],
        "sign_flip_two_sided_p": float((exceed + 1) / (SIGN_FLIP_REPLICATES + 1)),
    }


def _write(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as h:
        w = csv.DictWriter(h, fieldnames=fields); w.writeheader(); w.writerows(rows)


def run(island_data, species_data, cohort, folds, climate, fold_output, species_output, summary_output):
    hashes = {k: runner._sha256(v) for k, v in {"cohort":cohort,"folds":folds,"climate":climate,"island_data":island_data,"species_data":species_data}.items()}
    if hashes['cohort'] != runner.FROZEN_COHORT_SHA256 or hashes['folds'] != runner.FROZEN_FOLDS_SHA256 or hashes['climate'] != runner.FROZEN_CLIMATE_SHA256:
        raise ValueError('frozen pre-outcome SHA-256 mismatch')
    islands=runner._read(island_data); species_rows=runner._read(species_data); cohort_rows=runner._read(cohort); fold_rows=runner._read(folds); climate_rows=runner._read(climate)
    il=runner._col(islands,'List_ID','list_ID'); ii=runner._col(islands,'Island_ID','island_ID')
    sl=runner._col(species_rows,'List_ID','list_ID'); sn=runner._col(species_rows,'Species_update','species_update'); cn=runner._col(cohort_rows,'species')
    fi=runner._col(fold_rows,'island_id'); fc=runner._col(fold_rows,'fold'); xc=runner._col(fold_rows,'x'); yc=runner._col(fold_rows,'y'); ci=runner._col(climate_rows,'island_id')
    cc=[runner._col(climate_rows,p) for p in runner.PREDICTORS]
    l2i={runner._canonical_id(r[il]):runner._canonical_id(r[ii]) for r in islands}
    surveyed=sorted({l2i[runner._canonical_id(r[sl])] for r in species_rows},key=int)
    folds_by={runner._canonical_id(r[fi]):int(r[fc]) for r in fold_rows}; coords={runner._canonical_id(r[fi]):(float(r[yc]),float(r[xc])) for r in fold_rows}
    climate_by={runner._canonical_id(r[ci]):np.asarray([float(r[c]) for c in cc]) for r in climate_rows}
    taxa=sorted({r[cn].strip() for r in cohort_rows if r[cn].strip()});
    if len(taxa)!=886: raise ValueError(f'expected 886 taxa, got {len(taxa)}')
    presence={t:set() for t in taxa}; taxset=set(taxa)
    for r in species_rows:
        if r[sn].strip() in taxset: presence[r[sn].strip()].add(l2i[runner._canonical_id(r[sl])])
    nodes=tuple(surveyed); x=np.vstack([climate_by[n] for n in nodes]); lat=np.array([coords[n][0] for n in nodes]); lon=np.array([coords[n][1] for n in nodes]); fv=np.array([folds_by[n] for n in nodes])
    prepared={}
    for fold in range(1,6):
        training=fv!=fold
        prepared[fold]=prepare_island_bottleneck(nodes,lat,lon,x,training)
    fold_rows_out=[]; species_rows_out=[]; species_values=[]
    for taxon in taxa:
        labels=np.array([int(n in presence[taxon]) for n in nodes]); vals=[]
        for fold in range(1,6):
            held=fv==fold; training=~held; anchors=training & (labels==1)
            rec={"species":taxon,"fold":fold,"evaluable":0,"concordance":"","comparable_pairs":0,"informative_strata":0,"finite_bottleneck_islands":0,"failure":""}
            try:
                model=fit_penalized_logistic_support(x[training],labels[training],l2_penalty=1.0,min_class_count=5); support=model.predict_support(x)
                if np.sum(anchors)<5: raise ValueError('fewer than five training-presence anchors')
                nearest,bottleneck=evaluate_prepared_bottleneck(prepared[fold],anchors)
                value,pairs,strata,nfinite=_conditional_bottleneck(labels[held],support[held],nearest[held],bottleneck[held])
                rec.update(comparable_pairs=pairs,informative_strata=strata,finite_bottleneck_islands=nfinite)
                if value is None: rec['failure']='no finite comparable presence-absence pairs within frozen 5x5 strata'
                else: rec.update(evaluable=1,concordance=value); vals.append(float(value))
            except (SupportModelError,ValueError,np.linalg.LinAlgError) as exc: rec['failure']=str(exc)
            fold_rows_out.append(rec)
        sv=None if not vals else float(np.mean(vals)); species_rows_out.append({"species":taxon,"estimable_folds":len(vals),"conditional_bottleneck_concordance":"" if sv is None else sv})
        if sv is not None: species_values.append(sv)
    summary=_summary(species_values)
    summary.update({"status":"predeclared_bottleneck_secondary_execution","null":0.5,"evaluation_score":"negative_median_normalized_geographic_bottleneck","input_sha256":hashes,"contract":"benchmarks/aislands_bottleneck_secondary_contract.json","claim_boundary":"Structural bottleneck information conditional on frozen pointwise support and nearest-anchor distance; not dispersal probability or realized pathway."})
    _write(fold_output,fold_rows_out,["species","fold","evaluable","concordance","comparable_pairs","informative_strata","finite_bottleneck_islands","failure"])
    _write(species_output,species_rows_out,["species","estimable_folds","conditional_bottleneck_concordance"])
    summary_output.parent.mkdir(parents=True,exist_ok=True); summary_output.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    return summary


def main():
    p=argparse.ArgumentParser()
    for name in ('island-data','species-data','cohort','folds','climate','fold-output','species-output','summary-output'): p.add_argument('--'+name,type=Path,required=True)
    print(json.dumps(run(**{k.replace('-','_'):v for k,v in vars(p.parse_args()).items()}),indent=2,sort_keys=True))
if __name__=='__main__': main()
