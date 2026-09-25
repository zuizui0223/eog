from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[2]
LANE = ROOT / "manuscript" / "world_survival_identifiability"
DATA = LANE / "figure_data_scored_sites_v1.csv"
LOCK = ROOT / "validation" / "world_survival_regime_v2" / "neon_small_mammal_response_lock_v2_3.json"
OUT = LANE / "generated"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def svg_header(width: int, height: int, title: str, desc: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">\n'
        f'<title id="title">{escape(title)}</title>\n'
        f'<desc id="desc">{escape(desc)}</desc>\n'
        '<rect width="100%" height="100%" fill="white"/>\n'
        '<style>'
        'text{font-family:Arial,Helvetica,sans-serif;fill:#111}'
        '.h{font-size:24px;font-weight:700}.s{font-size:16px;font-weight:700}'
        '.b{font-size:14px}.sm{font-size:12px}.axis{stroke:#333;stroke-width:1.2}'
        '.grid{stroke:#ddd;stroke-width:1}.box{fill:#f5f5f5;stroke:#333;stroke-width:1.2}'
        '.dark{fill:#333}.mid{fill:#777}.light{fill:#bbb}.link{stroke:#555;stroke-width:2}'
        '.dash{stroke:#777;stroke-width:1.5;stroke-dasharray:5 5}'
        '</style>\n'
    )


def build_figure1() -> str:
    width, height = 1200, 640
    x1, x2, x3 = 70, 445, 820
    w, h = 300, 390
    parts = [svg_header(
        width, height,
        "Structural adequacy versus evidence-driven survival",
        "Three-stage conceptual diagram separating response-blind world construction from response-conditioned world survival."
    )]
    parts.append('<text x="60" y="42" class="h">Structural testability is not predictable contraction</text>\n')
    for x, label in [(x1, "A  Response-blind adequacy"), (x2, "B  Frozen world set"), (x3, "C  Positive evidence")]:
        parts.append(f'<rect x="{x}" y="90" width="{w}" height="{h}" rx="12" class="box"/>\n')
        parts.append(f'<text x="{x+18}" y="125" class="s">{escape(label)}</text>\n')
    parts.append(f'<text x="{x1+18}" y="170" class="b">Node registry</text>\n')
    for i,(cx,cy) in enumerate([(130,210),(210,180),(285,225),(170,300),(270,330)]):
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="10" class="dark"/>\n')
    parts.append(f'<text x="{x1+18}" y="375" class="b">Adequacy-complete ladder</text>\n')
    parts.append(f'<text x="{x1+18}" y="405" class="b">LCC + isolation gate</text>\n')
    parts.append(f'<text x="{x1+18}" y="445" class="sm">Uses no biological response</text>\n')

    for i,y in enumerate([180,245,310,375]):
        parts.append(f'<rect x="{x2+55}" y="{y}" width="190" height="38" rx="7" fill="white" stroke="#555"/>\n')
        parts.append(f'<text x="{x2+70}" y="{y+25}" class="b">world {i+1}</text>\n')
    parts.append(f'<text x="{x2+18}" y="445" class="sm">Exact identities retained for audit</text>\n')

    nodes=[(875,200),(965,165),(1065,215),(900,320),(1010,340),(1080,300)]
    edges=[(0,1),(1,2),(0,3),(3,4),(4,5),(2,5),(1,4)]
    for a,b in edges:
        xA,yA=nodes[a]; xB,yB=nodes[b]
        parts.append(f'<line x1="{xA}" y1="{yA}" x2="{xB}" y2="{yB}" class="link"/>\n')
    positives={1,3,4}
    for i,(cx,cy) in enumerate(nodes):
        cls="dark" if i in positives else "light"
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="12" class="{cls}"/>\n')
    parts.append(f'<text x="{x3+18}" y="395" class="b">Observed positives eliminate</text>\n')
    parts.append(f'<text x="{x3+18}" y="420" class="b">incompatible worlds</text>\n')
    parts.append(f'<text x="{x3+18}" y="455" class="sm">Outcome depends on positive placement</text>\n')

    for start,end in [(x1+w,x2),(x2+w,x3)]:
        parts.append(f'<line x1="{start+10}" y1="285" x2="{end-10}" y2="285" class="axis"/>\n')
        parts.append(f'<polygon points="{end-18},279 {end-8},285 {end-18},291" class="dark"/>\n')

    parts.append('<text x="70" y="550" class="s">Before response: can this world family be tested?</text>\n')
    parts.append('<text x="690" y="550" class="s">After response: which worlds survive?</text>\n')
    parts.append('<text x="70" y="590" class="b">These are different inferential objects.</text>\n')
    parts.append('</svg>\n')
    return "".join(parts)


