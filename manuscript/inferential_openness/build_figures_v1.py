#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import html
import json
from collections import Counter
from pathlib import Path

GROUPS={
 "Transport / source identity":{
   "source_transport","bounded_archive_transport","metadata_identity_or_transport",
   "metadata_identity_or_interface","response_blind_archive_range_transport",
   "response_blind_zip_presign_transport","source_transport_dns"
 },
 "Registry / geometry / time":{
   "publication_registry_reproduction","geometry_registry","temporal_registry",
   "response_independent_calendar_value","response_independent_geometry_registry",
   "temporal_context_estimability"
 },
 "Separation / linkage / schema":{
   "physical_source_separation","response_linkage","response_header",
   "response_blind_zip_inventory","response_blind_physical_header_schema",
   "full_response_schema_or_linkage"
 },
 "Semantic / covariate validity":{
   "surveyed_negative_semantics","response_independent_baseline_covariate_value"
 },
}

def esc(x): return html.escape(str(x))

def svg_start(w,h,title):
    return [
      f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
      f'<title>{esc(title)}</title>',
      '<rect width="100%" height="100%" fill="white"/>',
      '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#111} .small{font-size:13px}.mid{font-size:17px}.big{font-size:24px;font-weight:700}.box{fill:#f3f4f6;stroke:#333;stroke-width:1.4}.line{stroke:#555;stroke-width:2}.bar{fill:#777}.accent{fill:#333}</style>'
    ]

def write_svg(path,parts):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text("\n".join(parts+["</svg>"])+"\n",encoding="utf-8")

def read_flow(path):
    with open(path,newline="",encoding="utf-8") as fh:
        return list(csv.DictReader(fh))

def fig1(out):
    stages=[
      ("1","Exact source","bytes/version retrievable"),
      ("2","Registry","site/geometry/time reconstructable"),
      ("3","Linkage","response linked to opportunity units"),
      ("4","Semantics","zero means surveyed negative"),
      ("5","Calibration","negative state identifiable"),
    ]
    p=svg_start(1200,330,"Inferential-openness ladder")
    p.append('<text x="600" y="38" text-anchor="middle" class="big">From public data to claim-ready inference</text>')
    x=55
    for i,(n,title,sub) in enumerate(stages):
        p.append(f'<rect x="{x}" y="105" width="190" height="105" rx="10" class="box"/>')
        p.append(f'<text x="{x+95}" y="135" text-anchor="middle" class="big">{n}</text>')
        p.append(f'<text x="{x+95}" y="162" text-anchor="middle" class="mid">{esc(title)}</text>')
        p.append(f'<text x="{x+95}" y="188" text-anchor="middle" class="small">{esc(sub)}</text>')
        if i<len(stages)-1:
            p.append(f'<line x1="{x+190}" y1="157" x2="{x+220}" y2="157" class="line"/>')
            p.append(f'<polygon points="{x+220},157 {x+210},151 {x+210},163" class="accent"/>')
        x+=225
    p.append('<text x="600" y="265" text-anchor="middle" class="mid">Inferential openness is claim-specific: a data–claim pairing must pass the whole chain.</text>')
    write_svg(out/"figure1_inferential_openness_ladder.svg",p)

def fig2(flow,out):
    stops=[r for r in flow if r["classification"]=="scientific_protocol_stop"]
    counts={}
    for name,labels in GROUPS.items():
        counts[name]=sum(r["terminal_stage"] in labels for r in stops)
    p=svg_start(950,510,"Prospective candidate funnel")
    p.append('<text x="475" y="38" text-anchor="middle" class="big">Prospective candidate funnel</text>')
    p.append('<text x="140" y="95" text-anchor="middle" class="big">34</text>')
    p.append('<text x="140" y="120" text-anchor="middle" class="mid">scientific attempts</text>')
    p.append('<line x1="240" y1="108" x2="350" y2="108" class="line"/>')
    p.append('<text x="430" y="92" text-anchor="middle" class="big">31</text>')
    p.append('<text x="430" y="118" text-anchor="middle" class="mid">terminal STOPs</text>')
    p.append('<text x="735" y="92" text-anchor="middle" class="big">3</text>')
    p.append('<text x="735" y="118" text-anchor="middle" class="mid">scored endpoints</text>')
    p.append('<line x1="510" y1="108" x2="625" y2="108" class="line"/>')
    maxv=max(counts.values())
    y=185
    for name,value in counts.items():
        width=420*value/maxv
        p.append(f'<text x="35" y="{y+20}" class="mid">{esc(name)}</text>')
        p.append(f'<rect x="360" y="{y}" width="{width:.1f}" height="28" class="bar"/>')
        p.append(f'<text x="{370+width:.1f}" y="{y+21}" class="mid">{value}</text>')
        y+=68
    p.append('<text x="475" y="485" text-anchor="middle" class="small">3 administrative records are excluded from the scientific denominator.</text>')
    write_svg(out/"figure2_eog_candidate_funnel.svg",p)

