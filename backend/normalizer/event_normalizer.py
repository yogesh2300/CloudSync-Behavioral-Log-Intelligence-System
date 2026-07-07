"""Convert parsed log dictionaries into standardized security events."""

from __future__ import annotations

import re
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Iterable, Iterator, Protocol, Sequence

from backend.normalizer.event_types import (
    EventType,
    NormalizedSecurityEvent,
    category_for,
)
from backend.normalizer.severity import RiskScoreCalculator, SeverityLevel

ParsedLog = dict[str, Any]

# Placeholders used when score_risk=False; RiskEngine replaces these values.
_UNSCORED_SEVERITY = "info"
_UNSCORED_RISK_SCORE = 0

# --- Secure log (/var/log/secure) patterns ---

_SECURE_FAILED_LOGIN = re.compile(
    r"Failed\s+(?:password|publickey|keyboard-interactive/pam)\s+"
    r"(?:for\s+(?:invalid\s+user\s+)?(?P<user>\S+)\s+)?from\s+(?P<ip>\S+)",
    re.IGNORECASE,
)
_SECURE_SUCCESS_LOGIN = re.compile(
    r"Accepted\s+(?:password|publickey|keyboard-interactive/pam)\s+"
    r"for\s+(?P<user>\S+)\s+from\s+(?P<ip>\S+)",
    re.IGNORECASE,
)
_SECURE_TIMESTAMP = re.compile(
    r"^(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})$"
)

_MONTHS = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}

_ROOT_USERS = frozenset({"root", "0"})


