"""
FastAPI routes for code analysis
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional, List, Dict, Any
import asyncio
import json
import hashlib
from datetime import datetime
import uuid

from analyzers.ast_analyzer import ASTSecurityAnalyzer
from analyzers.sast_analyzer import SastAnalyzer  
from ml.threat_detector import EnsembleThreatDetector
from services.cache_service import CacheService
from services.report_service import ReportService

# Create routers
analysis_router = APIRouter()
reports_router = APIRouter()
ml_router = APIRouter()

# Initialize services
ast_analyzer = ASTSecurityAnalyzer()
sast_analyzer = SastAnalyzer()
ml_detector = EnsembleThreatDetector()
cache_service = CacheService()
report_service = ReportService()

@analysis_router.post("/analyze")
async def analyze_code(
    file: Optional[UploadFile] = File(None),
    code: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> JSONResponse:
    """
    Comprehensive code analysis endpoint
    Accepts either file upload or direct code input
    """
    
    # Validate input
    if not file and not code:
        raise HTTPException(status_code=400, detail="Either file or code must be provided")
        
    # Get code content
    if file:
        if not file.filename.endswith('.py'):
            raise HTTPException(status_code=400, detail="Only Python files are supported")
        code = (await file.read()).decode('utf-8')
        filename = file.filename
    else:
        filename = "inline_code.py"
        
    # Generate analysis ID
    analysis_id = str(uuid.uuid4())
    
    # Check cache
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    cached_result = await cache_service.get(f"analysis:{code_hash}")
    
    if cached_result:
        return JSONResponse(
            content={
                "analysis_id": analysis_id,
                "status": "completed",
                "cached": True,
                "results": json.loads(cached_result)
            },
            headers={"X-Analysis-ID": analysis_id}
        )
        
    # Start analysis in background
    background_tasks.add_task(
        run_full_analysis,
        analysis_id,
        code,
        filename,
        code_hash
    )
    
    return JSONResponse(
        content={
            "analysis_id": analysis_id,
            "status": "processing",
            "message": "Analysis started. Use the analysis_id to check status."
        },
        headers={"X-Analysis-ID": analysis_id}
    )

async def run_full_analysis(
    analysis_id: str,
    code: str,
    filename: str,
    code_hash: str
):
    """Run complete analysis pipeline"""
    
    try:
        # Store initial status
        await cache_service.set(
            f"status:{analysis_id}",
            json.dumps({"status": "running", "progress": 0})
        )
        
        # Phase 1: AST Analysis
        await cache_service.set(
            f"status:{analysis_id}",
            json.dumps({"status": "running", "progress": 20, "stage": "AST Analysis"})
        )
        ast_results = await ast_analyzer.analyze(code)
        
        # Phase 2: SAST Analysis
        await cache_service.set(
            f"status:{analysis_id}",
            json.dumps({"status": "running", "progress": 40, "stage": "SAST Analysis"})
        )
        sast_results = await sast_analyzer.analyze(code, filename)
        
        # Phase 3: ML Threat Detection
        await cache_service.set(
            f"status:{analysis_id}",
            json.dumps({"status": "running", "progress": 60, "stage": "ML Analysis"})
        )
        ml_results = await ml_detector.analyze(code)
        
        # Phase 4: Generate Report
        await cache_service.set(
            f"status:{analysis_id}",
            json.dumps({"status": "running", "progress": 80, "stage": "Generating Report"})
        )
        
        # Combine results
        final_results = {
            "analysis_id": analysis_id,
            "timestamp": datetime.utcnow().isoformat(),
            "filename": filename,
            "code_hash": code_hash,
            "ast_analysis": ast_results,
            "sast_analysis": sast_results,
            "ml_analysis": ml_results,
            "summary": generate_summary(ast_results, sast_results, ml_results)
        }
        
        # Cache results
        await cache_service.set(
            f"analysis:{code_hash}",
            json.dumps(final_results),
            ttl=3600  # 1 hour
        )
        
        # Store results
        await cache_service.set(
            f"result:{analysis_id}",
            json.dumps(final_results)
        )
        
        # Update status to completed
        await cache_service.set(
            f"status:{analysis_id}",
            json.dumps({"status": "completed", "progress": 100})
        )
        
    except Exception as e:
        # Store error status
        await cache_service.set(
            f"status:{analysis_id}",
            json.dumps({
                "status": "error",
                "error": str(e)
            })
        )

@analysis_router.get("/status/{analysis_id}")
async def get_analysis_status(analysis_id: str) -> JSONResponse:
    """Check analysis status"""
    
    status = await cache_service.get(f"status:{analysis_id}")
    
    if not status:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    return JSONResponse(content=json.loads(status))

@analysis_router.get("/result/{analysis_id}")
async def get_analysis_result(analysis_id: str) -> JSONResponse:
    """Get analysis results"""
    
    result = await cache_service.get(f"result:{analysis_id}")
    
    if not result:
        # Check if still processing
        status = await cache_service.get(f"status:{analysis_id}")
        if status:
            status_data = json.loads(status)
            if status_data["status"] == "running":
                return JSONResponse(
                    content={
                        "status": "processing",
                        "message": "Analysis still in progress",
                        "progress": status_data.get("progress", 0)
                    }
                )
        raise HTTPException(status_code=404, detail="Analysis results not found")
        
    return JSONResponse(content=json.loads(result))

@analysis_router.post("/quick-scan")
async def quick_scan(code: str) -> JSONResponse:
    """Quick security scan without full analysis"""
    
    # Run only SAST for quick results
    sast_results = await sast_analyzer.analyze(code, "quick_scan.py")
    
    # Extract critical findings
    critical_findings = [
        f for f in sast_results["findings"]
        if f["severity"] in ["CRITICAL", "HIGH"]
    ]
    
    return JSONResponse(content={
        "scan_type": "quick",
        "critical_issues": len(critical_findings),
        "findings": critical_findings[:10],  # Top 10 critical findings
        "recommendation": "Run full analysis for comprehensive results"
    })

@reports_router.get("/generate/{analysis_id}")
async def generate_report(
    analysis_id: str,
    format: str = Query("json", enum=["json", "html", "pdf", "sarif"])
) -> StreamingResponse:
    """Generate analysis report in various formats"""
    
    # Get analysis results
    result = await cache_service.get(f"result:{analysis_id}")
    
    if not result:
        raise HTTPException(status_code=404, detail="Analysis results not found")
        
    results = json.loads(result)
    
    # Generate report based on format
    if format == "json":
        return StreamingResponse(
            iter([json.dumps(results, indent=2)]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=analysis_{analysis_id}.json"
            }
        )
    elif format == "sarif":
        sarif_report = await report_service.generate_sarif(results)
        return StreamingResponse(
            iter([json.dumps(sarif_report, indent=2)]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=analysis_{analysis_id}.sarif"
            }
        )
    elif format == "html":
        html_report = await report_service.generate_html(results)
        return StreamingResponse(
            iter([html_report]),
            media_type="text/html",
            headers={
                "Content-Disposition": f"attachment; filename=analysis_{analysis_id}.html"
            }
        )
    elif format == "pdf":
        pdf_bytes = await report_service.generate_pdf(results)
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=analysis_{analysis_id}.pdf"
            }
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")

@reports_router.get("/history")
async def get_analysis_history(
    limit: int = Query(10, le=100),
    offset: int = Query(0, ge=0)
) -> JSONResponse:
    """Get analysis history"""
    
    # This would query from a database in production
    # For now, return placeholder
    return JSONResponse(content={
        "total": 0,
        "limit": limit,
        "offset": offset,
        "analyses": []
    })

@ml_router.post("/train")
async def train_models(
    training_data: List[Dict[str, Any]],
    background_tasks: BackgroundTasks
) -> JSONResponse:
    """Train ML models with new data"""
    
    # Validate training data
    if not training_data or len(training_data) < 10:
        raise HTTPException(
            status_code=400,
            detail="Insufficient training data (minimum 10 samples required)"
        )
        
    # Start training in background
    training_id = str(uuid.uuid4())
    background_tasks.add_task(
        train_ml_models,
        training_id,
        training_data
    )
    
    return JSONResponse(content={
        "training_id": training_id,
        "status": "started",
        "message": "Model training initiated"
    })

async def train_ml_models(training_id: str, training_data: List[Dict[str, Any]]):
    """Train ML models with provided data"""
    
    try:
        # Extract code samples and labels
        code_samples = [d["code"] for d in training_data]
        labels = [d.get("label", 0) for d in training_data]
        
        # Train anomaly detector
        ml_detector.anomaly_detector.train(code_samples, labels)
        
        # Save models
        ml_detector.anomaly_detector.save_model(f"/tmp/model_{training_id}.joblib")
        
        # Update training status
        await cache_service.set(
            f"training:{training_id}",
            json.dumps({
                "status": "completed",
                "model_path": f"/tmp/model_{training_id}.joblib"
            })
        )
        
    except Exception as e:
        await cache_service.set(
            f"training:{training_id}",
            json.dumps({
                "status": "error",
                "error": str(e)
            })
        )

@ml_router.get("/models")
async def list_models() -> JSONResponse:
    """List available ML models"""
    
    return JSONResponse(content={
        "models": [
            {
                "name": "CodeBERT",
                "type": "transformer",
                "version": "1.0",
                "status": "active"
            },
            {
                "name": "IsolationForest",
                "type": "anomaly_detection", 
                "version": "1.0",
                "status": "active"
            }
        ]
    })

@ml_router.post("/predict")
async def predict_threats(code: str) -> JSONResponse:
    """Direct ML prediction endpoint"""
    
    results = await ml_detector.analyze(code)
    
    return JSONResponse(content={
        "predictions": results["predictions"],
        "threat_score": results["threat_score"],
        "high_risk": results["high_risk"],
        "recommendations": results["recommendations"]
    })

def generate_summary(ast_results: Dict, sast_results: Dict, ml_results: Dict) -> Dict[str, Any]:
    """Generate executive summary from all analysis results"""
    
    # Count vulnerabilities by severity
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    
    for finding in sast_results.get("findings", []):
        severity = finding.get("severity", "LOW")
        if severity in severity_counts:
            severity_counts[severity] += 1
            
    # Calculate overall risk score
    risk_score = (
        severity_counts["CRITICAL"] * 10 +
        severity_counts["HIGH"] * 5 +
        severity_counts["MEDIUM"] * 2 +
        severity_counts["LOW"] * 1
    )
    
    # Normalize risk score (0-100)
    risk_score = min(risk_score, 100)
    
    # Determine risk level
    if risk_score >= 70:
        risk_level = "CRITICAL"
    elif risk_score >= 50:
        risk_level = "HIGH"
    elif risk_score >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
        
    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "total_issues": sum(severity_counts.values()),
        "severity_distribution": severity_counts,
        "code_metrics": ast_results.get("metrics", {}),
        "ml_threat_score": ml_results.get("threat_score", 0),
        "recommendations": ml_results.get("recommendations", [])
    }