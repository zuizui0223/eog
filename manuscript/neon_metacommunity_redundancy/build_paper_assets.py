from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[2]
LANE = ROOT / "manuscript" / "neon_metacommunity_redundancy"
SITE_DATA = LANE / "site_metrics_v1.csv"
BEST_DATA = LANE / "best_species_frequency_v1.csv"
LOCK = (
    ROOT
    / "validation"
    / "neon_metacommunity_connectivity_v1"
    / "response_lock_v1.json"
)
CLOSURE = (
    ROOT
    / "validation"
    / "neon_metacommunity_connectivity_v1"
    / "programme_closure_v1.json"
)
OUT = LANE / "generated"


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def svg_header(width: int, height: int, title: str, description: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">\n'
        f'<title id="title">{escape(title)}</title>\n'
        f'<desc id="desc">{escape(description)}</desc>\n'
        '<rect width="100%" height="100%" fill="white"/>\n'
        '<style>'
        'text{font-family:Arial,Helvetica,sans-serif;fill:#111}'
        '.h{font-size:24px;font-weight:700}.s{font-size:16px;font-weight:700}'
        '.b{font-size:14px}.sm{font-size:12px}.xs{font-size:11px}'
        '.axis{stroke:#333;stroke-width:1.2}.grid{stroke:#ddd;stroke-width:1}'
        '.box{fill:#f5f5f5;stroke:#333;stroke-width:1.2}'
        '.dark{fill:#333}.mid{fill:#777}.light{fill:#bbb}'
        '.line{stroke:#555;stroke-width:2}.dash{stroke:#777;stroke-width:1.5;stroke-dasharray:5 5}'
        '</style>\n'
    )


def figure1_conceptual() -> str:
    width, height = 1250, 620
    parts = [svg_header(
        width, height,
        "Complementarity, redundancy and weakest-link outcomes",
        "Conceptual comparison of species pooling effects on spatial world survival."
    )]
    parts.append('<text x="55" y="42" class="h">Three ways species pooling can change spatial continuity</text>\n')
    panels = [
        (55, "A  Complementarity", "community > every species", "gain > 0"),
        (445, "B  Redundancy", "community = best species", "gain = 0"),
        (835, "C  Weakest-link", "community < best species", "gain < 0"),
    ]
    for x, title, line1, line2 in panels:
        parts.append(f'<rect x="{x}" y="85" width="335" height="430" rx="12" class="box"/>\n')
        parts.append(f'<text x="{x+18}" y="120" class="s">{escape(title)}</text>\n')
        parts.append(f'<text x="{x+18}" y="470" class="b">{escape(line1)}</text>\n')
        parts.append(f'<text x="{x+18}" y="495" class="sm">{escape(line2)}</text>\n')

    # Complementarity: alternating species bridge the full chain.
    nodes = [(105,230),(175,190),(245,230),(315,190)]
    for a,b in [(0,1),(1,2),(2,3)]:
        parts.append(f'<line x1="{nodes[a][0]}" y1="{nodes[a][1]}" x2="{nodes[b][0]}" y2="{nodes[b][1]}" class="line"/>\n')
    for i,(x,y) in enumerate(nodes):
        label = "A" if i % 2 == 0 else "B"
        parts.append(f'<circle cx="{x}" cy="{y}" r="17" class="dark"/>\n')
        parts.append(f'<text x="{x}" y="{y+5}" text-anchor="middle" fill="white" class="b">{label}</text>\n')
    parts.append('<text x="85" y="315" class="sm">neither species alone spans the chain</text>\n')

    # Redundancy: species A alone spans.
    nodes2 = [(495,230),(565,190),(635,230),(705,190)]
    for a,b in [(0,1),(1,2),(2,3)]:
        parts.append(f'<line x1="{nodes2[a][0]}" y1="{nodes2[a][1]}" x2="{nodes2[b][0]}" y2="{nodes2[b][1]}" class="line"/>\n')
    for x,y in nodes2:
        parts.append(f'<circle cx="{x}" cy="{y}" r="17" class="dark"/>\n')
        parts.append(f'<text x="{x}" y="{y+5}" text-anchor="middle" fill="white" class="b">A</text>\n')
    parts.append('<circle cx="565" cy="280" r="14" class="mid"/>\n')
    parts.append('<text x="565" y="285" text-anchor="middle" fill="white" class="sm">B</text>\n')
    parts.append('<text x="475" y="315" class="sm">species A already supplies continuity</text>\n')

    # Weakest link: best species spans, extra species adds unsupported node.
    nodes3 = [(885,230),(955,190),(1025,230),(1095,190)]
    for a,b in [(0,1),(1,2),(2,3)]:
        parts.append(f'<line x1="{nodes3[a][0]}" y1="{nodes3[a][1]}" x2="{nodes3[b][0]}" y2="{nodes3[b][1]}" class="line"/>\n')
    for x,y in nodes3:
        parts.append(f'<circle cx="{x}" cy="{y}" r="17" class="dark"/>\n')
        parts.append(f'<text x="{x}" y="{y+5}" text-anchor="middle" fill="white" class="b">A</text>\n')
    parts.append('<circle cx="1130" cy="330" r="17" class="mid"/>\n')
    parts.append('<text x="1130" y="335" text-anchor="middle" fill="white" class="b">B</text>\n')
    parts.append('<text x="865" y="365" class="sm">pooling adds a peripheral positive node</text>\n')
    parts.append('<text x="55" y="570" class="b">Observed programme: redundancy at 15 sites; weakest-link at ORNL; complementarity at 0 sites.</text>\n')
    parts.append('</svg>\n')
    return "".join(parts)


