---
layout: default
title: Architecture
---

# Architecture

The system follows a layered, deterministic architecture where each component has a clear responsibility and no hidden magic.

## High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                    Event Orchestrator                       │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Benign     │  │  Malicious  │  │   Skeptic   │        │
│  │  Analyst    │  │  Analyst    │  │   Analyst   │        │
│  │             │  │             │  │             │        │
│  │  • Evidence │  │  • Evidence │  │  • Evidence │        │
│  │    Extract  │  │    Extract  │  │    Extract  │        │
│  │  • Claims   │  │  • Claims   │  │  • Claims   │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           │                                  │
│                  ┌────────▼────────┐                        │
│                  │                 │                        │
│                  │  Convergence    │                        │
│                  │    Engine       │                        │
│                  │                 │                        │
│                  │  • Deterministic│                        │
│                  │  • Metrics-based│                        │
│                  │  • No LLM calls │                        │
│                  └────────┬────────┘                        │
│                           │                                  │
│                  ┌────────▼────────┐                        │
│                  │  FINAL OUTPUT   │                        │
│                  │                 │                        │
│                  │  • BENIGN       │                        │
│                  │  • MALICIOUS    │ ◄─ UNCERTAIN           │
│                  │  • UNCERTAIN    │    when thresholds     │
│                  └─────────────────┘    not met             │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Event Orchestrator
**Responsibility**: Coordinate parallel agent execution while enforcing isolation
- Accepts incident text as input
- Dispatches to agents in parallel
- Enforces reasoning isolation (no shared context)
- Aggregates and persists artifacts
- **No LLM calls** - pure coordination logic

### 2. Agent System (Three Independent Perspectives)
Each agent:
- Extracts evidence with exact source spans
- Generates claims citing only their own evidence
- May contradict default stance if evidence warrants
- Outputs structured JSON with confidence scores

**Agents**:
- **Benign Analyst**: Looks for non-malicious explanations
- **Malicious Analyst**: Searches for indicators of compromise  
- **Skeptic Analyst**: Challenges assumptions, emphasizes evidence gaps

### 3. Evidence Extraction
- Structured extraction with source character spans
- Normalized evidence items for overlap computation
- Atomic evidence (no combined summaries)
- Each item must have exact quote from text

### 4. Convergence Engine (Deterministic)
**Key principle**: No LLM calls for consensus decisions
- Computes evidence overlap (Jaccard similarity)
- Calculates disagreement entropy
- Applies threshold logic (configurable)
- Produces final label with confidence
- **Fully reproducible** from stored artifacts

### 5. Artifact System
- All intermediate results stored as JSONL
- Schema-enforced structure (Pydantic)
- Replay mode recomputes convergence without LLMs
- Hash-verified exports for reproducibility

## Data Flow

```python
# Pseudo-code of the deterministic flow
def analyze_incident(incident_text):
    # Step 1: Parallel evidence extraction
    evidence = {
        "benign": extract_evidence(incident_text, "benign"),
        "malicious": extract_evidence(incident_text, "malicious"),
        "skeptic": extract_evidence(incident_text, "skeptic")
    }
    
    # Step 2: Parallel claims generation
    claims = {
        "benign": generate_claims(incident_text, evidence["benign"]),
        "malicious": generate_claims(incident_text, evidence["malicious"]),
        "skeptic": generate_claims(incident_text, evidence["skeptic"])
    }
    
    # Step 3: Deterministic convergence
    metrics = compute_convergence_metrics(evidence, claims)
    
    # Step 4: Threshold-based decision
    if meets_consensus_threshold(metrics):
        return {"label": consensus_label, "confidence": metrics.confidence}
    else:
        return {"label": "UNCERTAIN", "confidence": 1 - metrics.residual_disagreement}
```

## Key Architectural Decisions

### 1. Deterministic Convergence
**Choice**: No LLM in decision loop
**Reason**: Ensures reproducibility and avoids hidden reasoning
**Implementation**: Pure Python with configurable thresholds

### 2. Evidence Isolation
**Choice**: Agents cannot see each other's reasoning initially
**Reason**: Preserves epistemic independence
**Implementation**: Parallel execution with no shared context

### 3. Structured Artifacts
**Choice**: JSONL storage with strict schemas
**Reason**: Enables replay and audit trails
**Implementation**: Pydantic models with validation

### 4. Measurable Disagreement
**Choice**: Quantify rather than eliminate disagreement
**Reason**: Turns uncertainty into signal
**Implementation**: Residual disagreement metric (0-1)

## File Structure

```
self-arguing-analyst/
├── src/
│   ├── agents/           # LLM agents with structured outputs
│   ├── schemas/          # Pydantic models (strict validation)
│   ├── orchestrator.py   # Event coordination
│   ├── convergence_engine.py  # Deterministic logic
│   └── replay/           # Artifact replay system
├── api/
│   └── main.py          # REST API (FastAPI)
├── tests/               # Comprehensive test suite
├── docs/               # This documentation site
└── k8s/                # Production deployment
```

## Deployment Architecture

The system is designed for multiple deployment scenarios:

### 1. Local Development
```bash
python main.py analyze --file incident.txt
```

### 2. Docker Compose (Full Stack)
```bash
docker-compose up -d  # Includes API, DB, monitoring
```

### 3. Kubernetes (Production)
```bash
kubectl apply -f k8s/  # Auto-scaling, monitoring, backups
```

## Why This Architecture Works

1. **Testable**: Each component has single responsibility
2. **Reproducible**: Deterministic convergence, artifact replay
3. **Scalable**: Stateless agents, parallel execution
4. **Auditable**: Complete artifact trail, no hidden reasoning
5. **Maintainable**: Clear boundaries, minimal dependencies

## Next Evolution

The architecture supports:
- Adding new agent roles (pluggable system)
- Custom convergence logic (subclass engine)
- External evidence enrichment (MITRE ATT&CK)
- Different LLM providers (abstract interface)

---

**This architecture documents the system, not markets it.** The value is in the engineering choices, not the presentation.
