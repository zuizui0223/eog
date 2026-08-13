import json

import pytest

from eog.reachability_html import render_dynamic_reachability_html


def payload():
    return {
        "schema": "eog_dynamic_reachability_graph_v1",
        "interpretation": "relative reachability support",
        "operator_fingerprint": "a" * 64,
        "source_ids": ["source"],
        "source_weights": [1.0],
        "nodes": [
            {
                "id": "source",
                "position": [0.0, 0.0],
                "viability": 0.8,
                "persistence": 0.7,
                "first_arrival_step": 0,
                "integrated_reachability_support": 1.0,
                "source_attribution": {"source": 1.0},
                "is_declared_source": True,
            },
            {
                "id": "target",
                "position": [1.0, 0.0],
                "viability": 0.9,
                "persistence": 0.5,
                "first_arrival_step": 1,
                "integrated_reachability_support": 0.4,
                "source_attribution": {"source": 1.0},
                "is_declared_source": False,
            },
        ],
        "edges": [
            {
                "source": "source",
                "target": "target",
                "raw_support": 0.8,
                "transition_support": 0.6,
                "integrated_flux": 0.6,
            }
        ],
        "frames": [
            {
                "step": 0,
                "total_mass": 1.0,
                "lost_mass_after_step": 0.4,
                "nodes": [
                    {"id": "source", "reachability_mass": 1.0},
                    {"id": "target", "reachability_mass": 0.0},
                ],
                "edges": [{"source": "source", "target": "target", "flux": 0.6}],
            },
            {
                "step": 1,
                "total_mass": 0.6,
                "lost_mass_after_step": None,
                "nodes": [
                    {"id": "source", "reachability_mass": 0.0},
                    {"id": "target", "reachability_mass": 0.6},
                ],
                "edges": [],
            },
        ],
        "fingerprint": "b" * 64,
    }


def test_renderer_is_standalone_deterministic_and_has_controls():
    first = render_dynamic_reachability_html(payload(), title="Island flow")
    second = render_dynamic_reachability_html(payload(), title="Island flow")
    assert first == second
    assert "<!doctype html>" in first.lower()
    assert "Propagation step" in first
    assert 'id="play"' in first
    assert 'id="step"' in first
    assert "node radius = reachability mass" in first
    assert "edge width = directed flux" in first
    assert "https://" not in first
    assert "src=\"http" not in first


def test_renderer_embeds_payload_without_relabelling_step_as_time():
    rendered = render_dynamic_reachability_html(payload())
    assert "Propagation step is not calendar time" in rendered
    start = rendered.index('<script id="eog-data" type="application/json">')
    start = rendered.index(">", start) + 1
    end = rendered.index("</script>", start)
    embedded = json.loads(rendered[start:end])
    assert embedded["schema"] == "eog_dynamic_reachability_graph_v1"
    assert embedded["frames"][0]["edges"][0]["flux"] == pytest.approx(0.6)


def test_renderer_escapes_script_closing_sequence_in_node_id():
    value = payload()
    value["nodes"][1]["id"] = "</script><script>alert(1)</script>"
    value["edges"][0]["target"] = value["nodes"][1]["id"]
    value["frames"][0]["nodes"][1]["id"] = value["nodes"][1]["id"]
    value["frames"][0]["edges"][0]["target"] = value["nodes"][1]["id"]
    value["frames"][1]["nodes"][1]["id"] = value["nodes"][1]["id"]
    rendered = render_dynamic_reachability_html(value)
    data_block = rendered.split('<script id="eog-data" type="application/json">', 1)[1].split("</script>", 1)[0]
    assert "</script>" not in data_block.lower()
    assert "<\\/script>" in data_block.lower()


def test_renderer_rejects_invalid_schema_and_geometry_parameters():
    value = payload()
    value["schema"] = "wrong"
    with pytest.raises(ValueError, match="schema"):
        render_dynamic_reachability_html(value)
    with pytest.raises(ValueError, match="width"):
        render_dynamic_reachability_html(payload(), width=100)
    with pytest.raises(ValueError, match="frame_interval"):
        render_dynamic_reachability_html(payload(), frame_interval_ms=20)


def test_renderer_rejects_unknown_edge_endpoint():
    value = payload()
    value["edges"][0]["target"] = "missing"
    with pytest.raises(ValueError, match="edge endpoints"):
        render_dynamic_reachability_html(value)