def figure2_site_pairing(rows: list[dict[str, str]]) -> str:
    width, height = 1300, 720
    left, right, top, bottom = 90, 55, 90, 125
    plot_w = width-left-right
    plot_h = height-top-bottom
    parts=[svg_header(
        width,height,
        "Community versus best-species spatial world survival across fresh NEON sites",
        "Paired pooled-community and best individual-species survival fractions at sixteen fresh sites."
    )]
    parts.append('<text x="55" y="42" class="h">Pooling species never increased spatial world survival</text>\n')
    for frac in [0,0.25,0.5,0.75,1]:
        y=top+plot_h*(1-frac)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" class="grid"/>\n')
        parts.append(f'<text x="47" y="{y+5:.1f}" class="b">{frac:.2f}</text>\n')
    n=len(rows)
    step=plot_w/n
    for i,row in enumerate(rows):
        x=left+step*(i+0.5)
        community=float(row["community_survival_fraction"])
        best=float(row["max_species_survival_fraction"])
        yc=top+plot_h*(1-community)
        yb=top+plot_h*(1-best)
        parts.append(f'<line x1="{x:.1f}" y1="{yc:.1f}" x2="{x:.1f}" y2="{yb:.1f}" stroke="#777" stroke-width="3"/>\n')
        parts.append(f'<circle cx="{x:.1f}" cy="{yb:.1f}" r="7" fill="white" stroke="#222" stroke-width="2"/>\n')
        parts.append(f'<circle cx="{x:.1f}" cy="{yc:.1f}" r="7" class="dark"/>\n')
        parts.append(f'<text x="{x:.1f}" y="{top+plot_h+28}" text-anchor="middle" class="xs">{escape(row["site_code"])}</text>\n')
    parts.append(f'<text x="{left}" y="{height-48}" class="sm">open = best individual species; filled = pooled target-species community</text>\n')
    parts.append(f'<text x="{width-440}" y="{height-48}" class="sm">positive emergent gain: 0 / 16 sites</text>\n')
    parts.append(f'<text x="{width-440}" y="{height-27}" class="sm">ORNL: community 0.25 vs best species 1.00</text>\n')
    parts.append('</svg>\n')
    return "".join(parts)


def _scatter_panel(
    parts: list[str],
    x0: int,
    y0: int,
    w: int,
    h: int,
    xs: list[float],
    ys: list[float],
    labels: list[str],
    title: str,
    xlabel: str,
    ylabel: str,
    note: str,
) -> None:
    min_x,max_x=min(xs),max(xs)
    min_y,max_y=min(ys),max(ys)
    pad_x=(max_x-min_x)*0.08 or 1.0
    pad_y=(max_y-min_y)*0.08 or 0.1
    lo_x,hi_x=min_x-pad_x,max_x+pad_x
    lo_y,hi_y=min_y-pad_y,max_y+pad_y
    parts.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="white" stroke="#bbb"/>\n')
    parts.append(f'<text x="{x0+10}" y="{y0+24}" class="s">{escape(title)}</text>\n')
    plot_left=x0+65; plot_right=x0+w-20; plot_top=y0+55; plot_bottom=y0+h-70
    parts.append(f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_right}" y2="{plot_bottom}" class="axis"/>\n')
    parts.append(f'<line x1="{plot_left}" y1="{plot_top}" x2="{plot_left}" y2="{plot_bottom}" class="axis"/>\n')
    for x,y,label in zip(xs,ys,labels,strict=True):
        px=plot_left+(x-lo_x)/(hi_x-lo_x)*(plot_right-plot_left)
        py=plot_bottom-(y-lo_y)/(hi_y-lo_y)*(plot_bottom-plot_top)
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" class="dark"/>\n')
        if label=="ORNL":
            parts.append(f'<text x="{px+7:.1f}" y="{py-7:.1f}" class="xs">ORNL</text>\n')
    parts.append(f'<text x="{(plot_left+plot_right)/2:.1f}" y="{y0+h-36}" text-anchor="middle" class="sm">{escape(xlabel)}</text>\n')
    parts.append(f'<text x="{x0+8}" y="{y0+h-12}" class="xs">{escape(ylabel)}</text>\n')
    parts.append(f'<text x="{x0+10}" y="{y0+h-52}" class="xs">{escape(note)}</text>\n')


