# Q-Trace Pro API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
Currently, the API is open. In production, implement JWT authentication.

## Endpoints

### Analysis

#### POST /analysis/analyze
Analyze Python code for security vulnerabilities.

**Request:**
```json
{
  "code": "string",
  "file": "binary (optional)"
}
```

**Response:**
```json
{
  "analysis_id": "uuid",
  "status": "processing",
  "message": "Analysis started"
}
```

#### GET /analysis/status/{analysis_id}
Get analysis status.

**Response:**
```json
{
  "status": "running|completed|error",
  "progress": 75,
  "stage": "SAST Analysis"
}
```

#### GET /analysis/result/{analysis_id}
Get complete analysis results.

**Response:**
```json
{
  "analysis_id": "uuid",
  "timestamp": "2024-01-01T00:00:00",
  "ast_analysis": {
    "metrics": {},
    "vulnerabilities": [],
    "data_flow": {},
    "control_flow": {}
  },
  "sast_analysis": {
    "findings": [],
    "statistics": {}
  },
  "ml_analysis": {
    "predictions": [],
    "threat_score": 0.85
  },
  "summary": {
    "risk_score": 75,
    "risk_level": "HIGH",
    "total_issues": 10
  }
}
```

#### POST /analysis/quick-scan
Perform a quick security scan.

**Request:**
```json
{
  "code": "string"
}
```

**Response:**
```json
{
  "scan_type": "quick",
  "critical_issues": 3,
  "findings": []
}
```

### Reports

#### GET /reports/generate/{analysis_id}
Generate analysis report in various formats.

**Query Parameters:**
- `format`: json|sarif|html|pdf (default: json)

**Response:**
File download in requested format.

#### GET /reports/history
Get analysis history.

**Query Parameters:**
- `limit`: number (default: 10, max: 100)
- `offset`: number (default: 0)

**Response:**
```json
{
  "total": 50,
  "limit": 10,
  "offset": 0,
  "analyses": []
}
```

### Machine Learning

#### POST /ml/train
Train ML models with new data.

**Request:**
```json
{
  "training_data": [
    {
      "code": "string",
      "label": 0
    }
  ]
}
```

**Response:**
```json
{
  "training_id": "uuid",
  "status": "started"
}
```

#### GET /ml/models
List available ML models.

**Response:**
```json
{
  "models": [
    {
      "name": "CodeBERT",
      "type": "transformer",
      "version": "1.0",
      "status": "active"
    }
  ]
}
```

#### POST /ml/predict
Direct ML prediction.

**Request:**
```json
{
  "code": "string"
}
```

**Response:**
```json
{
  "predictions": [],
  "threat_score": 0.85,
  "high_risk": true,
  "recommendations": []
}
```

### WebSocket

#### WS /ws/analysis/{client_id}
Real-time analysis updates via WebSocket.

**Message Types:**

Client → Server:
```json
{
  "type": "start_analysis",
  "code": "string"
}
```

Server → Client:
```json
{
  "type": "progress",
  "stage": "SAST Analysis",
  "progress": 50
}
```

```json
{
  "type": "complete",
  "results": {}
}
```

### Health & Monitoring

#### GET /
Basic health check.

**Response:**
```json
{
  "status": "healthy",
  "service": "Q-Trace Pro Security Platform",
  "version": "2.0.0"
}
```

#### GET /health
Detailed health status.

**Response:**
```json
{
  "status": "healthy",
  "checks": {
    "cache": true,
    "websocket_connections": 5
  }
}
```

#### GET /metrics
Prometheus metrics endpoint.

**Response:**
```
# HELP qtrace_requests_total Total requests
# TYPE qtrace_requests_total counter
qtrace_requests_total{method="GET",endpoint="/"} 100
```

## Error Responses

All endpoints may return error responses:

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

## Rate Limiting

- Default: 100 requests per minute per IP
- Analyze endpoint: 10 requests per minute per IP

## Status Codes

- `200`: Success
- `201`: Created
- `400`: Bad Request
- `404`: Not Found
- `422`: Validation Error
- `429`: Rate Limited
- `500`: Internal Server Error