"""Optional contextual signals for risk rule evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RiskContext:
    """
    Supplemental context for risk scoring.

    Keeps RiskEngine stateless while allowing the pipeline to pass
    batch-level or session-level signals when available.
    """

    failed_login_count: int = 0
    is_root: bool = False
    is_remote: bool = False
    is_privileged_user: bool = False
    extra: dict[str, object] = field(default_factory=dict)
