"""Finite-n adequacy-complete structural ladder planning for EOG-WF v2.

A response-blind world ladder should contain at least one structural scale capable of
testing its own frozen adequacy declaration. This module derives finite-n LCC targets
from adequacy criteria before any biological response is opened.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json, math
from typing import Sequence
from eog.v2.world_adequacy import StructuralAdequacyDeclaration

def _sha256(value: object) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()

@dataclass(frozen=True)
class AdequacyCompleteLadderPlan:
    node_count:int
    declared_targets:tuple[float,...]
    required_lcc_targets:tuple[float,...]
    completed_targets:tuple[float,...]
    max_isolated_nodes:int|None
    horizon_reachability_requires_independent_design:bool
    fingerprint:str

def plan_adequacy_complete_lcc_targets(node_count:int, declared_targets:Sequence[float], adequacy:StructuralAdequacyDeclaration)->AdequacyCompleteLadderPlan:
    if isinstance(node_count,bool) or not isinstance(node_count,int) or node_count<2:
        raise ValueError("node_count must be an integer >= 2")
    values=tuple(float(v) for v in declared_targets)
    if not values: raise ValueError("declared_targets must be non-empty")
    if any(not 0.0<v<=1.0 for v in values): raise ValueError("declared_targets must lie in (0, 1]")
    if any(b<a for a,b in zip(values,values[1:])): raise ValueError("declared_targets must be non-decreasing")
    required=[]; max_iso=None
    if adequacy.min_largest_weak_component_fraction is not None:
        required.append(math.ceil(adequacy.min_largest_weak_component_fraction*node_count-1e-12)/node_count)
    if adequacy.max_isolated_node_fraction is not None:
        max_iso=math.floor(adequacy.max_isolated_node_fraction*node_count+1e-12)
        required.append((node_count-max_iso)/node_count)
    req=tuple(sorted(set(required))); completed=tuple(sorted(set(values)|set(req)))
    horizon=adequacy.min_median_horizon_reachable_fraction is not None
    payload={"node_count":node_count,"declared_targets":list(values),"required_lcc_targets":list(req),"completed_targets":list(completed),"max_isolated_nodes":max_iso,"horizon_reachability_requires_independent_design":horizon}
    return AdequacyCompleteLadderPlan(node_count,values,req,completed,max_iso,horizon,_sha256(payload))
