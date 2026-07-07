"""Risk level helpers for DefenSync behavioral scoring."""

from __future__ import annotations


def risk_level_from_score(score: int) -> str:
    """Map numeric risk score to enterprise risk level."""
    if score >= 85:
        return "critical"
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"
