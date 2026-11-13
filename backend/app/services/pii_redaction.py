"""Minimal deterministic PII/secret redaction helper for logging.

This is NOT a comprehensive PII detector. Add policy-based entity detection,
field-level controls, and integrate at logging/telemetry/output boundaries before
claiming end-to-end PII protection. Does not mutate application behavior alone.
"""
from __future__ import annotations

import re

_PATTERN_REPLACEMENTS = [
    (re.compile(r'(?<![\w.-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w.-])'), '[REDACTED_EMAIL]'),
    (re.compile(r'(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)'), '[REDACTED_SSN]'),
    (re.compile(r'(?<!\w)(?:\+1[ .-]?)?(?:\(\d{3}\)|\d{3})[ .-]?\d{3}[ .-]?\d{4}(?!\w)'), '[REDACTED_PHONE]'),
    (re.compile(r'(?<!\w)gsk_[A-Za-z0-9_-]{8,}'), '[REDACTED_GROQ_KEY]'),
    (re.compile(r'(?<!\w)sk-[A-Za-z0-9_-]{10,}'), '[REDACTED_API_KEY]'),
]


def redact_log_text(value: str) -> str:
    redacted = str(value)
    for pattern, replacement in _PATTERN_REPLACEMENTS:
        redacted = pattern.sub(replacement, redacted)
    return redacted
