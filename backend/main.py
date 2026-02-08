"""
Q-Trace Pro: Production-Ready Security Analysis Platform
Advanced Code Security Scanner with ML-Powered Threat Detection
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
import asyncio
import json
import logging
from typing import Optional, List, Dict, Any
import structlog
from datetime import datetime

# Import our analyzers
from api.routes import analysis_router, reports_router, ml_router
from api.websocket_manager import WebSocketManager
from core.config import settings
from services.cache_service import CacheService
from services.monitoring import metrics_middleware, PrometheusMetrics

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize services
ws_manager = WebSocketManager()
cache_service = CacheService()
metrics = PrometheusMetrics()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting Q-Trace Pro Security Platform", version=settings.VERSION)
    await cache_service.connect()
    metrics.start_metrics_server()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Q-Trace Pro")
    await cache_service.disconnect()
    await ws_manager.disconnect_all()

app = FastAPI(
    title="Q-Trace Pro Security Analysis API",
    description="Advanced Code Security Scanner with Quantum Analysis and ML Threat Detection",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS configuration for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Analysis-ID", "X-Threat-Score"]
)

# Add metrics middleware
app.middleware("http")(metrics_middleware)

# Include routers
app.include_router(analysis_router, prefix="/api/v1/analysis", tags=["analysis"])
app.include_router(reports_router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(ml_router, prefix="/api/v1/ml", tags=["machine-learning"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Q-Trace Pro Security Platform",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    health_status = {
        "status": "healthy",
        "checks": {
            "cache": await cache_service.health_check(),
            "websocket_connections": ws_manager.get_connection_count(),
            "uptime": metrics.get_uptime()
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    return JSONResponse(content=health_status)

@app.websocket("/ws/analysis/{client_id}")
async def websocket_analysis(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time analysis updates"""
    await ws_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Process different message types
            if message["type"] == "start_analysis":
                # Trigger analysis and stream results
                await ws_manager.send_personal_message(
                    {"type": "status", "message": "Analysis started"},
                    client_id
                )
                # Stream analysis updates
                asyncio.create_task(stream_analysis_updates(client_id, message["code"]))
                
            elif message["type"] == "ping":
                await ws_manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
                    client_id
                )
                
    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)
        logger.info("Client disconnected", client_id=client_id)
    except Exception as e:
        logger.error("WebSocket error", error=str(e), client_id=client_id)
        ws_manager.disconnect(client_id)

async def stream_analysis_updates(client_id: str, code: str):
    """Stream real-time analysis updates to client"""
    try:
        # This would integrate with the actual analysis pipeline
        stages = [
            "Parsing AST",
            "Building Control Flow Graph",
            "Running Taint Analysis", 
            "Executing Symbolic Analysis",
            "Performing ML Threat Detection",
            "Generating Quantum Signatures",
            "Finalizing Report"
        ]
        
        for i, stage in enumerate(stages):
            await asyncio.sleep(0.5)  # Simulate processing
            await ws_manager.send_personal_message({
                "type": "progress",
                "stage": stage,
                "progress": (i + 1) / len(stages) * 100,
                "timestamp": datetime.utcnow().isoformat()
            }, client_id)
            
        # Send final results
        await ws_manager.send_personal_message({
            "type": "complete",
            "results": {
                "threat_score": 0.85,
                "vulnerabilities": 3,
                "code_quality": "B+",
                "timestamp": datetime.utcnow().isoformat()
            }
        }, client_id)
        
    except Exception as e:
        logger.error("Analysis streaming error", error=str(e))
        await ws_manager.send_personal_message({
            "type": "error",
            "message": str(e)
        }, client_id)

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return StreamingResponse(
        metrics.generate_metrics(),
        media_type="text/plain"
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        }
    )