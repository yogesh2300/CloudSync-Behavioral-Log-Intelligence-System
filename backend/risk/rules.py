"""Extensible detection rules for the DefenSync RiskEngine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from backend.normalizer.event_types import EventType, NormalizedSecurityEvent
from backend.risk.context import RiskContext
from backend.risk.scoring import SeverityLevel


@dataclass(frozen=True, slots=True)
class RuleOutcome:
    """Result produced by a single risk rule evaluation."""

    score_delta: int = 0
    severity: SeverityLevel | None = None
    risk_factor: str = ""
    recommendation: str = ""


class RiskRule(ABC):
    """Base class for pluggable risk detection rules."""

    name: str = "base_rule"

    @abstractmethod
    def evaluate(
        self,
        event: NormalizedSecurityEvent,
        context: RiskContext,
    ) -> RuleOutcome | None:
        """Return a rule outcome when the rule matches, otherwise None."""


class FailedLoginRule(RiskRule):
    name = "failed_login"

    def evaluate(
        self,
        event: NormalizedSecurityEvent,
        context: RiskContext,
    ) -> RuleOutcome | None:
        if event.event_type != EventType.FAILED_LOGIN:
            return None
        return RuleOutcome(
            risk_factor="failed_login",
            recommendation="Review authentication logs and consider blocking the source IP after repeated failures.",
        )


class MultipleFailedLoginRule(RiskRule):
    name = "multiple_failed_login"

    def __init__(self, threshold: int = 3) -> None:
        self._threshold = threshold

    def evaluate(
        self,
        event: NormalizedSecurityEvent,
        context: RiskContext,
    ) -> RuleOutcome | None:
        if event.event_type != EventType.FAILED_LOGIN:
            return None
        if context.failed_login_count < self._threshold:
            return None
        return RuleOutcome(
            score_delta=15,
            severity=SeverityLevel.HIGH,
            risk_factor="multiple_failed_login",
            recommendation=(
                f"Detected {context.failed_login_count} failed login attempts. "
                "Investigate potential brute-force activity and enforce account lockout or IP blocking."
            ),
        )


class RootLoginRule(RiskRule):
    name = "root_login"

    def evaluate(
        self,
        event: NormalizedSecurityEvent,
        context: RiskContext,
    ) -> RuleOutcome | None:
        if event.event_type != EventType.SUCCESSFUL_LOGIN:
            return None
        username = (event.username or "").lower()
        if username not in {"root", "0"} and not context.is_root:
            return None
        return RuleOutcome(
            score_delta=20,
            severity=SeverityLevel.HIGH,
            risk_factor="root_login",
            recommendation="Direct root login detected. Prefer sudo-based privilege escalation and disable direct root SSH access.",
        )


class SshSuccessRule(RiskRule):
    name = "ssh_success"

    def evaluate(
        self,
        event: NormalizedSecurityEvent,
        context: RiskContext,
    ) -> RuleOutcome | None:
        if event.event_type != EventType.SUCCESSFUL_LOGIN:
            return None
        if not event.source_ip and not context.is_remote:
            return None
        return RuleOutcome(
            risk_factor="ssh_success",
            recommendation="Verify that the successful SSH login originated from an authorized source and expected user account.",
        )


class SuspiciousSudoRule(RiskRule):
    name = "suspicious_sudo"

    _SENSITIVE_COMMANDS = frozenset(
        {
            "chmod",
            "chown",
            "useradd",
            "userdel",
            "passwd",
            "visudo",
            "iptables",
            "firewall-cmd",
            "rm",
            "mkfs",
            "dd",
            "curl",
            "wget",
        }
    )

    def evaluate(
        self,
        event: NormalizedSecurityEvent,
        context: RiskContext,
    ) -> RuleOutcome | None:
        if event.event_type != EventType.SUDO_COMMAND:
            return None

        cmd = str(event.metadata.get("cmd") or event.metadata.get("proctitle") or "").lower()
        username = (event.username or "").lower()
        is_root_user = username in {"root", "0"} or context.is_root

        sensitive = any(token in cmd for token in self._SENSITIVE_COMMANDS)
        if not sensitive and not is_root_user:
            return None

        delta = 10 if sensitive else 5
        severity = SeverityLevel.HIGH if sensitive else SeverityLevel.MEDIUM
        return RuleOutcome(
            score_delta=delta,
            severity=severity,
            risk_factor="suspicious_sudo",
            recommendation="Review sudo command execution for unauthorized privilege escalation or destructive operations.",
        )


class NewUserCreationRule(RiskRule):
    name = "new_user_creation"

    def evaluate(
        self,
        event: NormalizedSecurityEvent,
        context: RiskContext,
    ) -> RuleOutcome | None:
        if event.event_type != EventType.USER_CREATION:
            return None
        acct = event.metadata.get("acct") or event.username or "unknown"
        return RuleOutcome(
            score_delta=5,
            severity=SeverityLevel.HIGH,
            risk_factor="new_user_creation",
            recommendation=f"Validate that user account '{acct}' was created by an authorized administrator.",
        )


DEFAULT_RULES: tuple[RiskRule, ...] = (
    FailedLoginRule(),
    MultipleFailedLoginRule(),
    RootLoginRule(),
    SshSuccessRule(),
    SuspiciousSudoRule(),
    NewUserCreationRule(),
)
