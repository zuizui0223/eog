"""Fail-closed native wetland amphibian survey-ID conflict and repeated-visit gate."""
import argparse,csv,hashlib,json
from collections import defaultdict
from pathlib import Path
SURVEY_SHA="45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd"
SITE_SHA="93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319"
META={"doy","surv","site","date","method","num","0","year","month","temp","humid","prec"}
PROTOCOL="25e040c1655a3ddbc449d3afe927e18f00079fc9"

def load(path):
    with Path(path).open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        return list(reader),reader.fieldnames

def analyze(surveys_path,sites_path):
    if hashlib.sha256(Path(surveys_path).read_bytes()).hexdigest()!=SURVEY_SHA:raise ValueError("survey source SHA drift")
    if hashlib.sha256(Path(sites_path).read_bytes()).hexdigest()!=SITE_SHA:raise ValueError("site source SHA drift")
    surveys,columns=load(surveys_path);sites,_=load(sites_path)
    species=[c for c in columns if c not in META]
    groups=defaultdict(list);opportunities=defaultdict(list)
    for i,row in enumerate(surveys,2):
        groups[row["surv"]].append((i,row))
        opportunities[(row["site"],row["date"],row["method"])].append((i,row))
    duplicates=[]
    for sid,entries in sorted(groups.items()):
        if len(entries)<2:continue
        identity_keys=("site","date","method","num","temp","humid","prec")
        matching_identity=all(all(r[k]==entries[0][1][k] for k in identity_keys) for _,r in entries)
        conflicting={sp:[r[sp] for _,r in entries] for sp in species
                     if len({r[sp] for _,r in entries})>1}
        duplicates.append({"survey_id":sid,"line_numbers":[i for i,_ in entries],
                           "same_identity_fields":matching_identity,
                           "species_conflicts":conflicting,
                           "raw_species_vectors":[{sp:r[sp] for sp in species} for _,r in entries],
                           "classification":"CONFLICTING_COUNTS" if conflicting else "IDENTICAL_SPECIES_COUNTS"})
    site_method_dates=defaultdict(set)
    for r in surveys:site_method_dates[(r["site"],r["method"])].add(r["date"])
    repeated=sum(len(v)>=2 for v in site_method_dates.values())
    conflicts=sum(d["classification"]=="CONFLICTING_COUNTS" for d in duplicates)
    result={"schema":"eog.wetland_duplicate_gate_v1.result",
            "status":"BLOCKED_CONFLICTING_SURVEY_IDENTIFIERS" if conflicts else "SOURCE_IDENTITY_GATE_PASSED_ONLY",
            "protocol_commit":PROTOCOL,"survey_sha256":SURVEY_SHA,"site_sha256":SITE_SHA,
            "site_rows":len(sites),"survey_rows":len(surveys),
            "species_columns":species,"unique_survey_ids":len(groups),
            "duplicate_survey_ids":len(duplicates),
            "duplicate_extra_rows":sum(len(v)-1 for v in groups.values()),
            "conflicting_duplicate_ids":conflicts,"duplicates":duplicates,
            "unique_site_date_method_opportunities":len(opportunities),
            "site_date_method_groups_with_multiple_rows":sum(len(v)>1 for v in opportunities.values()),
            "site_method_groups_with_repeated_dates":repeated,
            "readiness":{"native_identity_conflicts_resolved":conflicts==0,
                         "effort_standardized":False,
                         "closure_verified":False,
                         "zero_means_true_nondetection_verified":False,
                         "occupancy_model_permitted":False},
            "next_action":"Adjudicate the two conflicting survey identifiers from native sampling metadata; do not drop, sum, or maximize rows without evidence.",
            "limitations":["Method label and num=1 are not verified equal detection effort across methods.",
                           "Repeated dates are opportunities, not verified closure.",
                           "No ecological effect, A/B/M or EOG-WF endpoint."]}
    result["fingerprint"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--surveys",type=Path,required=True)
    p.add_argument("--sites",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();r=analyze(a.surveys,a.sites)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
    print("WETLAND_DUPLICATE_GATE="+json.dumps(r,sort_keys=True))