def load_scored_rows() -> list[dict[str, str]]:
    with DATA.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_figure2(rows: list[dict[str, str]], lock: dict) -> str:
    width, height = 1280, 720
    margin_l, margin_r = 90, 60
    top, bottom = 95, 120
    plot_w = width - margin_l - margin_r
    plot_h = height - top - bottom
    parts=[svg_header(
        width,height,
        "Prospective NEON world-survival validation",
        "Paired predicted and observed surviving-world fractions for nine scored NEON sites."
    )]
    parts.append('<text x="55" y="42" class="h">Prospective NEON validation: survival was systematically underpredicted</text>\n')
    for frac in [0,0.25,0.5,0.75,1.0]:
        y=top + plot_h*(1-frac)
        parts.append(f'<line x1="{margin_l}" y1="{y:.1f}" x2="{width-margin_r}" y2="{y:.1f}" class="grid"/>\n')
        parts.append(f'<text x="48" y="{y+5:.1f}" class="b">{frac:.2f}</text>\n')
    parts.append(f'<line x1="{margin_l}" y1="{top}" x2="{margin_l}" y2="{top+plot_h}" class="axis"/>\n')
    parts.append(f'<line x1="{margin_l}" y1="{top+plot_h}" x2="{width-margin_r}" y2="{top+plot_h}" class="axis"/>\n')

    n=len(rows)
    step=plot_w/n
    for i,row in enumerate(rows):
        x=margin_l + step*(i+0.5)
        pred=float(row["predicted_survival_fraction"])
        obs=float(row["observed_survival_fraction"])
        yp=top + plot_h*(1-pred)
        yo=top + plot_h*(1-obs)
        parts.append(f'<line x1="{x:.1f}" y1="{yp:.1f}" x2="{x:.1f}" y2="{yo:.1f}" stroke="#777" stroke-width="3"/>\n')
        parts.append(f'<circle cx="{x:.1f}" cy="{yp:.1f}" r="7" fill="white" stroke="#222" stroke-width="2"/>\n')
        parts.append(f'<circle cx="{x:.1f}" cy="{yo:.1f}" r="7" class="dark"/>\n')
        parts.append(f'<text x="{x:.1f}" y="{top+plot_h+28}" text-anchor="middle" class="b">{escape(row["site"])}</text>\n')
    parts.append(f'<text x="{margin_l}" y="{height-45}" class="sm">open circle = frozen forecast; filled circle = observed</text>\n')
    parts.append(f'<text x="{width-425}" y="{height-45}" class="sm">exact matches: {lock["primary"]["exact_regime_match_count"]}/{lock["scored_site_count"]}</text>\n')
    parts.append(f'<text x="{width-425}" y="{height-25}" class="sm">MAE = {lock["secondary"]["mean_absolute_survival_fraction_error"]:.3f}</text>\n')
    parts.append('</svg>\n')
    return "".join(parts)


def build_figure3() -> str:
    width,height=1150,520
    parts=[svg_header(
        width,height,
        "Positive-node placement identifiability witness",
        "The same graph and same number of positive nodes can yield world survival or failure depending only on placement."
    )]
    parts.append('<text x="55" y="42" class="h">Same graph, same positive count, different survival outcome</text>\n')
    panels=[(90,"Survives",True),(620,"Fails",False)]
    nodes=[(0,0),(110,-45),(210,5),(85,100),(200,115)]
    edges=[(0,1),(1,2),(0,3),(3,4)]
    for px,title,survive in panels:
        py=220
        parts.append(f'<rect x="{px-35}" y="90" width="430" height="340" rx="12" class="box"/>\n')
        parts.append(f'<text x="{px-15}" y="125" class="s">{title}</text>\n')
        for a,b in edges:
            x1=px+nodes[a][0]; y1=py+nodes[a][1]
            x2=px+nodes[b][0]; y2=py+nodes[b][1]
            parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="link"/>\n')
        positive={0,1} if survive else {2,4}
        for i,(dx,dy) in enumerate(nodes):
            cls="dark" if i in positive else "light"
            parts.append(f'<circle cx="{px+dx}" cy="{py+dy}" r="13" class="{cls}"/>\n')
        outcome="adjacent positive pair" if survive else "non-adjacent positive pair"
        parts.append(f'<text x="{px-15}" y="390" class="b">{outcome}</text>\n')
    parts.append('<text x="365" y="475" text-anchor="middle" class="b">global graph unchanged</text>\n')
    parts.append('<text x="895" y="475" text-anchor="middle" class="b">positive-set size unchanged</text>\n')
    parts.append('</svg>\n')
    return "".join(parts)


