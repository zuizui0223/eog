"""Standalone HTML renderer for graph-native EOG-R dynamics.

The renderer consumes the deterministic payload from
:func:`eog.reachability_visualization.build_dynamic_reachability_visualization_payload`
and returns a self-contained HTML document with an SVG graph, step slider and play/pause
control. It has no external JavaScript or CSS dependencies.

The visualisation remains a view of model support. It must not relabel propagation depth
as time or reachability mass as colonisation probability unless an external calibration
has been supplied outside this renderer.
"""
from __future__ import annotations

import html
import json
from typing import Mapping

import numpy as np


EXPECTED_SCHEMA = "eog_dynamic_reachability_graph_v1"


def _safe_json(value: object) -> str:
    text = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    # Keep embedded data inside the script element even when a node ID contains markup.
    return text.replace("</", "<\\/")


def _validate_payload(payload: Mapping[str, object]) -> None:
    if payload.get("schema") != EXPECTED_SCHEMA:
        raise ValueError(f"payload schema must be {EXPECTED_SCHEMA!r}")
    nodes = payload.get("nodes")
    frames = payload.get("frames")
    edges = payload.get("edges")
    if not isinstance(nodes, list) or not nodes:
        raise ValueError("payload must contain a non-empty nodes list")
    if not isinstance(frames, list) or not frames:
        raise ValueError("payload must contain a non-empty frames list")
    if not isinstance(edges, list):
        raise ValueError("payload edges must be a list")
    node_ids: list[str] = []
    for node in nodes:
        if not isinstance(node, dict) or not str(node.get("id", "")).strip():
            raise ValueError("every payload node must contain a non-empty id")
        node_ids.append(str(node["id"]))
    if len(set(node_ids)) != len(node_ids):
        raise ValueError("payload node IDs must be unique")
    known = set(node_ids)
    for edge in edges:
        if not isinstance(edge, dict):
            raise ValueError("payload edge entries must be objects")
        if edge.get("source") not in known or edge.get("target") not in known:
            raise ValueError("payload edge endpoints must refer to known nodes")
    expected_steps = list(range(len(frames)))
    observed_steps = [frame.get("step") if isinstance(frame, dict) else None for frame in frames]
    if observed_steps != expected_steps:
        raise ValueError("payload frame steps must be contiguous and zero-based")


def render_dynamic_reachability_html(
    payload: Mapping[str, object],
    *,
    title: str = "EOG-R dynamic reachability",
    width: int = 960,
    height: int = 640,
    frame_interval_ms: int = 800,
) -> str:
    """Render a deterministic self-contained HTML animation from an EOG-R payload.

    The SVG uses supplied node positions when present. Missing positions are placed on a
    deterministic circle, so schematic graph visualisation remains available without a
    map or raster. Node radius encodes current reachability mass, edge width encodes
    current directed flux, node outline opacity reflects viability when supplied, and a
    secondary ring reflects persistence when supplied.
    """

    _validate_payload(payload)
    if not isinstance(width, int) or width < 320:
        raise ValueError("width must be an integer >= 320")
    if not isinstance(height, int) or height < 240:
        raise ValueError("height must be an integer >= 240")
    if not isinstance(frame_interval_ms, int) or frame_interval_ms < 100:
        raise ValueError("frame_interval_ms must be an integer >= 100")
    if not str(title).strip():
        raise ValueError("title must be non-empty")

    data = _safe_json(dict(payload))
    safe_title = html.escape(str(title), quote=True)
    interpretation = html.escape(
        str(
            payload.get(
                "interpretation",
                "graph-native relative reachability support by propagation depth",
            )
        )
    )
    max_step = len(payload["frames"]) - 1

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_title}</title>
<style>
:root {{ color-scheme: light dark; font-family: system-ui, -apple-system, sans-serif; }}
body {{ margin: 0; padding: 1rem; background: Canvas; color: CanvasText; }}
main {{ max-width: {width}px; margin: 0 auto; }}
h1 {{ font-size: 1.25rem; margin: 0 0 .35rem; }}
.note {{ opacity: .76; margin: 0 0 .8rem; font-size: .9rem; }}
.controls {{ display:flex; gap:.65rem; align-items:center; flex-wrap:wrap; margin:.5rem 0; }}
button, input {{ font: inherit; }}
#step {{ width:min(34rem,65vw); }}
.readout {{ font-variant-numeric: tabular-nums; min-width:12rem; }}
svg {{ width:100%; height:auto; border:1px solid color-mix(in srgb, CanvasText 18%, transparent); border-radius:.6rem; background:Canvas; }}
.edge {{ stroke-linecap:round; fill:none; }}
.node-label {{ font-size:12px; text-anchor:middle; dominant-baseline:hanging; pointer-events:none; }}
.legend {{ display:flex; gap:1rem; flex-wrap:wrap; font-size:.82rem; opacity:.82; margin:.55rem 0 0; }}
.swatch {{ display:inline-block; width:.9rem; height:.9rem; border-radius:50%; vertical-align:-.12rem; border:2px solid currentColor; margin-right:.25rem; }}
</style>
</head>
<body>
<main>
<h1>{safe_title}</h1>
<p class="note">{interpretation}. Propagation step is not calendar time unless externally calibrated.</p>
<div class="controls">
  <button id="play" type="button" aria-label="Play reachability animation">Play</button>
  <label>Propagation step <input id="step" type="range" min="0" max="{max_step}" value="0" step="1"></label>
  <span class="readout" id="readout"></span>
