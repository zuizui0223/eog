"""Source qualification for public amphibian wetland repeated surveys; no model fitting."""
import argparse,csv,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path

def read(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))
def qualify(site_path,survey_path):
    sites=read(site_path);surveys=read(survey_path)
    if not sites or not surveys:raise ValueError("empty source")
    required_sites={"site","ci","depth","cover_submers","cover_emerged","plant_sp","fish"}
    required_surveys={"site","surv","date","method","num","temp","humid","prec"}
    if not required_sites.issubset(sites[0]) or not required_surveys.issubset(surveys[0]):
        raise ValueError("unexpected native source columns")
    ids=[r["site"] for r in sites]
    if len(set(ids))!=len(ids):raise ValueError("duplicate site")
    orphans=sorted({r["site"] for r in surveys}-set(ids))
    if orphans:raise ValueError("survey orphan sites: "+repr(orphans[:8]))
    surv_ids=[r["surv"] for r in surveys]
    dup=len(surv_ids)-len(set(surv_ids))
    site_dates=defaultdict(set);site_method_dates=defaultdict(set)
    for r in surveys:
        site_dates[r["site"]].add(r["date"])
        site_method_dates[(r["site"],r["method"])].add(r["date"])
    species_cols=[x for x in surveys[0] if x not in
                  {"doy","surv","site","date","method","num","0","year","month","temp","humid","prec"}]
    species_positive=Counter();species_zero=Counter()
    for r in surveys:
        for sp in species_cols:
            value=r[sp].strip()
            if value=="" :continue
            try:v=float(value)
            except ValueError:raise ValueError("non-numeric species count")
            if v<0:raise ValueError("negative count")
            if v>0:species_positive[sp]+=1
            else:species_zero[sp]+=1
    report={"schema":"eog.wetland_amphibian_source_qualification_v1.result",
            "status":"SOURCE_STRUCTURE_ONLY_NOT_OCCUPANCY_READY",
            "source":{"repo":"zuizui0223/frogcs",
                      "commit":"5e2f0a87c639df373fa2700b29403d2ab417a1cc",
                      "site_sha256":hashlib.sha256(Path(site_path).read_bytes()).hexdigest(),
                      "survey_sha256":hashlib.sha256(Path(survey_path).read_bytes()).hexdigest()},
            "site_rows":len(sites),"survey_rows":len(surveys),
            "unique_survey_ids":len(set(surv_ids)),"duplicate_survey_ids":dup,
            "methods":dict(sorted(Counter(r["method"] for r in surveys).items())),
            "sites_with_multiple_dates":sum(len(v)>=2 for v in site_dates.values()),
            "site_method_groups_with_multiple_dates":sum(len(v)>=2 for v in site_method_dates.values()),
            "species_columns":species_cols,"positive_survey_rows_by_species":dict(species_positive),
            "zero_survey_rows_by_species":dict(species_zero),
            "site_environment_missing":{k:sum(not r[k].strip() for r in sites)
                                        for k in sorted(required_sites-{"site"})},
            "survey_covariate_missing":{k:sum(not r[k].strip() for r in surveys)
                                       for k in ("num","temp","humid","prec")},
            "limits":["Source structure and repeated dates alone do not establish comparable effort or closure.",
                      "Site environment variables are observed associations, not independent A/B/M.",
                      "No model fitting, EOG geometry or EOG-WF endpoint."]}
    report["fingerprint"]=hashlib.sha256(json.dumps(report,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return report
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--sites",type=Path,required=True)
    p.add_argument("--surveys",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();r=qualify(a.sites,a.surveys)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print("WETLAND_SOURCE_QUALIFICATION="+json.dumps(r,sort_keys=True))