def fig3(flow,out):
    stops=[r for r in flow if r["classification"]=="scientific_protocol_stop"]
    c=Counter(r["biological_response_access"] for r in stops)
    labels=[("No response access","none"),("Header only","header_only"),("Full response once","full_response_once")]
    p=svg_start(850,470,"Response access at terminal STOP")
    p.append('<text x="425" y="40" text-anchor="middle" class="big">Where did STOPs occur relative to response access?</text>')
    maxv=max(c[k] for _,k in labels)
    x=120
    for label,key in labels:
        value=c[key]
        h=270*value/maxv
        y=365-h
        p.append(f'<rect x="{x}" y="{y:.1f}" width="130" height="{h:.1f}" class="bar"/>')
        p.append(f'<text x="{x+65}" y="{y-12:.1f}" text-anchor="middle" class="big">{value}</text>')
        p.append(f'<text x="{x+65}" y="397" text-anchor="middle" class="small">{esc(label)}</text>')
        x+=240
    p.append('<text x="425" y="445" text-anchor="middle" class="mid">30/31 stopped before response row values contributed to scoring.</text>')
    write_svg(out/"figure3_response_access.svg",p)

def fig4(ledger,out):
    vals=[
      ("Candidates screened",ledger["level_c_284b"]["architecture_screened_candidates"]),
      ("Architecture-qualified",ledger["level_c_284b"]["architecture_qualified_candidates"]),
      ("Calibration passes",ledger["level_c_284b"]["candidate_specific_calibration_passed"]),
      ("Hard endpoints opened",ledger["level_c_284b"]["focal_value_opening_authorized"]),
    ]
    p=svg_start(1000,340,"Biological-relation calibration funnel")
    p.append('<text x="500" y="38" text-anchor="middle" class="big">Later inferential barrier: negative-state calibration</text>')
    x=45
    for i,(label,value) in enumerate(vals):
        p.append(f'<rect x="{x}" y="115" width="190" height="100" rx="10" class="box"/>')
        p.append(f'<text x="{x+95}" y="155" text-anchor="middle" class="big">{value}</text>')
        p.append(f'<text x="{x+95}" y="187" text-anchor="middle" class="small">{esc(label)}</text>')
        if i<len(vals)-1:
            p.append(f'<line x1="{x+190}" y1="165" x2="{x+235}" y2="165" class="line"/>')
            p.append(f'<polygon points="{x+235},165 {x+225},159 {x+225},171" class="accent"/>')
        x+=240
    p.append('<text x="500" y="270" text-anchor="middle" class="mid">0/2 retained systems had independent calibration sufficient to identify F=false.</text>')
    p.append('<text x="500" y="300" text-anchor="middle" class="small">Unresolved negative state ≠ biological absence.</text>')
    write_svg(out/"figure4_level_c_calibration_funnel.svg",p)

