"""Backward-compatible re-exports for the DefenSync log parser."""

from backend.parser.engine import parse_audit_line, parse_logs, parse_secure_line, summarize_events

__all__ = ["parse_audit_line", "parse_logs", "parse_secure_line", "summarize_events"]