class ClassificationResult:
    """Outcome of classifying a parsed log entry."""

    __slots__ = ("event_type", "username", "source_ip", "is_root", "is_remote", "metadata")

    def __init__(
        self,
        event_type: EventType,
        *,
        username: str | None = None,
        source_ip: str | None = None,
        is_root: bool = False,
        is_remote: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.event_type = event_type
        self.username = username
        self.source_ip = source_ip
        self.is_root = is_root
        self.is_remote = is_remote
        self.metadata = metadata or {}


class LogClassifier(Protocol):
    """Interface for source-specific event classifiers."""

    def supports(self, parsed: ParsedLog) -> bool:
        """Return True when this classifier handles the parsed log source."""

    def classify(self, parsed: ParsedLog) -> ClassificationResult | None:
        """Classify a parsed log entry, or return None if unmatched."""


class SecureLogClassifier:
    """Classify events from parsed /var/log/secure entries."""

    def supports(self, parsed: ParsedLog) -> bool:
        return parsed.get("source") == "secure" and "parse_error" not in parsed

    def classify(self, parsed: ParsedLog) -> ClassificationResult | None:
        message = parsed.get("message")
        if not isinstance(message, str):
            return None

        failed = _SECURE_FAILED_LOGIN.search(message)
        if failed:
            username = failed.group("user")
            return ClassificationResult(
                EventType.FAILED_LOGIN,
                username=username,
                source_ip=failed.group("ip"),
                is_root=_is_root_user(username),
                is_remote=True,
                metadata={"program": parsed.get("program"), "pid": parsed.get("pid")},
            )

        success = _SECURE_SUCCESS_LOGIN.search(message)
        if success:
            username = success.group("user")
            return ClassificationResult(
                EventType.SUCCESSFUL_LOGIN,
                username=username,
                source_ip=success.group("ip"),
                is_root=_is_root_user(username),
                is_remote=True,
                metadata={"program": parsed.get("program"), "pid": parsed.get("pid")},
            )

        return None


class AuditLogClassifier:
    """Classify events from parsed audit.log entries."""

    _WRITE_SYSCALLS = frozenset({"open", "openat", "write", "writev", "pwrite64"})
    _MKDIR_SYSCALLS = frozenset({"mkdir", "mkdirat"})
    _PERM_SYSCALLS = frozenset({"chmod", "fchmod", "fchmodat", "chown", "fchown", "fchownat", "lchown"})

    def supports(self, parsed: ParsedLog) -> bool:
        return parsed.get("source") == "audit" and "parse_error" not in parsed

    def classify(self, parsed: ParsedLog) -> ClassificationResult | None:
        audit_type = parsed.get("type")
        fields = parsed.get("fields")
        if not isinstance(audit_type, str) or not isinstance(fields, dict):
            return None

        username = _extract_audit_username(fields)
        source_ip = fields.get("addr") or None
        is_root = _is_root_user(username) or fields.get("uid") in _ROOT_USERS
        metadata: dict[str, Any] = {
            "audit_type": audit_type,
            "pid": fields.get("pid"),
            "exe": fields.get("exe"),
        }

        if audit_type == "ADD_USER":
            return ClassificationResult(
                EventType.USER_CREATION,
                username=fields.get("acct") or username,
                source_ip=source_ip,
                is_root=is_root,
                is_remote=bool(source_ip),
                metadata={**metadata, "acct": fields.get("acct")},
            )

        if audit_type == "DEL_USER":
            return ClassificationResult(
                EventType.USER_DELETION,
                username=fields.get("acct") or username,
                source_ip=source_ip,
                is_root=is_root,
                is_remote=bool(source_ip),
                metadata={**metadata, "acct": fields.get("acct")},
            )

        if audit_type == "USER_ACCT":
            op = fields.get("op", "").lower()
            if "adding" in op or "add" in op:
                return ClassificationResult(
                    EventType.USER_CREATION,
                    username=fields.get("acct") or username,
                    source_ip=source_ip,
                    is_root=is_root,
                    metadata={**metadata, "op": fields.get("op")},
                )
            if "deleting" in op or "delete" in op:
                return ClassificationResult(
                    EventType.USER_DELETION,
                    username=fields.get("acct") or username,
                    source_ip=source_ip,
                    is_root=is_root,
                    metadata={**metadata, "op": fields.get("op")},
                )

        if self._is_sudo_event(audit_type, fields):
            return ClassificationResult(
                EventType.SUDO_COMMAND,
                username=username,
                source_ip=source_ip,
                is_root=is_root,
                metadata={**metadata, "cmd": fields.get("cmd") or fields.get("proctitle")},
            )

        if audit_type in {"USER_CMD", "EXECVE", "PROCTITLE"}:
            if self._is_sudo_event(audit_type, fields):
                return ClassificationResult(
                    EventType.SUDO_COMMAND,
                    username=username,
                    source_ip=source_ip,
                    is_root=is_root,
                    metadata={**metadata, "cmd": fields.get("cmd") or fields.get("proctitle")},
                )
            return ClassificationResult(
                EventType.COMMAND_EXECUTION,
                username=username,
                source_ip=source_ip,
                is_root=is_root,
                metadata={**metadata, "cmd": fields.get("cmd") or fields.get("proctitle")},
            )

        if audit_type == "PATH":
            nametype = fields.get("nametype", "").upper()
            if nametype == "CREATE":
                return ClassificationResult(
                    EventType.DIRECTORY_CREATION,
                    username=username,
                    source_ip=source_ip,
                    is_root=is_root,
                    metadata={**metadata, "name": fields.get("name"), "nametype": nametype},
                )
            if nametype in {"NORMAL", "DELETE"}:
                return ClassificationResult(
                    EventType.FILE_MODIFICATION,
                    username=username,
                    source_ip=source_ip,
                    is_root=is_root,
                    metadata={**metadata, "name": fields.get("name"), "nametype": nametype},
                )

        if audit_type == "SYSCALL":
            syscall = (fields.get("syscall") or fields.get("comm") or "").lower()
            nametype = fields.get("nametype", "").upper()

            if syscall in self._MKDIR_SYSCALLS or nametype == "CREATE":
                return ClassificationResult(
                    EventType.DIRECTORY_CREATION,
                    username=username,
                    source_ip=source_ip,
                    is_root=is_root,
                    metadata={**metadata, "syscall": syscall, "nametype": nametype},
                )

            if syscall in self._PERM_SYSCALLS:
                return ClassificationResult(
                    EventType.PERMISSION_CHANGE,
                    username=username,
                    source_ip=source_ip,
                    is_root=is_root,
                    metadata={**metadata, "syscall": syscall},
                )

            if syscall in self._WRITE_SYSCALLS or nametype == "NORMAL":
                return ClassificationResult(
                    EventType.FILE_MODIFICATION,
                    username=username,
                    source_ip=source_ip,
                    is_root=is_root,
                    metadata={**metadata, "syscall": syscall, "nametype": nametype},
                )

        return None

    @staticmethod
    def _is_sudo_event(audit_type: str, fields: dict[str, str]) -> bool:
        exe = (fields.get("exe") or "").lower()
        cmd = (fields.get("cmd") or fields.get("proctitle") or "").lower()
        comm = (fields.get("comm") or "").lower()
        return "sudo" in exe or "sudo" in cmd or comm == "sudo" or audit_type == "CRED_REFR"


class TimestampNormalizer(ABC):
    """Normalize timestamps from parsed logs to ISO-8601 UTC strings."""

    @abstractmethod
    def normalize(self, parsed: ParsedLog) -> str:
        """Return an ISO-8601 timestamp string."""


class DefaultTimestampNormalizer(TimestampNormalizer):
    """Normalize secure syslog and audit epoch timestamps."""

    def normalize(self, parsed: ParsedLog) -> str:
        timestamp = parsed.get("timestamp")
        if timestamp is None:
            return datetime.now(timezone.utc).isoformat()

        if parsed.get("source") == "audit":
            return self._normalize_audit_timestamp(str(timestamp))

        if parsed.get("source") == "secure":
            return self._normalize_secure_timestamp(str(timestamp))

        return str(timestamp)

    @staticmethod
    def _normalize_audit_timestamp(raw: str) -> str:
        try:
            epoch = float(raw.split(".", maxsplit=1)[0])
            return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
        except (ValueError, OSError):
            return raw

    @staticmethod
    def _normalize_secure_timestamp(raw: str) -> str:
        match = _SECURE_TIMESTAMP.match(raw.strip())
        if not match:
            return raw

        month = _MONTHS.get(match.group("month"))
        if month is None:
            return raw

        day = int(match.group("day"))
        hour, minute, second = (int(part) for part in match.group("time").split(":"))
        year = datetime.now(timezone.utc).year

        try:
            dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            return raw


class EventNormalizer:
    """
    Convert parsed log dictionaries into NormalizedSecurityEvent instances.

    Classification and field normalization always run. Risk scoring is optional:
    set score_risk=False when a downstream RiskEngine owns scoring (pipeline path).

    Unrecognized or malformed entries are skipped (returns None per entry).
    """

    def __init__(
        self,
        classifiers: Sequence[LogClassifier] | None = None,
        risk_calculator: RiskScoreCalculator | None = None,
        timestamp_normalizer: TimestampNormalizer | None = None,
        default_hostname: str = "unknown",
        score_risk: bool = True,
    ) -> None:
        self._classifiers: tuple[LogClassifier, ...] = tuple(
            classifiers or (SecureLogClassifier(), AuditLogClassifier())
        )
        self._risk_calculator = risk_calculator or RiskScoreCalculator()
        self._timestamp_normalizer = timestamp_normalizer or DefaultTimestampNormalizer()
        self._default_hostname = default_hostname
        self._score_risk = score_risk

    def normalize(self, parsed: ParsedLog) -> NormalizedSecurityEvent | None:
        """Normalize a single parsed log dictionary."""
        if parsed.get("parse_error"):
            return None

        classification = self._classify(parsed)
        if classification is None:
            return None

        event_type = classification.event_type
        if self._score_risk:
            severity = self._risk_calculator.severity_for(event_type).value
            risk_score = self._risk_calculator.calculate(
                event_type,
                is_root=classification.is_root,
                is_remote=classification.is_remote,
            )
        else:
            severity = _UNSCORED_SEVERITY
            risk_score = _UNSCORED_RISK_SCORE

        hostname = str(parsed.get("hostname") or self._default_hostname)
        raw_log = str(parsed.get("raw", ""))

        return NormalizedSecurityEvent(
            event_id=str(uuid.uuid4()),
            timestamp=self._timestamp_normalizer.normalize(parsed),
            hostname=hostname,
            username=classification.username,
            source_ip=classification.source_ip,
            event_type=event_type,
            category=category_for(event_type),
            severity=severity,
            risk_score=risk_score,
            raw_log=raw_log,
            metadata={
                "source": parsed.get("source"),
                "path": parsed.get("path"),
                "line_number": parsed.get("line_number"),
                "is_root": classification.is_root,
                "is_remote": classification.is_remote,
                **classification.metadata,
            },
        )

    def normalize_many(self, parsed_logs: Iterable[ParsedLog]) -> list[NormalizedSecurityEvent]:
        """Normalize a batch of parsed log dictionaries."""
        return [event for parsed in parsed_logs if (event := self.normalize(parsed)) is not None]

    def iter_normalize(self, parsed_logs: Iterable[ParsedLog]) -> Iterator[NormalizedSecurityEvent]:
        """Lazily normalize parsed logs, yielding only recognized events."""
        for parsed in parsed_logs:
            event = self.normalize(parsed)
            if event is not None:
                yield event

    def _classify(self, parsed: ParsedLog) -> ClassificationResult | None:
        for classifier in self._classifiers:
            if classifier.supports(parsed):
                return classifier.classify(parsed)
        return None


def _extract_audit_username(fields: dict[str, str]) -> str | None:
    for key in ("acct", "auid", "uid", "suser", "user"):
        value = fields.get(key)
        if value and value not in {"unset", "4294967295", "-1"}:
            if key in {"auid", "uid"} and value == "0":
                return "root"
            if key in {"auid", "uid"} and value.isdigit():
                continue
            return value
    return None


def _is_root_user(username: str | None) -> bool:
    return username is not None and username.lower() in _ROOT_USERS
