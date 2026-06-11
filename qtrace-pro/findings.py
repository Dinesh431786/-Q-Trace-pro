"""
findings.py — Q-Trace Pro Threat Catalog & Severity Model
=========================================================

Centralizes the industry-standard metadata for every threat Q-Trace can
report, so the rest of the codebase never hard-codes severities or CWE IDs.

Two independent axes (per Bandit / OWASP guidance) are modeled separately:

  * **severity**   — potential impact *if* the finding is real
                     (Critical / High / Medium / Low), with a CVSS-style score.
  * **confidence** — probability the finding is a true positive
                     (High / Medium / Low), driven by how the detector fired.

Each pattern is mapped to the most appropriate **CWE** so output integrates
with GitHub code scanning, DefectDojo, SonarQube, etc.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# Severity -> (SARIF level, representative CVSS 3.1 base score)
SEVERITY_TO_SARIF = {
    "Critical": "error",
    "High": "error",
    "Medium": "warning",
    "Low": "note",
    "Info": "none",
}
SEVERITY_TO_CVSS = {
    "Critical": 9.3,
    "High": 7.8,
    "Medium": 5.4,
    "Low": 3.1,
    "Info": 0.0,
}
CONFIDENCE_RANK = {"High": 0.9, "Medium": 0.6, "Low": 0.3}


@dataclass(frozen=True)
class ThreatMeta:
    rule_id: str
    title: str
    cwe: str            # e.g. "CWE-511"
    cwe_name: str
    severity: str       # Critical | High | Medium | Low | Info
    base_confidence: str  # High | Medium | Low
    description: str
    remediation: str
    help_uri: str = ""

    def cwe_number(self) -> str:
        return self.cwe.replace("CWE-", "")

    def cwe_uri(self) -> str:
        return f"https://cwe.mitre.org/data/definitions/{self.cwe_number()}.html"


# --------------------------------------------------------------------------- #
# Threat catalog. CWE choices:
#   CWE-511 Logic/Time Bomb           — probabilistic/chained/entangled triggers
#   CWE-506 Embedded Malicious Code   — distributed / cross-function payloads
#   CWE-515 Covert Storage Channel    — steganographic data hiding
#   CWE-489 Active Debug Code / anti-analysis behaviour (closest fit)
#   CWE-78  OS Command Injection      — os.system / subprocess sinks
#   CWE-95  Eval Injection            — exec / eval
#   CWE-502 Untrusted Deserialization — pickle / marshal / yaml.load
# --------------------------------------------------------------------------- #
CATALOG: Dict[str, ThreatMeta] = {
    "PROBABILISTIC_BOMB": ThreatMeta(
        rule_id="QT.PROBABILISTIC_BOMB",
        title="Probabilistic Logic Bomb",
        cwe="CWE-511", cwe_name="Logic/Time Bomb",
        severity="High", base_confidence="Medium",
        description=(
            "A dangerous action is gated behind a low-probability random check, "
            "so the payload only fires occasionally — a classic evasion tactic "
            "to survive sandbox/CI analysis."),
        remediation=(
            "Remove randomness from security-relevant control flow. If sampling "
            "is legitimate, isolate it from privileged side effects (no os/exec)."),
    ),
    "ENTANGLED_BOMB": ThreatMeta(
        rule_id="QT.ENTANGLED_BOMB",
        title="Entangled (Multi-Condition) Logic Bomb",
        cwe="CWE-511", cwe_name="Logic/Time Bomb",
        severity="High", base_confidence="Medium",
        description=(
            "The trigger depends on several correlated/coupled conditions, hiding "
            "the true activation criteria across multiple random or stateful checks."),
        remediation=(
            "Audit every condition feeding the privileged action; collapse the "
            "coupled checks and verify none combine to form a hidden trigger."),
    ),
    "CHAINED_QUANTUM_BOMB": ThreatMeta(
        rule_id="QT.CHAINED_BOMB",
        title="Chained / Stateful Logic Bomb",
        cwe="CWE-511", cwe_name="Logic/Time Bomb",
        severity="High", base_confidence="Medium",
        description=(
            "A counter or accumulated state must reach a threshold across multiple "
            "iterations before the payload detonates (staged trigger)."),
        remediation=(
            "Trace the state variable's lifecycle; ensure no accumulated counter "
            "unlocks privileged operations after N events."),
    ),
    "CROSS_FUNCTION_QUANTUM_BOMB": ThreatMeta(
        rule_id="QT.CROSS_FUNCTION_BOMB",
        title="Cross-Function Embedded Malicious Code",
        cwe="CWE-506", cwe_name="Embedded Malicious Code",
        severity="Critical", base_confidence="Medium",
        description=(
            "Malicious logic is distributed across multiple functions so no single "
            "function looks suspicious — an interprocedural backdoor."),
        remediation=(
            "Perform interprocedural review; follow the data/control flow between "
            "the cooperating functions to expose the assembled payload."),
    ),
    "QUANTUM_STEGANOGRAPHY": ThreatMeta(
        rule_id="QT.STEGANOGRAPHY",
        title="Steganographic / Covert Data Channel",
        cwe="CWE-515", cwe_name="Covert Storage Channel",
        severity="Critical", base_confidence="Medium",
        description=(
            "Bit-level manipulation (chr/ord/xor/encode-decode) is used to hide a "
            "payload or exfiltrate data through an unobvious channel."),
        remediation=(
            "Inspect the encode/decode routine and the data it transforms; confirm "
            "it is not concealing commands, keys, or exfiltrated data."),
    ),
    "QUANTUM_ANTIDEBUG": ThreatMeta(
        rule_id="QT.ANTIDEBUG",
        title="Anti-Analysis / Anti-Debug Behaviour",
        cwe="CWE-489", cwe_name="Active Debug Code / Anti-Analysis",
        severity="Medium", base_confidence="Medium",
        description=(
            "The code attempts to detect or evade analysis (long sleeps, timing "
            "checks, debugger detection) to hide behaviour during inspection."),
        remediation=(
            "Treat anti-analysis logic as a strong indicator of malice; analyze "
            "what behaviour the code is trying to hide when observed."),
    ),
    "DANGEROUS_SINK": ThreatMeta(
        rule_id="QT.DANGEROUS_SINK",
        title="Dangerous Execution Sink",
        cwe="CWE-78", cwe_name="OS Command Injection",
        severity="High", base_confidence="High",
        description=(
            "A direct call to an OS command / code-execution sink "
            "(os.system, subprocess, exec, eval) was found."),
        remediation=(
            "Avoid shelling out; use safe APIs with argument lists and never pass "
            "untrusted input to exec/eval/os.system."),
    ),
}

# Fallback for any unknown rule so reporting never KeyErrors.
_UNKNOWN = ThreatMeta(
    rule_id="QT.UNKNOWN",
    title="Unknown / Generic Finding",
    cwe="CWE-693", cwe_name="Protection Mechanism Failure",
    severity="Low", base_confidence="Low",
    description="An unclassified pattern was reported by a detector.",
    remediation="Review manually.",
)


def get_meta(pattern: str) -> ThreatMeta:
    return CATALOG.get(pattern, _UNKNOWN)


@dataclass
class Finding:
    """A single, deduplicatable audit finding."""
    pattern: str
    meta: ThreatMeta
    confidence: str                  # may be elevated/lowered from base
    risk_score: float = 0.0          # 0-1 quantum risk
    line: int = 1
    column: int = 1
    snippet: str = ""
    evidence: List[str] = field(default_factory=list)

    @property
    def severity(self) -> str:
        return self.meta.severity

    @property
    def cvss(self) -> float:
        return SEVERITY_TO_CVSS.get(self.meta.severity, 0.0)

    def fingerprint(self) -> str:
        """Stable hash for cross-run deduplication (rule + location + snippet)."""
        import hashlib
        basis = f"{self.meta.rule_id}|{self.line}|{self.snippet.strip()[:120]}"
        return hashlib.sha256(basis.encode("utf-8", "replace")).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {
            "rule_id": self.meta.rule_id,
            "title": self.meta.title,
            "pattern": self.pattern,
            "cwe": self.meta.cwe,
            "cwe_name": self.meta.cwe_name,
            "severity": self.severity,
            "cvss": self.cvss,
            "confidence": self.confidence,
            "risk_score": round(float(self.risk_score), 4),
            "line": self.line,
            "column": self.column,
            "description": self.meta.description,
            "remediation": self.meta.remediation,
            "evidence": self.evidence,
            "fingerprint": self.fingerprint(),
        }


def dedupe(findings: List[Finding]) -> List[Finding]:
    """Remove duplicate findings by fingerprint, keeping the highest risk."""
    best: Dict[str, Finding] = {}
    for f in findings:
        fp = f.fingerprint()
        if fp not in best or f.risk_score > best[fp].risk_score:
            best[fp] = f
    # Sort by severity then risk (most important first).
    order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4}
    return sorted(best.values(), key=lambda x: (order.get(x.severity, 9), -x.risk_score))