def validate_lock(rows: list[dict[str, str]], lock: dict) -> None:
    assert lock["fixed_site_count"] == 16
    assert lock["scored_site_count"] == 9
    assert lock["stopped_site_count"] == 7
    assert lock["primary"]["exact_regime_match_count"] == 2
    assert abs(lock["primary"]["exact_regime_match_fraction"] - 2/9) < 1e-15
    assert lock["observed_regime_counts_scored"] == {
        "contracting": 2,
        "falsified_universe": 0,
        "saturated": 7,
    }
    assert len(rows) == 9
    assert sum(row["exact_match"].lower() == "true" for row in rows) == 2
    assert sum(row["observed_regime"] == "saturated" for row in rows) == 7
    assert sum(row["observed_regime"] == "contracting" for row in rows) == 2


def write_supplement_tables(lock: dict) -> list[Path]:
    scored = OUT / "table_s1_scored_sites.csv"
    with scored.open("w", newline="", encoding="utf-8") as handle:
        writer=csv.DictWriter(handle, fieldnames=[
            "site","positive_nodes","predicted_fraction","observed_fraction",
            "predicted_regime","observed_regime","exact_match"
        ])
        writer.writeheader()
        writer.writerows(lock["scored_sites"])

    stops = OUT / "table_s2_response_consumed_stops.csv"
    with stops.open("w", newline="", encoding="utf-8") as handle:
        fields=["site","status","unknown_positive_nodes","known_positive_nodes","examples"]
        writer=csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in lock["response_consumed_stops"]:
            writer.writerow({
                "site":row["site"],
                "status":row["status"],
                "unknown_positive_nodes":row["unknown_positive_nodes"],
                "known_positive_nodes":row["known_positive_nodes"],
                "examples":";".join(row["examples"]),
            })
    return [scored,stops]


def main() -> None:
    rows=load_scored_rows()
    lock=json.loads(LOCK.read_text(encoding="utf-8"))
    validate_lock(rows,lock)
    OUT.mkdir(parents=True,exist_ok=True)

    assets = {
        OUT/"figure_1_adequacy_vs_survival.svg": build_figure1(),
        OUT/"figure_2_neon_validation.svg": build_figure2(rows,lock),
        OUT/"figure_3_identifiability_witness.svg": build_figure3(),
    }
    for path,text in assets.items():
        write_text(path,text)
    supplement=write_supplement_tables(lock)

    manifest={
        "schema":"eog.world_survival_identifiability.paper_assets.v1",
        "source_data":str(DATA.relative_to(ROOT)),
        "source_lock":str(LOCK.relative_to(ROOT)),
        "frozen_values":{
            "fixed_sites":16,
            "scored_sites":9,
            "stopped_sites":7,
            "exact_matches":2,
            "observed_saturated":7,
            "observed_contracting":2,
            "observed_falsified":0,
            "mean_absolute_survival_fraction_error":lock["secondary"]["mean_absolute_survival_fraction_error"],
        },
        "files":{}
    }
    for path in [*assets.keys(),*supplement]:
        raw=path.read_bytes()
        try:
            manifest_key = str(path.relative_to(ROOT))
        except ValueError:
            manifest_key = f"generated/{path.name}"
        manifest["files"][manifest_key]={
            "bytes":len(raw),
            "sha256":sha256_bytes(raw),
        }
    manifest_path=OUT/"asset_manifest_v1.json"
    write_text(manifest_path,json.dumps(manifest,indent=2,sort_keys=True)+"\n")


if __name__ == "__main__":
    main()