def figure3_exploratory(rows: list[dict[str, str]], closure: dict) -> str:
    width,height=1300,650
    parts=[svg_header(
        width,height,
        "Exploratory richness, redundancy and heterospecific rescue",
        "Post hoc exploratory associations between site richness, number of individually saturated species, dominance coverage, and cross-species rescue."
    )]
    parts.append('<text x="55" y="42" class="h">Exploratory: richer sites carried more redundant continuity, not more rescue</text>\n')
    richness=[float(r["observed_target_species_count"]) for r in rows]
    saturated=[float(r["best_species_count"]) for r in rows]
    rescue=[float(r["cross_species_rescue_fraction"]) for r in rows]
    dominance=[float(r["dominance_coverage"]) for r in rows]
    labels=[r["site_code"] for r in rows]
    post=closure["posthoc_mechanism"]
    _scatter_panel(
        parts,45,85,390,500,richness,saturated,labels,
        "A  Richness → redundant species",
        "observed target-species richness",
        "individually saturated species count",
        f'post hoc Spearman rho={post["richness_vs_individually_saturated_species_count"]["spearman_rho"]:.3f}, p={post["richness_vs_individually_saturated_species_count"]["p"]:.4f}'
    )
    _scatter_panel(
        parts,455,85,390,500,richness,dominance,labels,
        "B  Richness → dominance",
        "observed target-species richness",
        "dominance coverage",
        f'post hoc Spearman rho={post["richness_vs_dominance_coverage"]["spearman_rho"]:.3f}, p={post["richness_vs_dominance_coverage"]["p"]:.4f}'
    )
    _scatter_panel(
        parts,865,85,390,500,richness,rescue,labels,
        "C  Richness → rescue",
        "observed target-species richness",
        "cross-species rescue fraction",
        f'post hoc Spearman rho={post["richness_vs_cross_species_rescue_fraction"]["spearman_rho"]:.3f}, p={post["richness_vs_cross_species_rescue_fraction"]["p"]:.3f}'
    )
    parts.append('<text x="55" y="625" class="sm">All three associations are explicitly post hoc exploratory and do not alter the preregistered primary result.</text>\n')
    parts.append('</svg>\n')
    return "".join(parts)


def figure4_ornl(rows: list[dict[str,str]]) -> str:
    ornl=next(row for row in rows if row["site_code"]=="ORNL")
    width,height=1050,560
    parts=[svg_header(
        width,height,
        "ORNL weakest-link pooling result",
        "At ORNL the best individual species survived all worlds while the pooled guild survived one quarter, illustrating how additional restricted occurrences can lower all-positive world survival."
    )]
    parts.append('<text x="55" y="42" class="h">ORNL: pooling taxa reduced spatial world survival</text>\n')
    x1,x2=230,690
    baseline=430
    scale=300
    best=float(ornl["max_species_survival_fraction"])
    community=float(ornl["community_survival_fraction"])
    for x,label,value in [(x1,"best individual species",best),(x2,"pooled community",community)]:
        h=value*scale
        parts.append(f'<rect x="{x-70}" y="{baseline-h:.1f}" width="140" height="{h:.1f}" class="dark"/>\n')
        parts.append(f'<text x="{x}" y="{baseline+32}" text-anchor="middle" class="b">{escape(label)}</text>\n')
        parts.append(f'<text x="{x}" y="{baseline-h-12:.1f}" text-anchor="middle" class="s">{value:.2f}</text>\n')
    parts.append(f'<line x1="120" y1="{baseline}" x2="850" y2="{baseline}" class="axis"/>\n')
    parts.append('<text x="55" y="500" class="b">Best species: Ochrotomys nuttalli, Oryzomys palustris, Reithrodontomys humulis</text>\n')
    parts.append('<text x="55" y="525" class="sm">Interpretation: pooling adds positive occurrences that must all satisfy the support rule, creating a weakest-link effect.</text>\n')
    parts.append('</svg>\n')
    return "".join(parts)


