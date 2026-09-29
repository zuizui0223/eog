"""Independent multi-landscape stochastic BAM generator for v4.

This module intentionally imports no EOG package. It generates eight preregistered
landscapes, independently simulated partner/antagonist distributions, and stochastic
focal occurrence histories under a shared finite BAM parameter grammar.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math

import numpy as np


@dataclass(frozen=True)
class LandscapeSpec:
    landscape_id: str
    family: str
    env_seed: int
    bottleneck_amplitude: float
    environmental_noise_sd: float
    barrier_col: int | None
    barrier_gap_row: int | None


@dataclass(frozen=True)
class Landscape:
    spec: LandscapeSpec
    width: int
    height: int
    node_ids: tuple[str, ...]
    coordinates: np.ndarray
    environment: np.ndarray


@dataclass(frozen=True)
class SpeciesSpec:
    source_id: str
    niche_center: tuple[float, float]
    niche_radius: tuple[float, float]
    step_radius: float
    barrier_permeable: bool
    colonization_beta: float
    persistence_probability: float


@dataclass(frozen=True)
class FocalSpec:
    scenario_id: str
    source_id: str
    abiotic_label: str
    niche_center: tuple[float, float]
    niche_radius: tuple[float, float]
    biotic_mode: str
    movement_label: str
    step_radius: float
    barrier_permeable: bool
    colonization_beta: float
    persistence_probability: float


@dataclass(frozen=True)
class Associates:
    partner_mask: np.ndarray
    antagonist_mask: np.ndarray


@dataclass(frozen=True)
class FocalRealization:
    occupancy_history: np.ndarray
    structural_reachable_ids: tuple[str, ...]


LANDSCAPE_PANEL = (
    LandscapeSpec("open_smooth_s0","open_smooth",0,0.0,0.03,None,None),
    LandscapeSpec("open_smooth_s1","open_smooth",1,0.0,0.03,None,None),
    LandscapeSpec("barrier_gap_s0","barrier_gap",2,0.20,0.04,7,2),
    LandscapeSpec("barrier_gap_s1","barrier_gap",3,0.20,0.04,7,5),
    LandscapeSpec("bottleneck_s0","bottleneck",4,0.50,0.05,None,None),
    LandscapeSpec("bottleneck_s1","bottleneck",5,0.50,0.05,None,None),
    LandscapeSpec("joint_fragmented_s0","joint_fragmented",6,0.50,0.06,7,3),
    LandscapeSpec("joint_fragmented_s1","joint_fragmented",7,0.50,0.06,7,4),
)


def seed_from(*parts: object) -> int:
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def make_landscape(spec: LandscapeSpec) -> Landscape:
    width, height = 12, 8
    rng = np.random.default_rng(spec.env_seed)
    node_ids, coords, env = [], [], []
    for row in range(height):
        for col in range(width):
            node_ids.append(f"r{row}c{col}")
            coords.append((float(col), float(row)))
            temp = col / (width - 1)
            moisture = row / (height - 1)
            if col == 5:
                temp += spec.bottleneck_amplitude
            temp += float(rng.normal(0.0, spec.environmental_noise_sd))
            moisture += float(rng.normal(0.0, spec.environmental_noise_sd))
            env.append((float(np.clip(temp, -0.25, 1.5)), float(np.clip(moisture, -0.25, 1.25))))
    return Landscape(
        spec=spec,
        width=width,
        height=height,
        node_ids=tuple(node_ids),
        coordinates=np.asarray(coords, dtype=float),
        environment=np.asarray(env, dtype=float),
    )


def abiotic_mask(landscape: Landscape, center, radius) -> np.ndarray:
    c=np.asarray(center,float); r=np.asarray(radius,float)
    scaled=(landscape.environment-c)/r
    return np.sum(scaled*scaled,axis=1)<=1.0+1e-12


def _crosses_barrier(landscape: Landscape, i:int, j:int)->bool:
    col=landscape.spec.barrier_col
    if col is None:
        return False
    x1,y1=landscape.coordinates[i]; x2,y2=landscape.coordinates[j]
    if not (min(x1,x2)<col<=max(x1,x2)):
        return False
    gap=landscape.spec.barrier_gap_row
    if gap is not None and int(round(y1))==int(round(y2))==gap:
        return False
    return True


def movement_adjacency(landscape: Landscape, step_radius:float, barrier_permeable:bool):
    n=len(landscape.node_ids); rows=[[] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i==j: continue
            if float(np.linalg.norm(landscape.coordinates[i]-landscape.coordinates[j]))>step_radius+1e-12:
                continue
            if not barrier_permeable and _crosses_barrier(landscape,i,j):
                continue
            rows[i].append(j)
    return tuple(tuple(x) for x in rows)


def structural_reachable_mask(landscape: Landscape, source_id:str, eligible_mask:np.ndarray, step_radius:float, barrier_permeable:bool):
    idx={x:i for i,x in enumerate(landscape.node_ids)}; source=idx[source_id]
    if not bool(eligible_mask[source]):
        raise ValueError("source_outside_structural_eligibility")
    adj=movement_adjacency(landscape,step_radius,barrier_permeable)
    reached=np.zeros(len(landscape.node_ids),bool); reached[source]=True
    q=[source]; k=0
    while k<len(q):
        i=q[k]; k+=1
        for j in adj[i]:
            if reached[j] or not bool(eligible_mask[j]): continue
            reached[j]=True; q.append(j)
    return reached


def simulate_species(landscape:Landscape,spec:SpeciesSpec,steps:int,seed:int,extra_eligible_mask:np.ndarray|None=None):
    rng=np.random.default_rng(seed)
    A=abiotic_mask(landscape,spec.niche_center,spec.niche_radius)
    eligible=A if extra_eligible_mask is None else A & extra_eligible_mask
    idx={x:i for i,x in enumerate(landscape.node_ids)}; source=idx[spec.source_id]
    if not bool(eligible[source]):
        raise ValueError("species_source_not_eligible")
    adj=movement_adjacency(landscape,spec.step_radius,spec.barrier_permeable)
    hist=np.zeros((steps+1,len(landscape.node_ids)),bool); hist[0,source]=True
    for t in range(1,steps+1):
        prev=hist[t-1]; cur=np.zeros(len(landscape.node_ids),bool); cur[source]=True
        for node in range(len(landscape.node_ids)):
            if node==source or not bool(eligible[node]): continue
            if prev[node]:
                cur[node]=rng.random()<spec.persistence_probability
            else:
                k=sum(1 for nb in adj[node] if prev[nb])
                if k:
                    cur[node]=rng.random() < 1.0-(1.0-spec.colonization_beta)**k
        hist[t]=cur
    return hist


def simulate_associates(landscape:Landscape)->Associates:
    partner=SpeciesSpec("r4c0",(0.42,0.52),(0.48,0.72),1.01,True,0.58,0.94)
    antagonist=SpeciesSpec("r4c11",(0.78,0.50),(0.34,0.72),1.01,True,0.55,0.94)
    ph=simulate_species(landscape,partner,30,seed_from("v4",landscape.spec.landscape_id,"partner"))
    ah=simulate_species(landscape,antagonist,30,seed_from("v4",landscape.spec.landscape_id,"antagonist"))
    return Associates(ph[-1].copy(),ah[-1].copy())


def biotic_mask(mode:str,associates:Associates):
    if mode=="none": return np.ones(associates.partner_mask.shape[0],bool)
    if mode=="obligate_partner": return associates.partner_mask.copy()
    if mode=="antagonist_exclusion": return ~associates.antagonist_mask
    if mode=="partner_and_antagonist": return associates.partner_mask & ~associates.antagonist_mask
    raise ValueError(mode)


def candidate_parameter_grid():
    a_specs=(("A_narrow",(0.42,0.52),(0.44,0.74)),("A_broad",(0.50,0.52),(0.82,0.90)))
    b_modes=("none","obligate_partner","antagonist_exclusion","partner_and_antagonist")
    m_specs=(("short_closed",1.01,False),("short_open",1.01,True),("long_closed",2.01,False),("long_open",2.01,True))
    rows=[]
    for al,c,r in a_specs:
        for b in b_modes:
            for ml,d,p in m_specs:
                rows.append(FocalSpec(f"{al}|B_{b}|M_{ml}","r4c0",al,c,r,b,ml,d,p,0.48,0.86))
    return tuple(rows)


def truth_scenarios():
    return {
        "A_limited":"A_narrow|B_none|M_long_open",
        "partner_limited":"A_broad|B_obligate_partner|M_long_open",
        "antagonist_limited":"A_broad|B_antagonist_exclusion|M_long_open",
        "distance_limited":"A_broad|B_none|M_short_open",
        "barrier_limited":"A_broad|B_none|M_long_closed",
        "joint_ABM":"A_narrow|B_partner_and_antagonist|M_short_closed",
    }


def simulate_focal(landscape:Landscape,associates:Associates,spec:FocalSpec,replicate:int,steps:int=40)->FocalRealization:
    A=abiotic_mask(landscape,spec.niche_center,spec.niche_radius)
    B=biotic_mask(spec.biotic_mode,associates)
    eligible=A&B
    ss=SpeciesSpec(spec.source_id,spec.niche_center,spec.niche_radius,spec.step_radius,spec.barrier_permeable,spec.colonization_beta,spec.persistence_probability)
    hist=simulate_species(landscape,ss,steps,seed_from("v4",landscape.spec.landscape_id,spec.scenario_id,replicate),B)
    reach=structural_reachable_mask(landscape,spec.source_id,eligible,spec.step_radius,spec.barrier_permeable)
    ids=tuple(x for x,v in zip(landscape.node_ids,reach,strict=True) if bool(v))
    return FocalRealization(hist,ids)
