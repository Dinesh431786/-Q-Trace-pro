"""
SAST (Static Application Security Testing) analyzer
Integrates Semgrep, Bandit, and custom security rules
"""

import asyncio
import json
import subprocess
import tempfile
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
import yaml
import hashlib
from dataclasses import dataclass
import re

@dataclass
class SastFinding:
    """Represents a SAST finding"""
    tool: str
    rule_id: str
    severity: str
    confidence: str
    message: str
    file_path: str
    line_start: int
    line_end: int
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    cwe: Optional[str] = None
    owasp: Optional[str] = None
    fix_guidance: Optional[str] = None
    code_snippet: Optional[str] = None

class SastAnalyzer:
    """Multi-engine SAST analyzer"""
    
    # Custom Semgrep rules for advanced detection
    CUSTOM_SEMGREP_RULES = """
rules:
  - id: quantum-probabilistic-logic
    pattern-either:
      - pattern: |
          if random.random() < $PROB:
            $DANGEROUS_CALL
      - pattern: |
          if random.uniform(...) < $PROB:
            $DANGEROUS_CALL
    message: Detected probabilistic logic that could be quantum-vulnerable
    severity: WARNING
    languages: [python]
    
  - id: hardcoded-credentials
    pattern-either:
      - pattern: $VAR = "sk_live_..."
      - pattern: $VAR = "pk_live_..."
      - pattern: password = "..."
      - pattern: api_key = "..."
    message: Hardcoded credentials detected
    severity: ERROR
    languages: [python]
    
  - id: unsafe-deserialization
    pattern-either:
      - pattern: pickle.loads(...)
      - pattern: pickle.load(...)
      - pattern: yaml.load(..., Loader=yaml.Loader)
      - pattern: eval(...)
      - pattern: exec(...)
    message: Unsafe deserialization detected
    severity: ERROR
    languages: [python]
    
  - id: sql-injection
    patterns:
      - pattern-either:
          - pattern: |
              $CURSOR.execute(... % ...)
          - pattern: |
              $CURSOR.execute(... + ...)
          - pattern: |
              $CURSOR.execute(f"...")
          - pattern: |
              $CURSOR.execute("..." .format(...))
    message: Potential SQL injection vulnerability
    severity: ERROR
    languages: [python]
    
  - id: command-injection
    pattern-either:
      - pattern: os.system($INPUT)
      - pattern: subprocess.call($INPUT, shell=True)
      - pattern: subprocess.Popen($INPUT, shell=True)
    message: Command injection vulnerability
    severity: CRITICAL
    languages: [python]
    
  - id: path-traversal
    pattern-either:
      - pattern: open(os.path.join(..., $USER_INPUT), ...)
      - pattern: open(f"...{$USER_INPUT}...", ...)
    message: Path traversal vulnerability
    severity: ERROR
    languages: [python]
    
  - id: xxe-vulnerability
    pattern-either:
      - pattern: |
          etree.parse(..., parser=etree.XMLParser(resolve_entities=True))
      - pattern: |
          etree.fromstring(..., parser=etree.XMLParser(resolve_entities=True))
    message: XXE vulnerability - XML external entity injection
    severity: ERROR
    languages: [python]
    
  - id: timing-attack
    patterns:
      - pattern-either:
          - pattern: if $SECRET == $INPUT
          - pattern: if $INPUT == $SECRET
      - metavariable-regex:
          metavariable: $SECRET
          regex: (password|token|secret|key)
    message: Potential timing attack vulnerability in string comparison
    severity: WARNING
    languages: [python]
"""
    
    def __init__(self):
        self.semgrep_available = self._check_tool_availability("semgrep")
        self.bandit_available = self._check_tool_availability("bandit")
        self.custom_rules = self._load_custom_rules()
        
    def _check_tool_availability(self, tool: str) -> bool:
        """Check if a tool is available in PATH"""
        try:
            result = subprocess.run(
                [tool, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
            
    def _load_custom_rules(self) -> Dict[str, Any]:
        """Load custom detection rules"""
        return {
            "backdoor_patterns": [
                r"if\s+.*==.*magic.*:",
                r"exec\(base64\.b64decode",
                r"eval\(.*request\.",
                r"__import__\(['\"]os['\"]\)",
                r"globals\(\)\[.*\]\(",
            ],
            "crypto_weaknesses": [
                r"Random\(\)",  # Weak random
                r"md5\(",       # Weak hash
                r"sha1\(",      # Weak hash
                r"DES\.",       # Weak cipher
                r"RC4\.",       # Weak cipher
            ],
            "timing_channels": [
                r"time\.sleep\(.*random",
                r"if.*time\.time\(\)",
            ]
        }
        
    async def analyze(self, code: str, filename: str = "code.py") -> Dict[str, Any]:
        """Run all SAST analyzers"""
        tasks = []
        
        # Run each analyzer concurrently
        if self.semgrep_available:
            tasks.append(self._run_semgrep(code, filename))
        if self.bandit_available:
            tasks.append(self._run_bandit(code, filename))
            
        # Always run custom pattern matching
        tasks.append(self._run_custom_patterns(code, filename))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine and deduplicate findings
        all_findings = []
        seen_hashes = set()
        
        for result in results:
            if isinstance(result, Exception):
                continue
            if isinstance(result, list):
                for finding in result:
                    # Create hash for deduplication
                    finding_hash = self._hash_finding(finding)
                    if finding_hash not in seen_hashes:
                        seen_hashes.add(finding_hash)
                        all_findings.append(finding)
                        
        # Sort by severity
        severity_order = {"CRITICAL": 0, "ERROR": 1, "HIGH": 1, "WARNING": 2, "MEDIUM": 2, "INFO": 3, "LOW": 3}
        all_findings.sort(key=lambda x: (severity_order.get(x.severity, 4), x.line_start))
        
        # Generate summary statistics
        stats = self._generate_statistics(all_findings)
        
        return {
            "findings": [self._serialize_finding(f) for f in all_findings],
            "statistics": stats,
            "tools_used": self._get_tools_used(results)
        }
        
    async def _run_semgrep(self, code: str, filename: str) -> List[SastFinding]:
        """Run Semgrep analysis"""
        findings = []
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write code to temp file
            code_path = Path(tmpdir) / filename
            code_path.write_text(code)
            
            # Write custom rules
            rules_path = Path(tmpdir) / "rules.yaml"
            rules_path.write_text(self.CUSTOM_SEMGREP_RULES)
            
            try:
                # Run Semgrep with custom rules
                result = await asyncio.create_subprocess_exec(
                    "semgrep",
                    "--config", str(rules_path),
                    "--json",
                    "--no-git-ignore",
                    str(code_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await result.communicate()
                
                if result.returncode == 0:
                    data = json.loads(stdout.decode())
                    
                    for finding in data.get("results", []):
                        findings.append(SastFinding(
                            tool="semgrep",
                            rule_id=finding.get("check_id", "unknown"),
                            severity=self._map_semgrep_severity(finding.get("extra", {}).get("severity", "INFO")),
                            confidence="HIGH",
                            message=finding.get("extra", {}).get("message", ""),
                            file_path=filename,
                            line_start=finding.get("start", {}).get("line", 0),
                            line_end=finding.get("end", {}).get("line", 0),
                            column_start=finding.get("start", {}).get("col"),
                            column_end=finding.get("end", {}).get("col"),
                            code_snippet=finding.get("extra", {}).get("lines")
                        ))
                        
            except Exception as e:
                # Log error but don't fail the entire analysis
                print(f"Semgrep error: {e}")
                
        return findings
        
    async def _run_bandit(self, code: str, filename: str) -> List[SastFinding]:
        """Run Bandit analysis"""
        findings = []
        
        with tempfile.TemporaryDirectory() as tmpdir:
            code_path = Path(tmpdir) / filename
            code_path.write_text(code)
            
            try:
                result = await asyncio.create_subprocess_exec(
                    "bandit",
                    "-f", "json",
                    "-ll",  # Low severity and above
                    str(code_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await result.communicate()
                
                # Bandit returns non-zero if issues found, which is expected
                if stdout:
                    data = json.loads(stdout.decode())
                    
                    for finding in data.get("results", []):
                        findings.append(SastFinding(
                            tool="bandit",
                            rule_id=finding.get("test_id", "unknown"),
                            severity=finding.get("issue_severity", "LOW"),
                            confidence=finding.get("issue_confidence", "LOW"),
                            message=finding.get("issue_text", ""),
                            file_path=filename,
                            line_start=finding.get("line_number", 0),
                            line_end=finding.get("line_number", 0),
                            cwe=finding.get("issue_cwe", {}).get("id"),
                            code_snippet=finding.get("code")
                        ))
                        
            except Exception as e:
                print(f"Bandit error: {e}")
                
        return findings
        
    async def _run_custom_patterns(self, code: str, filename: str) -> List[SastFinding]:
        """Run custom pattern matching"""
        findings = []
        lines = code.split('\n')
        
        # Check for backdoor patterns
        for pattern_name, patterns in self.custom_rules.items():
            for pattern in patterns:
                regex = re.compile(pattern, re.IGNORECASE)
                
                for line_num, line in enumerate(lines, 1):
                    if regex.search(line):
                        severity = "CRITICAL" if "backdoor" in pattern_name else "HIGH"
                        findings.append(SastFinding(
                            tool="custom",
                            rule_id=f"custom_{pattern_name}",
                            severity=severity,
                            confidence="MEDIUM",
                            message=f"Suspicious pattern detected: {pattern_name}",
                            file_path=filename,
                            line_start=line_num,
                            line_end=line_num,
                            code_snippet=line.strip()
                        ))
                        
        # Advanced heuristics
        findings.extend(await self._run_heuristic_analysis(code, filename))
        
        return findings
        
    async def _run_heuristic_analysis(self, code: str, filename: str) -> List[SastFinding]:
        """Run advanced heuristic analysis"""
        findings = []
        
        # Entropy analysis for obfuscation detection
        entropy = self._calculate_entropy(code)
        if entropy > 4.5:  # High entropy threshold
            findings.append(SastFinding(
                tool="heuristic",
                rule_id="high_entropy",
                severity="WARNING",
                confidence="LOW",
                message=f"High entropy detected ({entropy:.2f}), possible obfuscation",
                file_path=filename,
                line_start=1,
                line_end=1
            ))
            
        # Check for long base64 strings (potential payloads)
        base64_pattern = re.compile(r'[A-Za-z0-9+/]{100,}={0,2}')
        for line_num, line in enumerate(code.split('\n'), 1):
            if base64_pattern.search(line):
                findings.append(SastFinding(
                    tool="heuristic",
                    rule_id="long_base64",
                    severity="WARNING",
                    confidence="MEDIUM",
                    message="Long base64 string detected, potential encoded payload",
                    file_path=filename,
                    line_start=line_num,
                    line_end=line_num
                ))
                
        return findings
        
    def _calculate_entropy(self, data: str) -> float:
        """Calculate Shannon entropy"""
        if not data:
            return 0
            
        entropy = 0
        for x in range(256):
            p_x = float(data.count(chr(x))) / len(data)
            if p_x > 0:
                import math
                entropy += - p_x * math.log(p_x, 2)
                
        return entropy
        
    def _hash_finding(self, finding: SastFinding) -> str:
        """Create hash for finding deduplication"""
        key = f"{finding.tool}:{finding.rule_id}:{finding.file_path}:{finding.line_start}:{finding.message[:50]}"
        return hashlib.md5(key.encode()).hexdigest()
        
    def _serialize_finding(self, finding: SastFinding) -> Dict[str, Any]:
        """Serialize finding to dict"""
        return {
            "tool": finding.tool,
            "rule_id": finding.rule_id,
            "severity": finding.severity,
            "confidence": finding.confidence,
            "message": finding.message,
            "location": {
                "file": finding.file_path,
                "line_start": finding.line_start,
                "line_end": finding.line_end,
                "column_start": finding.column_start,
                "column_end": finding.column_end
            },
            "metadata": {
                "cwe": finding.cwe,
                "owasp": finding.owasp,
                "fix_guidance": finding.fix_guidance
            },
            "code_snippet": finding.code_snippet
        }
        
    def _generate_statistics(self, findings: List[SastFinding]) -> Dict[str, Any]:
        """Generate statistics from findings"""
        stats = {
            "total": len(findings),
            "by_severity": {},
            "by_tool": {},
            "by_category": {}
        }
        
        for finding in findings:
            # By severity
            stats["by_severity"][finding.severity] = stats["by_severity"].get(finding.severity, 0) + 1
            
            # By tool
            stats["by_tool"][finding.tool] = stats["by_tool"].get(finding.tool, 0) + 1
            
            # By category (from rule_id)
            category = finding.rule_id.split("_")[0] if "_" in finding.rule_id else "other"
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
            
        return stats
        
    def _get_tools_used(self, results: List[Any]) -> List[str]:
        """Get list of tools successfully used"""
        tools = []
        if self.semgrep_available:
            tools.append("semgrep")
        if self.bandit_available:
            tools.append("bandit")
        tools.append("custom")
        tools.append("heuristic")
        return tools
        
    def _map_semgrep_severity(self, severity: str) -> str:
        """Map Semgrep severity to standard severity"""
        mapping = {
            "ERROR": "CRITICAL",
            "WARNING": "HIGH",
            "INFO": "MEDIUM"
        }
        return mapping.get(severity.upper(), severity.upper())