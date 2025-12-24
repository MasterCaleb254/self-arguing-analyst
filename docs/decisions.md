---
layout: default
title: Design Decisions
---

# Design Decisions

Explicit engineering choices that shape the system. Each decision has a reason and a consequence.

## Core Philosophy Decisions

### 1. **Epistemic Uncertainty as Signal**
**Decision**: Treat disagreement as measurable output, not error state
**Reason**: In cybersecurity, knowing when you don't know is more valuable than guessing
**Consequence**: System outputs `UNCERTAIN` when evidence is insufficient
**Alternative Considered**: Forced consensus (common in LLM systems)

### 2. **No LLM in Convergence Loop**
**Decision**: Use deterministic metrics, not LLM negotiation
**Reason**: Ensures reproducibility and avoids hidden reasoning
**Consequence**: Convergence engine is pure Python, fully testable
**Alternative Considered**: LLM-as-judge (breaks determinism)

### 3. **Evidence Isolation**
**Decision**: Agents cannot see each other's reasoning initially
**Reason**: Preserves epistemic independence, prevents groupthink
**Consequence**: Parallel execution with no shared context
**Alternative Considered**: Sequential or collaborative analysis

## Technical Implementation Decisions

### 4. **Structured Outputs Over Free Text**
**Decision**: Enforce JSON schema with strict mode
**Reason**: Machine-parseable artifacts enable replay and validation
**Consequence**: All agent outputs validated against Pydantic models
**Alternative Considered**: Free-text responses with regex parsing

### 5. **Artifact Persistence as First-Class Feature**
**Decision**: Store all intermediate results as JSONL
**Reason**: Enables audit trails, replay, and research analysis
**Consequence**: Storage requirements increase but reproducibility guaranteed
**Alternative Considered**: Transient results (common in chat applications)

### 6. **Deterministic Replay System**
**Decision**: Build replay engine that recomputes from artifacts
**Reason**: Proves convergence is LLM-free and reproducible
**Consequence**: Can verify any analysis result without original LLM calls
**Alternative Considered**: Trust-based system (no verification)

## Architecture Decisions

### 7. **Three-Agent Minimum**
**Decision**: Require at least three distinct perspectives
**Reason**: Two agents can disagree; three reveals ambiguity
**Consequence**: System complexity increases but signal quality improves
**Alternative Considered**: Single agent or two-agent debate

### 8. **Pluggable Agent Roles**
**Decision**: Make agent roles configurable and extensible
**Reason**: Different domains need different analytical perspectives
**Consequence**: Can add forensic, compliance, threat-intel agents
**Alternative Considered**: Hard-coded roles (simpler but rigid)

### 9. **Metrics-Driven Thresholds**
**Decision**: Use configurable thresholds for consensus
**Reason**: Different use cases need different certainty levels
**Consequence**: Thresholds are tunable parameters
**Alternative Considered**: Fixed thresholds (simpler but less flexible)

## Interface Decisions

### 10. **CLI-First, Web-Second**
**Decision**: Build command-line interface before web UI
**Reason**: Engineers and researchers work in terminals
**Consequence**: System is scriptable from day one
**Alternative Considered**: Web UI first (more user-friendly initially)

### 11. **Structured API Over Chat Interface**
**Decision**: REST API with strict schemas, not chat completion
**Reason**: Enables integration with existing security tools
**Consequence**: API is predictable but less conversational
**Alternative Considered**: ChatGPT-like interface (more natural but less structured)

### 12. **OpenAPI Specification from Start**
**Decision**: Generate OpenAPI spec from code
**Reason**: Auto-generated documentation stays in sync
**Consequence**: API docs are always current
**Alternative Considered**: Manual documentation (prone to drift)

## Operational Decisions

### 13. **Docker-Compose for Local Development**
**Decision**: Provide complete local stack with one command
**Reason**: Researchers need full environment easily
**Consequence**: `docker-compose up` gives API, DB, monitoring
**Alternative Considered**: Manual setup instructions

### 14. **Prometheus Metrics by Default**
**Decision**: Instrument everything, expose metrics endpoint
**Reason**: Need to measure system behavior in production
**Consequence**: Can monitor disagreement patterns over time
**Alternative Considered**: Basic logging only

### 15. **Kubernetes Manifests in Repository**
**Decision**: Include production deployment configs
**Reason**: Show how to deploy, not just how to develop
**Consequence**: Repository contains complete lifecycle configs
**Alternative Considered**: Separate deployment repository

## Trade-Offs Acknowledged

### Complexity vs. Simplicity
**We chose complexity** in the service of transparency. A simpler system would hide more.

### Speed vs. Thoroughness
**We chose thoroughness**. Parallel agent analysis takes longer but provides better signals.

### Flexibility vs. Consistency
**We chose consistency** in the core, **flexibility** in the edges. Convergence is deterministic; agents are pluggable.

### Developer Experience vs. End-User Experience
**We prioritized developers** (security engineers, researchers) over casual users. The system is built to be integrated.

## Decisions Rejected (and Why)

### 1. **LLM-as-Arbiter**
**Rejected**: Would hide reasoning in black box
**Chosen**: Deterministic metrics anyone can audit

### 2. **Single Confidence Score**
**Rejected**: Collapses uncertainty
**Chosen**: Multiple metrics (residual disagreement, entropy, overlap)

### 3. **Transient Results**
**Rejected**: No audit trail
**Chosen**: Complete artifact persistence

### 4. **Fixed Thresholds**
**Rejected**: Not adaptable to different risk profiles
**Chosen**: Configurable thresholds

### 5. **Closed System**
**Rejected**: Cannot extend or modify
**Chosen**: Open source with pluggable architecture

## Evolution of Decisions

The system has evolved through these decision points:

1. **v0.1**: Proof of concept with hard-coded prompts
2. **v0.5**: Added structured outputs and basic replay
3. **v1.0**: Deterministic convergence and artifact contracts
4. **v1.5**: Production deployment with monitoring
5. **Current**: Pluggable agents and MITRE integration

Each version added complexity only when necessary to solve a specific problem.

## Principles Over Rules

These decisions follow core principles:

1. **Transparency over magic**
2. **Reproducibility over speed**
3. **Measurement over intuition**
4. **Extensibility over perfection**
5. **Engineering over marketing**

The system is built to be understood, not just used.

---

**These decisions document the engineering, not justify it.** The code is the proof; this page is the explanation.