</div>
<svg id="graph" viewBox="0 0 {width} {height}" role="img" aria-label="Dynamic EOG-R island graph">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor"></path>
    </marker>
  </defs>
  <g id="edge-layer"></g>
  <g id="node-layer"></g>
</svg>
<div class="legend">
  <span><i class="swatch"></i>node radius = reachability mass</span>
  <span>edge width = directed flux</span>
  <span>outer ring = persistence when supplied</span>
</div>
</main>
<script id="eog-data" type="application/json">{data}</script>
<script>
(() => {{
  const payload = JSON.parse(document.getElementById('eog-data').textContent);
  const svg = document.getElementById('graph');
  const edgeLayer = document.getElementById('edge-layer');
  const nodeLayer = document.getElementById('node-layer');
  const slider = document.getElementById('step');
  const play = document.getElementById('play');
  const readout = document.getElementById('readout');
  const W = {width}, H = {height}, margin = 70;
  const ids = payload.nodes.map(n => n.id);
  const nodeById = new Map(payload.nodes.map(n => [n.id, n]));
  const supplied = payload.nodes.filter(n => Array.isArray(n.position));
  const pos = new Map();

  if (supplied.length >= 2) {{
    const xs = supplied.map(n => Number(n.position[0]));
    const ys = supplied.map(n => Number(n.position[1]));
    const xmin = Math.min(...xs), xmax = Math.max(...xs);
    const ymin = Math.min(...ys), ymax = Math.max(...ys);
    const xspan = Math.max(xmax - xmin, 1e-12);
    const yspan = Math.max(ymax - ymin, 1e-12);
    payload.nodes.forEach((node, i) => {{
      if (Array.isArray(node.position)) {{
        pos.set(node.id, [margin + (Number(node.position[0])-xmin)/xspan*(W-2*margin), H-margin-(Number(node.position[1])-ymin)/yspan*(H-2*margin)]);
      }} else {{
        const a = 2*Math.PI*i/payload.nodes.length - Math.PI/2;
        pos.set(node.id, [W/2 + Math.cos(a)*(W/2-margin), H/2 + Math.sin(a)*(H/2-margin)]);
      }}
    }});
  }} else {{
    payload.nodes.forEach((node, i) => {{
      const a = 2*Math.PI*i/payload.nodes.length - Math.PI/2;
      pos.set(node.id, [W/2 + Math.cos(a)*(W/2-margin), H/2 + Math.sin(a)*(H/2-margin)]);
    }});
  }}

  function el(name, attrs={{}}) {{
    const node = document.createElementNS('http://www.w3.org/2000/svg', name);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
    return node;
  }}

  const baseEdges = new Map(payload.edges.map(e => [`${{e.source}}\u0000${{e.target}}`, e]));
  function render(step) {{
    const frame = payload.frames[step];
    const masses = new Map(frame.nodes.map(n => [n.id, Number(n.reachability_mass)]));
    const fluxes = new Map(frame.edges.map(e => [`${{e.source}}\u0000${{e.target}}`, Number(e.flux)]));
    const maxMass = Math.max(1e-12, ...masses.values());
    const maxFlux = Math.max(1e-12, ...fluxes.values(), 0);
    edgeLayer.replaceChildren();
    nodeLayer.replaceChildren();

    for (const [key, base] of baseEdges) {{
      const value = fluxes.get(key) || 0;
      if (value <= 0) continue;
      const [x1,y1] = pos.get(base.source), [x2,y2] = pos.get(base.target);
      const line = el('line', {{x1,y1,x2,y2,class:'edge','stroke-width':1.2+7*Math.sqrt(value/maxFlux),'stroke-opacity':0.18+0.72*Math.sqrt(value/maxFlux),'marker-end':'url(#arrow)'}});
      const tip = el('title'); tip.textContent = `${{base.source}} → ${{base.target}}; flux=${{value.toPrecision(4)}}`;
      line.appendChild(tip); edgeLayer.appendChild(line);
    }}

    for (const id of ids) {{
      const node = nodeById.get(id), [x,y] = pos.get(id);
      const mass = masses.get(id) || 0;
      const radius = 6 + 22*Math.sqrt(mass/maxMass);
      const group = el('g', {{transform:`translate(${{x}},${{y}})`}});
      if (node.persistence !== null && node.persistence !== undefined) {{
        group.appendChild(el('circle', {{r:radius+5, fill:'none', stroke:'currentColor', 'stroke-opacity':0.15+0.7*Math.max(0,Math.min(1,Number(node.persistence))), 'stroke-width':3}}));
      }}
      const circle = el('circle', {{r:radius, fill:'currentColor', 'fill-opacity':0.12+0.75*Math.sqrt(mass/maxMass), stroke:'currentColor', 'stroke-width':node.is_declared_source?3:1.5, 'stroke-opacity':node.viability===null||node.viability===undefined?0.65:0.2+0.8*Math.max(0,Math.min(1,Number(node.viability)))}});
      const tip = el('title');
      tip.textContent = `${{id}}; step mass=${{mass.toPrecision(4)}}; integrated=${{Number(node.integrated_reachability_support).toPrecision(4)}}`;
      circle.appendChild(tip); group.appendChild(circle);
      const label = el('text', {{y:radius+6,class:'node-label'}}); label.textContent=id; group.appendChild(label);
      nodeLayer.appendChild(group);
    }}
    readout.textContent = `step ${{step}} / ${{payload.frames.length-1}} · total mass ${{Number(frame.total_mass).toPrecision(4)}}`;
  }}

  let timer = null;
  function stop() {{ if (timer !== null) clearInterval(timer); timer=null; play.textContent='Play'; }}
  function start() {{
    if (timer !== null) return;
    play.textContent='Pause';
    timer=setInterval(() => {{
      let next=Number(slider.value)+1;
      if (next > Number(slider.max)) next=0;
      slider.value=String(next); render(next);
    }}, {frame_interval_ms});
  }}
  slider.addEventListener('input', () => {{ render(Number(slider.value)); }});
  play.addEventListener('click', () => timer===null ? start() : stop());
  document.addEventListener('visibilitychange', () => {{ if (document.hidden) stop(); }});
  render(0);
}})();
</script>
</body>
</html>
"""
