from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = [
    p for p in (ROOT / "services").rglob("*")
    if p.is_file() and p.suffix in {".py", ".js"}
]
PRODUCTION += [
    p for p in (ROOT / "setup").rglob("*")
    if p.is_file() and p.suffix in {".py", ".js"}
]
PRODUCTION += [
    p for p in (ROOT / "api").rglob("*")
    if p.is_file() and p.suffix in {".py", ".js"}
]
PRODUCTION += [
    p for p in (ROOT / "murasalat_office/doctype").rglob("*")
    if p.is_file() and p.suffix in {".py", ".js"}
]

FIXED_STATE_COMPARISON = re.compile(
    r"workflow_state\s*(?:==|!=|in|not\s+in)\s*(?:[\"'](?:Draft|Sent|Received|Completed|Cancelled|Closed|Sealed|Registered)[\"']|\([^\n)]*[\"'](?:Draft|Sent|Received|Completed|Cancelled|Closed|Sealed|Registered)[\"'])"
)


def test_production_code_does_not_bind_business_logic_to_named_workflow_states():
    offenders = []
    for path in PRODUCTION:
        source = path.read_text(encoding="utf-8", errors="ignore")
        if FIXED_STATE_COMPARISON.search(source):
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == [], offenders


def test_provision_never_creates_or_updates_a_workflow():
    source = (ROOT / "setup/provision.py").read_text(encoding="utf-8")
    assert "_ensure_workflow" not in source
    assert '"doctype": "Workflow"' not in source
    assert ".insert(ignore_permissions=True)" in source  # master/governance provisioning still exists
