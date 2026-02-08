"""
Monitoring and metrics service
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
from fastapi import Request

# Metrics
request_count = Counter('qtrace_requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('qtrace_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
active_connections = Gauge('qtrace_active_connections', 'Active WebSocket connections')
analysis_counter = Counter('qtrace_analyses_total', 'Total analyses performed')
error_counter = Counter('qtrace_errors_total', 'Total errors', ['type'])

class PrometheusMetrics:
    """Prometheus metrics manager"""
    
    def __init__(self):
        self.start_time = time.time()
        
    def start_metrics_server(self):
        """Start metrics server (called during app startup)"""
        pass  # Metrics exposed via /metrics endpoint
        
    def get_uptime(self) -> float:
        """Get application uptime in seconds"""
        return time.time() - self.start_time
        
    def generate_metrics(self):
        """Generate Prometheus metrics"""
        return generate_latest()

async def metrics_middleware(request: Request, call_next):
    """Middleware for collecting request metrics"""
    start_time = time.time()
    
    # Record request
    request_count.labels(
        method=request.method,
        endpoint=request.url.path
    ).inc()
    
    # Process request
    response = await call_next(request)
    
    # Record duration
    duration = time.time() - start_time
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response