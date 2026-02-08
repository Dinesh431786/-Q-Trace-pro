"""
Report generation service for multiple formats
"""

from typing import Dict, Any
import json
from datetime import datetime
import base64

class ReportService:
    """Generate reports in various formats"""
    
    async def generate_sarif(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SARIF format report"""
        
        sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "Q-Trace Pro",
                            "version": "2.0.0",
                            "informationUri": "https://qtrace-pro.com",
                            "rules": self._generate_sarif_rules(results)
                        }
                    },
                    "results": self._generate_sarif_results(results),
                    "invocations": [
                        {
                            "executionSuccessful": True,
                            "endTimeUtc": datetime.utcnow().isoformat() + "Z"
                        }
                    ]
                }
            ]
        }
        
        return sarif
        
    async def generate_html(self, results: Dict[str, Any]) -> str:
        """Generate HTML report"""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Q-Trace Pro Security Report</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; }}
                .summary {{ background: #f7fafc; padding: 20px; border-radius: 10px; margin: 20px 0; }}
                .finding {{ background: white; border: 1px solid #e2e8f0; padding: 15px; margin: 10px 0; border-radius: 8px; }}
                .critical {{ border-left: 4px solid #f56565; }}
                .high {{ border-left: 4px solid #ed8936; }}
                .medium {{ border-left: 4px solid #ecc94b; }}
                .low {{ border-left: 4px solid #48bb78; }}
                .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
                .metric-value {{ font-size: 24px; font-weight: bold; }}
                .metric-label {{ color: #718096; font-size: 14px; }}
                pre {{ background: #2d3748; color: #fff; padding: 10px; border-radius: 5px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Q-Trace Pro Security Analysis Report</h1>
                <p>Generated: {datetime.utcnow().isoformat()}</p>
            </div>
            
            <div class="summary">
                <h2>Executive Summary</h2>
                <div class="metric">
                    <div class="metric-value">{results.get('summary', {}).get('risk_score', 0)}</div>
                    <div class="metric-label">Risk Score</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{results.get('summary', {}).get('total_issues', 0)}</div>
                    <div class="metric-label">Total Issues</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{results.get('summary', {}).get('risk_level', 'LOW')}</div>
                    <div class="metric-label">Risk Level</div>
                </div>
            </div>
            
            <h2>Findings</h2>
            {self._generate_html_findings(results)}
            
            <h2>Recommendations</h2>
            <ul>
                {''.join(f"<li>{rec}</li>" for rec in results.get('summary', {}).get('recommendations', []))}
            </ul>
        </body>
        </html>
        """
        
        return html
        
    async def generate_pdf(self, results: Dict[str, Any]) -> bytes:
        """Generate PDF report (simplified - would use reportlab in production)"""
        
        # For now, return a simple text representation
        # In production, use reportlab or similar library
        content = f"""
Q-TRACE PRO SECURITY REPORT
============================
Generated: {datetime.utcnow().isoformat()}

EXECUTIVE SUMMARY
-----------------
Risk Score: {results.get('summary', {}).get('risk_score', 0)}
Risk Level: {results.get('summary', {}).get('risk_level', 'LOW')}
Total Issues: {results.get('summary', {}).get('total_issues', 0)}

FINDINGS
--------
{self._generate_text_findings(results)}

RECOMMENDATIONS
---------------
{chr(10).join('• ' + rec for rec in results.get('summary', {}).get('recommendations', []))}
        """
        
        return content.encode('utf-8')
        
    def _generate_sarif_rules(self, results: Dict[str, Any]) -> list:
        """Generate SARIF rules from findings"""
        rules = []
        seen_rules = set()
        
        for finding in results.get('sast_analysis', {}).get('findings', []):
            rule_id = finding.get('rule_id')
            if rule_id and rule_id not in seen_rules:
                seen_rules.add(rule_id)
                rules.append({
                    "id": rule_id,
                    "shortDescription": {
                        "text": finding.get('message', '')[:100]
                    },
                    "fullDescription": {
                        "text": finding.get('message', '')
                    },
                    "defaultConfiguration": {
                        "level": self._map_severity_to_sarif(finding.get('severity', 'note'))
                    }
                })
                
        return rules
        
    def _generate_sarif_results(self, results: Dict[str, Any]) -> list:
        """Generate SARIF results from findings"""
        sarif_results = []
        
        for finding in results.get('sast_analysis', {}).get('findings', []):
            sarif_results.append({
                "ruleId": finding.get('rule_id', 'unknown'),
                "message": {
                    "text": finding.get('message', '')
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": finding.get('location', {}).get('file', 'unknown')
                            },
                            "region": {
                                "startLine": finding.get('location', {}).get('line_start', 1),
                                "endLine": finding.get('location', {}).get('line_end', 1)
                            }
                        }
                    }
                ]
            })
            
        return sarif_results
        
    def _map_severity_to_sarif(self, severity: str) -> str:
        """Map severity to SARIF level"""
        mapping = {
            "CRITICAL": "error",
            "HIGH": "error",
            "MEDIUM": "warning",
            "LOW": "note",
            "INFO": "note"
        }
        return mapping.get(severity.upper(), "note")
        
    def _generate_html_findings(self, results: Dict[str, Any]) -> str:
        """Generate HTML for findings"""
        html_findings = []
        
        for finding in results.get('sast_analysis', {}).get('findings', [])[:20]:
            severity = finding.get('severity', 'LOW').lower()
            html_findings.append(f"""
                <div class="finding {severity}">
                    <h3>{finding.get('rule_id', 'Unknown')}</h3>
                    <p><strong>Severity:</strong> {finding.get('severity', 'Unknown')}</p>
                    <p><strong>Message:</strong> {finding.get('message', '')}</p>
                    <p><strong>Location:</strong> Line {finding.get('location', {}).get('line_start', '?')}</p>
                    {f"<pre>{finding.get('code_snippet', '')}</pre>" if finding.get('code_snippet') else ''}
                </div>
            """)
            
        return ''.join(html_findings)
        
    def _generate_text_findings(self, results: Dict[str, Any]) -> str:
        """Generate text representation of findings"""
        findings_text = []
        
        for finding in results.get('sast_analysis', {}).get('findings', [])[:20]:
            findings_text.append(f"""
[{finding.get('severity', 'UNKNOWN')}] {finding.get('rule_id', 'Unknown')}
{finding.get('message', '')}
Location: Line {finding.get('location', {}).get('line_start', '?')}
---
            """)
            
        return ''.join(findings_text)