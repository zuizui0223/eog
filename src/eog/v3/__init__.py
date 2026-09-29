"""Public EOG v3 exact finite joint-world and evidence-design interfaces.

EOG v3 is a post-closure API consolidation. It does not alter the frozen EOG-WF
empirical programme or manuscript result.
"""

from .adaptive import (
    ActionSupports,
    adaptive_forced_first_depth,
    plan_robust_evidence_set,
    solve_adaptive_evidence_policy,
)
from .joint_world_engine import (
    ActionRanking,
    EcologicalWorld,
    EvidenceEvent,
    JointEvidencePlan,
    JointMember,
    JointWorldEvaluation,
    ObservationSupport,
    ObservationWorld,
    evaluate_joint_worlds,
    evaluation_is_contraction,
    plan_next_evidence_action,
)

__all__ = [
    "ActionRanking",
    "ActionSupports",
    "EcologicalWorld",
    "EvidenceEvent",
    "JointEvidencePlan",
    "JointMember",
    "JointWorldEvaluation",
    "ObservationSupport",
    "ObservationWorld",
    "adaptive_forced_first_depth",
    "evaluate_joint_worlds",
    "evaluation_is_contraction",
    "plan_next_evidence_action",
    "plan_robust_evidence_set",
    "solve_adaptive_evidence_policy",
]
