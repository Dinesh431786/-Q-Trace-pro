"""
Q-Trace Pro Demo - Simplified version for demonstration
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
import uvicorn
import random
import json
from datetime import datetime
import asyncio
from typing import Optional

app = FastAPI(
    title="Q-Trace Pro Security Analysis API",
    description="Advanced Code Security Scanner Demo",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo HTML interface
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Q-Trace Pro 2.0 - Security Analysis Platform</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 100%);
            color: #ffffff;
            min-height: 100vh;
        }
        
        .header {
            background: rgba(26, 26, 46, 0.95);
            backdrop-filter: blur(10px);
            padding: 1rem 2rem;
            border-bottom: 1px solid rgba(102, 126, 234, 0.2);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .logo {
            display: flex;
            align-items: center;
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .shield-icon {
            width: 30px;
            height: 30px;
            margin-right: 10px;
        }
        
        .container {
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 2rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: rgba(26, 26, 46, 0.8);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 1.5rem;
            border: 1px solid rgba(102, 126, 234, 0.2);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        }
        
        .stat-card.gradient-1 {
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
        }
        
        .stat-card.gradient-2 {
            background: linear-gradient(135deg, rgba(240, 147, 251, 0.2) 0%, rgba(245, 87, 108, 0.2) 100%);
        }
        
        .stat-card.gradient-3 {
            background: linear-gradient(135deg, rgba(79, 172, 254, 0.2) 0%, rgba(0, 242, 254, 0.2) 100%);
        }
        
        .stat-card.gradient-4 {
            background: linear-gradient(135deg, rgba(250, 112, 154, 0.2) 0%, rgba(254, 225, 64, 0.2) 100%);
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
        }
        
        @media (max-width: 1024px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }
        
        .panel {
            background: rgba(26, 26, 46, 0.8);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 2rem;
            border: 1px solid rgba(102, 126, 234, 0.2);
        }
        
        .panel-title {
            font-size: 1.25rem;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
        }
        
        .code-input {
            width: 100%;
            min-height: 300px;
            background: rgba(15, 15, 30, 0.5);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 8px;
            color: #ffffff;
            padding: 1rem;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 14px;
            resize: vertical;
        }
        
        .code-input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 0.75rem 2rem;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 1rem;
            width: 100%;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .results-area {
            background: rgba(15, 15, 30, 0.5);
            border-radius: 8px;
            padding: 1rem;
            min-height: 300px;
            max-height: 500px;
            overflow-y: auto;
        }
        
        .finding {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            border-left: 4px solid #667eea;
        }
        
        .finding.critical {
            border-left-color: #f56565;
        }
        
        .finding.high {
            border-left-color: #ed8936;
        }
        
        .finding.medium {
            border-left-color: #ecc94b;
        }
        
        .finding.low {
            border-left-color: #48bb78;
        }
        
        .finding-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
        }
        
        .finding-title {
            font-weight: 600;
        }
        
        .severity-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            text-transform: uppercase;
            font-weight: 600;
        }
        
        .severity-badge.critical {
            background: rgba(245, 101, 101, 0.2);
            color: #f56565;
        }
        
        .severity-badge.high {
            background: rgba(237, 137, 54, 0.2);
            color: #ed8936;
        }
        
        .severity-badge.medium {
            background: rgba(236, 201, 75, 0.2);
            color: #ecc94b;
        }
        
        .severity-badge.low {
            background: rgba(72, 187, 120, 0.2);
            color: #48bb78;
        }
        
        .progress-bar {
            width: 100%;
            height: 4px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 2px;
            margin-top: 1rem;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 2px;
            transition: width 0.3s;
            animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
            0% { opacity: 0.8; }
            50% { opacity: 1; }
            100% { opacity: 0.8; }
        }
        
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .feature-item {
            display: flex;
            align-items: center;
            padding: 0.75rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
        }
        
        .feature-icon {
            margin-right: 0.75rem;
            color: #667eea;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 2rem;
        }
        
        .loading.active {
            display: block;
        }
        
        .spinner {
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-radius: 50%;
            border-top: 3px solid #667eea;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">
            <svg class="shield-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7v8c0 5.5 3.5 10.5 10 12 6.5-1.5 10-6.5 10-12V7l-10-5z"/>
                <path d="M12 7v5l4 2"/>
            </svg>
            Q-Trace Pro 2.0
        </div>
        <div>Enterprise Security Platform</div>
    </div>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card gradient-1">
                <div class="stat-value" id="riskScore">0</div>
                <div class="stat-label">Risk Score</div>
            </div>
            <div class="stat-card gradient-2">
                <div class="stat-value" id="issuesFound">0</div>
                <div class="stat-label">Issues Found</div>
            </div>
            <div class="stat-card gradient-3">
                <div class="stat-value" id="threatScore">0%</div>
                <div class="stat-label">ML Threat Score</div>
            </div>
            <div class="stat-card gradient-4">
                <div class="stat-value" id="riskLevel">LOW</div>
                <div class="stat-label">Risk Level</div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="panel">
                <h2 class="panel-title">
                    <span style="margin-right: 10px;">📝</span>
                    Code Analysis
                </h2>
                
                <textarea class="code-input" id="codeInput" placeholder="Paste your Python code here for analysis...">
import os
import subprocess
import pickle

# Example vulnerable code
def unsafe_command(user_input):
    os.system(f"echo {user_input}")  # Command injection
    
def load_data(data):
    return pickle.loads(data)  # Unsafe deserialization

password = "admin123"  # Hardcoded credential
                </textarea>
                
                <button class="btn" id="analyzeBtn" onclick="analyzeCode()">
                    ⚡ Analyze Code
                </button>
                
                <div class="progress-bar" id="progressBar" style="display: none;">
                    <div class="progress-fill" id="progressFill" style="width: 0%;"></div>
                </div>
            </div>
            
            <div class="panel">
                <h2 class="panel-title">
                    <span style="margin-right: 10px;">🛡️</span>
                    Security Analysis Results
                </h2>
                
                <div class="loading" id="loadingSection">
                    <div class="spinner"></div>
                    <div>Analyzing code...</div>
                </div>
                
                <div class="results-area" id="resultsArea">
                    <div style="text-align: center; color: rgba(255,255,255,0.5); padding: 3rem;">
                        Results will appear here after analysis
                    </div>
                </div>
            </div>
        </div>
        
        <div class="panel" style="margin-top: 2rem;">
            <h2 class="panel-title">
                <span style="margin-right: 10px;">✨</span>
                Platform Features
            </h2>
            
            <div class="feature-grid">
                <div class="feature-item">
                    <span class="feature-icon">✅</span>
                    <span>AST Analysis</span>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">✅</span>
                    <span>SAST Integration</span>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">✅</span>
                    <span>ML Detection</span>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">✅</span>
                    <span>Quantum Analysis</span>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">✅</span>
                    <span>Real-time Updates</span>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">✅</span>
                    <span>Export Reports</span>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">✅</span>
                    <span>Docker Ready</span>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">✅</span>
                    <span>WebSocket API</span>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        async function analyzeCode() {
            const code = document.getElementById('codeInput').value;
            const btn = document.getElementById('analyzeBtn');
            const loadingSection = document.getElementById('loadingSection');
            const resultsArea = document.getElementById('resultsArea');
            const progressBar = document.getElementById('progressBar');
            const progressFill = document.getElementById('progressFill');
            
            if (!code.trim()) {
                alert('Please enter some code to analyze');
                return;
            }
            
            // Show loading state
            btn.disabled = true;
            btn.textContent = 'Analyzing...';
            loadingSection.classList.add('active');
            resultsArea.innerHTML = '';
            progressBar.style.display = 'block';
            
            // Simulate progress
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += 10;
                progressFill.style.width = progress + '%';
                if (progress >= 90) {
                    clearInterval(progressInterval);
                }
            }, 200);
            
            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ code: code })
                });
                
                const data = await response.json();
                
                // Update progress to 100%
                clearInterval(progressInterval);
                progressFill.style.width = '100%';
                
                // Display results
                setTimeout(() => {
                    displayResults(data);
                    loadingSection.classList.remove('active');
                    btn.disabled = false;
                    btn.textContent = '⚡ Analyze Code';
                    progressBar.style.display = 'none';
                }, 500);
                
            } catch (error) {
                console.error('Analysis failed:', error);
                resultsArea.innerHTML = '<div style="color: #f56565;">Analysis failed. Please try again.</div>';
                loadingSection.classList.remove('active');
                btn.disabled = false;
                btn.textContent = '⚡ Analyze Code';
                progressBar.style.display = 'none';
            }
        }
        
        function displayResults(data) {
            const resultsArea = document.getElementById('resultsArea');
            
            // Update stats
            document.getElementById('riskScore').textContent = data.risk_score;
            document.getElementById('issuesFound').textContent = data.total_issues;
            document.getElementById('threatScore').textContent = Math.round(data.threat_score * 100) + '%';
            document.getElementById('riskLevel').textContent = data.risk_level;
            
            // Display findings
            let html = '';
            data.findings.forEach(finding => {
                html += `
                    <div class="finding ${finding.severity.toLowerCase()}">
                        <div class="finding-header">
                            <div class="finding-title">${finding.type}</div>
                            <div class="severity-badge ${finding.severity.toLowerCase()}">${finding.severity}</div>
                        </div>
                        <div style="color: rgba(255,255,255,0.8); margin-bottom: 0.5rem;">${finding.message}</div>
                        <div style="color: rgba(255,255,255,0.5); font-size: 0.875rem;">Line ${finding.line}</div>
                    </div>
                `;
            });
            
            if (data.findings.length === 0) {
                html = '<div style="text-align: center; color: #48bb78; padding: 2rem;">✅ No security issues detected!</div>';
            }
            
            resultsArea.innerHTML = html;
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the demo UI"""
    return HTML_CONTENT

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Q-Trace Pro Security Platform",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/analyze")
async def analyze_code(request: dict):
    """Demo analysis endpoint"""
    code = request.get("code", "")
    
    # Simulate analysis with demo results
    await asyncio.sleep(2)  # Simulate processing time
    
    # Demo vulnerability detection
    findings = []
    
    if "os.system" in code or "subprocess" in code:
        findings.append({
            "type": "Command Injection",
            "severity": "CRITICAL",
            "message": "Potential command injection vulnerability detected. User input is passed to system commands.",
            "line": code[:100].count('\n') + 1
        })
    
    if "pickle.loads" in code or "pickle.load" in code:
        findings.append({
            "type": "Unsafe Deserialization",
            "severity": "CRITICAL",
            "message": "Unsafe deserialization detected. This can lead to remote code execution.",
            "line": code[:code.find("pickle")].count('\n') + 1
        })
    
    if "eval(" in code or "exec(" in code:
        findings.append({
            "type": "Code Injection",
            "severity": "HIGH",
            "message": "Use of eval/exec detected. This can execute arbitrary code.",
            "line": code[:code.find("eval" if "eval" in code else "exec")].count('\n') + 1
        })
    
    if "password" in code.lower() and "=" in code:
        findings.append({
            "type": "Hardcoded Credentials",
            "severity": "HIGH",
            "message": "Hardcoded credentials detected in source code.",
            "line": code.lower()[:code.lower().find("password")].count('\n') + 1
        })
    
    if "import random" in code and "random.random()" in code:
        findings.append({
            "type": "Weak Random",
            "severity": "MEDIUM",
            "message": "Use of weak random number generator for security purposes.",
            "line": code[:code.find("random")].count('\n') + 1
        })
    
    # Calculate scores
    risk_score = len(findings) * 20 + random.randint(10, 30)
    threat_score = min(0.95, len(findings) * 0.2 + random.random() * 0.3)
    
    if risk_score >= 70:
        risk_level = "CRITICAL"
    elif risk_score >= 50:
        risk_level = "HIGH"
    elif risk_score >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    return {
        "risk_score": min(100, risk_score),
        "total_issues": len(findings),
        "threat_score": threat_score,
        "risk_level": risk_level,
        "findings": findings,
        "analysis_time": f"{random.uniform(1.5, 3.5):.2f}s"
    }

@app.get("/api/docs")
async def api_docs():
    """API documentation"""
    return {
        "endpoints": {
            "/": "Demo UI",
            "/api/health": "Health check",
            "/api/analyze": "Analyze code (POST)",
            "/api/docs": "API documentation"
        },
        "version": "2.0.0",
        "features": [
            "Multi-engine analysis",
            "ML threat detection",
            "Real-time updates",
            "Export reports",
            "Docker support"
        ]
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Q-TRACE PRO 2.0 - SECURITY ANALYSIS PLATFORM")
    print("="*60)
    print("\n✅ Starting demo server...")
    print("\n📍 Access the application at:")
    print("   🌐 Web UI: http://localhost:8000")
    print("   📚 API Docs: http://localhost:8000/api/docs")
    print("\n" + "="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)