def validate(rows: list[dict[str,str]], best_rows: list[dict[str,str]], lock: dict, closure: dict) -> None:
    assert lock["denominator"] == {
        "fixed_sites":16,
        "scored_sites":16,
        "response_consumed_stops":0,
    }
    assert lock["primary"]["median_emergent_connectivity_gain"] == 0
    assert lock["primary"]["positive_null_adjusted_site_count"] == 0
    assert lock["primary"]["one_sided_sign_test_p"] == 1
    assert len(rows)==16
    assert sum(float(r["emergent_connectivity_gain"])>0 for r in rows)==0
    assert sum(float(r["community_survival_fraction"])==1 for r in rows)==15
    assert sum(float(r["max_species_survival_fraction"])==1 for r in rows)==16
    assert all(float(r["strict_emergent_world_fraction"])==0 for r in rows)
    ornl=next(r for r in rows if r["site_code"]=="ORNL")
    assert float(ornl["community_survival_fraction"])==0.25
    assert float(ornl["max_species_survival_fraction"])==1.0
    assert float(ornl["emergent_connectivity_gain"])==-0.75
    assert abs(float(closure["ecological_result"]["cross_species_rescue_fraction_median"])-0.002685173977948)<1e-15
    freq={r["species_name"]:int(r["sites_as_best_species"]) for r in best_rows}
    for name in ["Mus musculus","Peromyscus boylii","Reithrodontomys megalotis","Sigmodon hispidus"]:
        assert freq[name]==3


def write_supplement(rows: list[dict[str,str]], best_rows: list[dict[str,str]], lock: dict) -> list[Path]:
    paths=[]
    table1=OUT/"table_s1_site_metrics.csv"
    write_text(table1,SITE_DATA.read_text(encoding="utf-8"))
    paths.append(table1)
    table2=OUT/"table_s2_best_species_frequency.csv"
    write_text(table2,BEST_DATA.read_text(encoding="utf-8"))
    paths.append(table2)
    table3=OUT/"table_s3_response_integrity.txt"
    write_text(
        table3,
        "\n".join([
            "Fixed fresh sites: 16",
            "Scored sites: 16",
            "Response-consumed stops: 0",
            f"Authenticated query requests: {lock['response_consumption']['authenticated_query_requests']}",
            f"Response files: {lock['response_consumption']['selected_response_file_count']}",
            f"Biological response bytes: {lock['response_consumption']['biological_response_bytes_opened']}",
            "Model fits: 0",
            "Rerun allowed: false",
        ])+"\n",
    )
    paths.append(table3)
    return paths


def main() -> None:
    rows=load_csv(SITE_DATA)
    best_rows=load_csv(BEST_DATA)
    lock=json.loads(LOCK.read_text(encoding="utf-8"))
    closure=json.loads(CLOSURE.read_text(encoding="utf-8"))
    validate(rows,best_rows,lock,closure)
    OUT.mkdir(parents=True,exist_ok=True)
    assets={
        OUT/"figure_1_conceptual_outcomes.svg":figure1_conceptual(),
        OUT/"figure_2_community_vs_species.svg":figure2_site_pairing(rows),
        OUT/"figure_3_exploratory_redundancy.svg":figure3_exploratory(rows,closure),
        OUT/"figure_4_ornl_weakest_link.svg":figure4_ornl(rows),
    }
    for path,text in assets.items():
        write_text(path,text)
    supplement=write_supplement(rows,best_rows,lock)
    manifest={
        "schema":"eog.neon_metacommunity_redundancy.paper_assets.v1",
        "source_lock":str(LOCK.relative_to(ROOT)),
        "source_closure":str(CLOSURE.relative_to(ROOT)),
        "frozen_values":{
            "fixed_sites":16,
            "scored_sites":16,
            "positive_emergent_gain_sites":0,
            "community_survival_one_sites":15,
            "best_species_survival_one_sites":16,
            "strict_emergent_world_positive_sites":0,
            "ORNL_community_survival_fraction":0.25,
            "ORNL_best_species_survival_fraction":1.0,
            "cross_species_rescue_median":closure["ecological_result"]["cross_species_rescue_fraction_median"],
            "dominance_coverage_median":closure["ecological_result"]["dominance_coverage_median"],
        },
        "files":{},
    }
    for path in [*assets.keys(),*supplement]:
        raw=path.read_bytes()
        try:
            key=str(path.relative_to(ROOT))
        except ValueError:
            key=f"generated/{path.name}"
        manifest["files"][key]={"bytes":len(raw),"sha256":sha256_bytes(raw)}
    write_text(OUT/"asset_manifest_v1.json",json.dumps(manifest,indent=2,sort_keys=True)+"\n")


if __name__=="__main__":
    main()
