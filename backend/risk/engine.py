"""Central risk assessment engine for DefenSync security events."""

from __future__ import annotations

from dataclasses import replace

from backend.core.logging import get_logger
from backend.normalizer.event_types import NormalizedSecurityEvent
from backend.risk.context import RiskContext
from backend.risk.rules import DEFAULT_RULES, RiskRule
from backend.risk.scoring import RiskScoreCalculator, SeverityLevel
from backend.risk.levels import risk_level_from_score

logger = get_logger(__name__)

_SEVERITY_ORDER = {
    SeverityLevel.LOW: 1,
    SeverityLevel.MEDIUM: 2,
    SeverityLevel.HIGH: 3,
    SeverityLevel.CRITICAL: 4,
}


class RiskEngine:
    """
    Stateless risk evaluator.

    Accepts a normalized event and caller-supplied context, then returns
    an updated NormalizedSecurityEvent with final severity, score, and
    recommendation metadata.
    """

    def __init__(
        self,
        *,
        calculator: RiskScoreCalculator | None = None,
        rules: tuple[RiskRule, ...] | None = None,
    ) -> None:
        self._calculator = calculator or RiskScoreCalculator()
        self._rules = rules or DEFAULT_RULES

    def enrich(
        self,
        event: NormalizedSecurityEvent,
        context: RiskContext,
    ) -> NormalizedSecurityEvent:
        """Apply centralized scoring rules and return an enriched normalized event."""
        base_score = self._calculator.calculate(
            event.event_type,
            is_root=context.is_root,
            is_privileged_user=context.is_privileged_user,
            is_remote=context.is_remote,
        )
        base_severity = self._calculator.severity_for(event.event_type)

        score = base_score
        severity = base_severity
        risk_factors: list[str] = []
        recommendations: list[str] = []

        for rule in self._rules:
            outcome = rule.evaluate(event, context)
            if outcome is None:
                continue
            score = self._clamp_score(score + outcome.score_delta)
            if outcome.severity and _SEVERITY_ORDER[outcome.severity] > _SEVERITY_ORDER[severity]:
                severity = outcome.severity
            if outcome.risk_factor:
                risk_factors.append(outcome.risk_factor)
            if outcome.recommendation:
                recommendations.append(outcome.recommendation)
            logger.debug("Rule '%s' matched event %s", rule.name, event.event_id)

        metadata = dict(event.metadata)
        metadata["message"] = self._build_message(event)
        metadata["recommendation"] = " ".join(recommendations)
        metadata["risk_factors"] = risk_factors
        metadata["risk_level"] = risk_level_from_score(score)

        process = event.metadata.get("process") or event.metadata.get("exe") or event.metadata.get("comm")
        if process:
            metadata["process"] = str(process)

        return replace(
            event,
            severity=severity.value,
            risk_score=score,
            metadata=metadata,
        )

    @staticmethod
    def build_context(
        event: NormalizedSecurityEvent,
        *,
        failed_login_count: int = 0,
    ) -> RiskContext:
        """Derive per-event risk context supplied by the orchestrating caller."""
        metadata = event.metadata
        username = (event.username or "").lower()

        if "is_root" in metadata:
            is_root = bool(metadata["is_root"])
        else:
            is_root = username in {"root", "0"}

        if "is_remote" in metadata:
            is_remote = bool(metadata["is_remote"])
        else:
            is_remote = bool(event.source_ip)

        return RiskContext(
            failed_login_count=failed_login_count,
            is_root=is_root,
            is_remote=is_remote,
            is_privileged_user=is_root,
        )

    @staticmethod
    def _build_message(event: NormalizedSecurityEvent) -> str:
        cmd = event.metadata.get("cmd") or event.metadata.get("proctitle")
        if cmd:
            return f"{event.event_type.value}: {cmd}"
        if event.username and event.source_ip:
            return f"{event.event_type.value} for {event.username} from {event.source_ip}"
        if event.username:
            return f"{event.event_type.value} for {event.username}"
        return event.raw_log or event.event_type.value

    @staticmethod
    def _clamp_score(score: int) -> int:
        return max(RiskScoreCalculator.MIN_SCORE, min(RiskScoreCalculator.MAX_SCORE, score))