def graphical_abstract(out):
    p=svg_start(1200,560,"Graphical abstract: from public data to claim-ready inference")
    p.append('<text x="600" y="42" text-anchor="middle" class="big">Open data become claim-ready only when the evidence chain is reproducible</text>')

    stages=[
      ("PUBLIC DATA",""),
      ("1. Source","exact bytes / version"),
      ("2. Registry","opportunity units"),
      ("3. Linkage","response ↔ units"),
      ("4. Semantics","negative vs missing"),
      ("5. Calibration","absence vs non-detection"),
      ("CLAIM-READY","INFERENCE"),
    ]
    x=30
    widths=[145,145,145,145,145,145,160]
    for i,((title,sub),w) in enumerate(zip(stages,widths)):
        fill="#ffffff" if i in {0,len(stages)-1} else "#f3f4f6"
        p.append(f'<rect x="{x}" y="100" width="{w}" height="92" rx="10" fill="{fill}" stroke="#333" stroke-width="1.5"/>')
        p.append(f'<text x="{x+w/2}" y="136" text-anchor="middle" class="mid">{esc(title)}</text>')
        if sub:
            parts=sub.split("|")
            if len(parts)==1:
                p.append(f'<text x="{x+w/2}" y="163" text-anchor="middle" class="small">{esc(sub)}</text>')
            else:
                for j,line in enumerate(parts):
                    p.append(f'<text x="{x+w/2}" y="{157+17*j}" text-anchor="middle" class="small">{esc(line)}</text>')
        if i<len(stages)-1:
            p.append(f'<line x1="{x+w}" y1="146" x2="{x+w+18}" y2="146" class="line"/>')
            p.append(f'<polygon points="{x+w+18},146 {x+w+9},140 {x+w+9},152" class="accent"/>')
        x+=w+18

    p.append('<text x="265" y="250" text-anchor="middle" class="big">Prospective workflow denominator</text>')
    p.append('<text x="265" y="288" text-anchor="middle" class="mid">34 attempts → 31 STOPs → 3 scored endpoints</text>')
    p.append('<text x="265" y="320" text-anchor="middle" class="small">11 source/transport · 10 registry/time · 8 linkage/schema · 2 semantics/covariates</text>')
    p.append('<text x="265" y="350" text-anchor="middle" class="small">29 no response · 1 header only · 1 full response once</text>')
    p.append('<text x="265" y="380" text-anchor="middle" class="mid">30/31 STOPs before response row values contributed to scoring</text>')

    p.append('<line x1="585" y1="235" x2="585" y2="430" stroke="#aaa" stroke-width="1.5"/>')

    p.append('<text x="870" y="250" text-anchor="middle" class="big">Later negative-state barrier</text>')
    p.append('<text x="870" y="292" text-anchor="middle" class="mid">Biological-relation audit: 12 → 2 → 0 → 0</text>')
    p.append('<text x="870" y="324" text-anchor="middle" class="small">screened → architecture-qualified → calibrated negatives → opened endpoints</text>')
    p.append('<text x="870" y="370" text-anchor="middle" class="mid">Unresolved non-detection ≠ biological absence</text>')

    p.append('<text x="600" y="500" text-anchor="middle" class="mid">Prospective STOP rules make normally invisible abandoned reuse attempts measurable.</text>')
    write_svg(out/"graphical_abstract_inferential_openness.svg",p)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidate-flow",type=Path,required=True)
    ap.add_argument("--ledger",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args()
    flow=read_flow(a.candidate_flow)
    ledger=json.loads(a.ledger.read_text(encoding="utf-8"))
    fig1(a.output_dir)
    fig2(flow,a.output_dir)
    fig3(flow,a.output_dir)
    fig4(ledger,a.output_dir)
    graphical_abstract(a.output_dir)
    stops=[r for r in flow if r["classification"]=="scientific_protocol_stop"]
    grouped_barriers={
      name:sum(r["terminal_stage"] in labels for r in stops)
      for name,labels in GROUPS.items()
    }
    response_access=Counter(r["biological_response_access"] for r in stops)

    # Submission-facing supplementary table: the complete prospective STOP denominator.
    supplement=a.output_dir/"supplementary_table_S1_terminal_stops.csv"
    with supplement.open("w",newline="",encoding="utf-8") as fh:
        fields=[
          "issue","system","terminal_stage","terminal_status_or_reason",
          "biological_response_access"
        ]
        writer=csv.DictWriter(fh,fieldnames=fields)
        writer.writeheader()
        for row in stops:
            writer.writerow({key:row[key] for key in fields})

    manifest={
      "figures":[p.name for p in sorted(a.output_dir.glob("figure*.svg"))],
      "graphical_abstract":"graphical_abstract_inferential_openness.svg",
      "supplementary_table":supplement.name,
      "scientific_attempts":sum(r["classification"] in {"predictive_result","scientific_protocol_stop"} for r in flow),
      "scientific_stops":len(stops),
      "scored_endpoints":sum(r["classification"]=="predictive_result" for r in flow),
      "administrative_exclusions":sum(r["classification"]=="administrative_exclusion" for r in flow),
      "grouped_barriers":grouped_barriers,
      "response_access_among_stops":{
        "none":response_access["none"],
        "header_only":response_access["header_only"],
        "full_response_once":response_access["full_response_once"],
      },
      "level_c_284b":{
        "architecture_screened_candidates":ledger["level_c_284b"]["architecture_screened_candidates"],
        "architecture_qualified_candidates":ledger["level_c_284b"]["architecture_qualified_candidates"],
        "candidate_specific_calibration_passed":ledger["level_c_284b"]["candidate_specific_calibration_passed"],
        "focal_value_opening_authorized":ledger["level_c_284b"]["focal_value_opening_authorized"],
      },
    }
    (a.output_dir/"figure_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(manifest,indent=2))

if __name__=="__main__":
    main()
