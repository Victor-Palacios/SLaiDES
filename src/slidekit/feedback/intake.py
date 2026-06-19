"""Parse a GitHub **issue-form** body into a feedback comment dict.

The `.github/ISSUE_TEMPLATE/layout-feedback.yml` form renders its submitted body as
markdown: each field becomes a `### <label>` heading followed by the value (an empty
optional field renders the literal `_No response_`). This parser is the deterministic,
unit-tested bridge from that body to a `{component, comment, severity}` dict the store
can merge. It validates nothing about authorisation — that gate lives in the workflow.
"""
from __future__ import annotations

import re

from slidekit.feedback.store import known_components

# Form field label -> our key. Keep in lockstep with build_feedback_form.py labels.
_LABELS = {
    "Layout": "component",
    "Your comment": "comment",
    "Severity": "severity",
}
_NO_RESPONSE = "_No response_"


def _split_sections(body: str) -> dict[str, str]:
    """Map each `### <heading>` to the text beneath it (trimmed)."""
    out: dict[str, str] = {}
    heading = None
    buf: list[str] = []
    for line in body.replace("\r\n", "\n").split("\n"):
        m = re.match(r"^#{1,6}\s+(.*\S)\s*$", line)
        if m:
            if heading is not None:
                out[heading] = "\n".join(buf).strip()
            heading = m.group(1).strip()
            buf = []
        elif heading is not None:
            buf.append(line)
    if heading is not None:
        out[heading] = "\n".join(buf).strip()
    return out


class FeedbackParseError(ValueError):
    """Raised when an issue body is not a valid layout-feedback submission."""


def parse_issue_form(body: str) -> dict:
    """Return `{component, comment, severity}` from an issue-form body.

    Raises FeedbackParseError with an operator-facing message when the required Layout or
    comment fields are missing/blank, or the layout name is not a known component.
    """
    sections = _split_sections(body or "")
    values: dict[str, str] = {}
    for label, key in _LABELS.items():
        raw = sections.get(label, "").strip()
        values[key] = "" if raw == _NO_RESPONSE else raw

    component = values.get("component", "").strip()
    comment = values.get("comment", "").strip()
    severity = (values.get("severity", "").strip() or "med")

    if not component:
        raise FeedbackParseError(
            "missing the **Layout** field — submit via the *Layout feedback* issue form."
        )
    if component not in known_components():
        raise FeedbackParseError(
            f"'{component}' is not a known layout component; pick one from the form dropdown."
        )
    if not comment:
        raise FeedbackParseError("the **Your comment** field is empty.")
    if severity not in ("low", "med", "high"):
        severity = "med"

    return {"component": component, "comment": comment, "severity": severity}
