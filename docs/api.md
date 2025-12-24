---
layout: default
title: API Reference
---

# API Reference

REST API for programmatic access to the Self-Arguing Multi-Agent Analyst. All endpoints return structured JSON with deterministic outputs.

## Base URL

```
https://api.self-arguing-analyst.com/v1
```

Or locally:
```
http://localhost:8000
```

## Authentication

Currently open (for demo). Production deployments use API keys:

```bash
curl -H "X-API-Key: your-key" https://api.self-arguing-analyst.com/v1/analyze
```

## Endpoints

### 1. Analyze Incident

**POST** `/analyze`

Submit a cybersecurity incident for analysis.

**Request Body**:
```json
{
  "incident_text": "string (required)",
  "priority": "normal|high",
  "enable_mitre": false,
  "roles": ["benign", "malicious", "skeptic"]
}
```

**Response**:
```json
{
  "event_id": "uuid",
  "status": "queued|processing|completed",
  "decision": {
    "label": "BENIGN|MALICIOUS|UNCERTAIN",
    "confidence": 0.85,
    "reason_codes": ["CONSENSUS_BENIGN"]
  },
  "summary": {
    "total_evidence_items": 14,
    "residual_disagreement": 0.24,
    "agent_labels": {
      "benign": "BENIGN",
      "malicious": "BENIGN",
      "skeptic": "UNCERTAIN"
    }
  },
  "epistemic_status": "string",
  "artifacts_location": "path/to/artifacts"
}
```

**Example**:
```bash
curl -X POST "https://api.self-arguing-analyst.com/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_text": "User downloaded suspicious.exe from unknown domain",
    "priority": "high"
  }'
```

### 2. Get Results

**GET** `/results/{event_id}`

Retrieve analysis results for a specific event.

**Response**:
```json
{
  "event_id": "uuid",
  "status": "completed",
  "result": { /* full analysis result */ },
  "processing_time_seconds": 12.5,
  "completed_at": "2024-01-15T10:30:00Z"
}
```

### 3. Replay Analysis

**POST** `/replay/replay`

Recompute convergence metrics from stored artifacts (deterministic, no LLM calls).

**Request Body**:
```json
{
  "event_id": "uuid (required)",
  "recalculate": true
}
```

**Response**:
```json
{
  "event_id": "uuid",
  "status": "recomputed",
  "deterministic": true,
  "decision": { /* recomputed decision */ },
  "comparison_with_original": {
    "identical": true,
    "differences": {}
  }
}
```

### 4. Validate Artifacts

**GET** `/validate/{event_id}`

Validate artifact contracts for an event.

**Response**:
```json
{
  "event_id": "uuid",
  "valid": true,
  "missing_artifacts": [],
  "invalid_artifacts": [],
  "checks": {
    "incident_text": true,
    "evidence_files": true,
    "claims_files": true,
    "convergence_files": true
  }
}
```

### 5. System Metrics

**GET** `/metrics`

Prometheus metrics for monitoring.

**Response** (Prometheus format):
```
# HELP analysis_requests_total Total analysis requests
# TYPE analysis_requests_total counter
analysis_requests_total{status="completed"} 142

# HELP residual_disagreement Current residual disagreement
# TYPE residual_disagreement gauge
residual_disagreement 0.31

# HELP uncertainty_rate Rate of UNCERTAIN decisions
# TYPE uncertainty_rate gauge
uncertainty_rate 0.18
```

### 6. List Events

**GET** `/events`

List available analysis events.

**Query Parameters**:
- `limit`: Maximum events to return (default: 20)
- `status`: Filter by status (completed, processing, failed)

**Response**:
```json
{
  "total_events": 156,
  "events": [
    {
      "event_id": "uuid",
      "incident_preview": "User downloaded...",
      "decision": "UNCERTAIN",
      "confidence": 0.42,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

## WebSocket API

### Real-time Analysis Progress

**WS** `/ws/analysis/{event_id}`

Subscribe to real-time updates for an analysis.

**Messages**:
```json
{
  "type": "progress",
  "stage": "evidence_extraction|claims_generation|convergence",
  "progress": 0.67,
  "agent": "benign"
}
```

```json
{
  "type": "complete",
  "result": { /* full analysis result */ }
}
```

## Error Responses

All endpoints use standard HTTP status codes:

- `200`: Success
- `400`: Bad request (invalid input)
- `404`: Resource not found
- `429`: Rate limit exceeded
- `500`: Internal server error

Error response format:
```json
{
  "error": "string",
  "detail": "string (optional)",
  "event_id": "uuid (if applicable)"
}
```

## Rate Limiting

- **Free tier**: 10 requests/hour
- **Authenticated**: 100 requests/hour
- **High priority**: 1000 requests/hour (contact for access)

Headers included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1705312800
```

## Python Client Example

```python
from self_arguing_analyst import Client

client = Client(api_key="your-key")

# Analyze incident
result = client.analyze(
    incident_text="Suspicious PowerShell activity detected",
    priority="high"
)

print(f"Decision: {result.decision.label}")
print(f"Confidence: {result.decision.confidence}")
print(f"Residual Disagreement: {result.summary.residual_disagreement}")

# Replay analysis
replay = client.replay(result.event_id)
print(f"Deterministic: {replay.deterministic}")

# Export artifacts
export = client.export(result.event_id, "./exports")
```

## cURL Examples

### Basic Analysis
```bash
curl -X POST "https://api.self-arguing-analyst.com/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{"incident_text": "Malware detected on endpoint"}'
```

### With MITRE Enrichment
```bash
curl -X POST "https://api.self-arguing-analyst.com/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_text": "Ransomware encrypted files",
    "enable_mitre": true,
    "roles": ["benign", "malicious", "threat_intel"]
  }'
```

### Batch Validation
```bash
curl "https://api.self-arguing-analyst.com/v1/batch-validate"
```

## SDK Availability

Official SDKs:
- **Python**: `pip install self-arguing-analyst`
- **JavaScript/TypeScript**: `npm install self-arguing-analyst`
- **Go**: `go get github.com/mastercaleb254/self-arguing-analyst/sdk/go`
- **Rust**: `cargo add self_arguing_analyst`

## OpenAPI Specification

Full OpenAPI 3.0 specification available at:
- `/docs` - Interactive Swagger UI
- `/openapi.json` - Raw OpenAPI JSON
- `/redoc` - ReDoc documentation

---

**This API exposes the system's capabilities, not its implementation.** The interface is simple; the engineering is complex.
