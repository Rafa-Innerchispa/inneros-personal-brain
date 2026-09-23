from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CuratedMemory:
    text: str
    policy: dict = field(default_factory=dict)


SECRET_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"(?i)(api[_ -]?key|token|secret|password|passwd|pwd|authorization|bearer)\s*[:=]\s*['\"]?[^'\"\s,;]+", r"\1=[REDACTED]"),
    (r"(?i)Bearer\s+[A-Za-z0-9._~+/=-]{16,}", "Bearer [REDACTED]"),
    (r"\bsk-[A-Za-z0-9_-]{16,}\b", "[REDACTED_OPENAI_KEY]"),
    (r"\b[A-Fa-f0-9]{32,}\b", "[REDACTED_HEX_SECRET]"),
)

PRIVATE_INFRA_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\b(?:10|127)\.(?:\d{1,3}\.){2}\d{1,3}\b", "[LOCAL_IP]"),
    (r"\b192\.168\.(?:\d{1,3}\.)\d{1,3}\b", "[LOCAL_IP]"),
    (r"\b172\.(?:1[6-9]|2\d|3[0-1])\.(?:\d{1,3}\.)\d{1,3}\b", "[LOCAL_IP]"),
    (r"/home/[A-Za-z0-9_.-]+/[^\s,;]+", "[LOCAL_PATH]"),
    (r"[A-Za-z]:\\Users\\[^ \n\r\t,;]+", "[LOCAL_PATH]"),
)


def _redact(text: str, patterns: tuple[tuple[str, str], ...]) -> tuple[str, int]:
    count = 0
    cleaned = text
    for pattern, replacement in patterns:
        cleaned, replaced = re.subn(pattern, replacement, cleaned)
        count += replaced
    return cleaned, count


def curate_for_cognee(text: str, *, max_chars: int = 1400) -> CuratedMemory:
    """Prepare a safe, portable memory note for shared Cognee agent memory."""
    original_len = len(text)
    curated, secret_redactions = _redact(text, SECRET_PATTERNS)
    curated, infra_redactions = _redact(curated, PRIVATE_INFRA_PATTERNS)
    curated = re.sub(r"\n{3,}", "\n\n", curated).strip()
    truncated = len(curated) > max_chars
    if truncated:
        curated = curated[: max_chars - 32].rstrip() + "\n[TRUNCATED_FOR_SHARED_MEMORY]"

    return CuratedMemory(
        text=curated,
        policy={
            "curated": True,
            "shared_memory_scope": "safe_facts_outcomes_provenance",
            "secret_redactions": secret_redactions,
            "private_infra_redactions": infra_redactions,
            "truncated": truncated,
            "original_chars": original_len,
            "stored_chars": len(curated),
        },
    )
