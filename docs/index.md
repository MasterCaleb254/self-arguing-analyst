---
layout: default
title: Self-Arguing Multi-Agent Analyst
---

# Self-Arguing Multi-Agent Analyst

**Epistemic disagreement as a first-class signal in cybersecurity incident analysis**

> **You don't trust models—you make them earn belief through structured disagreement.**

## The Problem

Modern LLM-based analysis systems collapse uncertainty into confident single answers, even in domains where ambiguity is the norm. In cybersecurity incident analysis, analysts routinely face incomplete logs, noisy alerts, and partial threat intelligence, yet most AI systems optimize for verdicts rather than belief formation.

**Current systems hide uncertainty**, treating disagreement as noise rather than signal.

**Our solution**: A system that **measures epistemic uncertainty** through structured, multi-agent disagreement, turning hallucination into a measurable variable.

## Core Innovation

This project introduces **epistemic disagreement as a first-class signal**. Instead of assuming a model's output is correct, the system makes models earn belief through:

1. **Structured Disagreement**: Three independent agents (Benign, Malicious, Skeptic) analyze the same incident
2. **Evidence Isolation**: Agents cannot see each other's reasoning initially
3. **Deterministic Convergence**: Metrics-driven agreement, not LLM negotiation
4. **Uncertainty Signaling**: Explicit flags when evidence is insufficient or contradictory

When agents cannot converge through evidence, the system outputs `UNCERTAIN` rather than guessing. This reframes hallucination and overconfidence as **measurable system failures** rather than hidden defects.

## Quick Start

```bash
# Install and run
pip install -r requirements-enhanced.txt
python main.py analyze --file incident.txt

# Or use Docker
docker-compose up -d
```

**Live demo available at**: [api.self-arguing-analyst.com](https://api.self-arguing-analyst.com)

## System Status

| Component | Status | Notes |
|-----------|--------|-------|
| **Core Engine** | ✅ Production Ready | Deterministic, reproducible |
| **API Layer** | ✅ Deployed | FastAPI with async support |
| **Database** | ✅ PostgreSQL | All artifacts stored |
| **Monitoring** | ✅ Prometheus/Grafana | Real-time metrics |
| **Documentation** | 🔄 In Progress | This site |

## Navigation

- [Architecture](architecture.html) - System design and components
- [API Reference](api.html) - REST endpoints and usage
- [Design Decisions](decisions.html) - Why we built it this way
- [Experiments](experiments.html) - Results and validation

## Repository

All source code, tests, and deployment configurations are available in the [GitHub repository](https://github.com/mastercaleb254/self-arguing-analyst).

**Key directories**:
- `/src` - Core Python implementation
- `/api` - REST API with FastAPI
- `/tests` - Comprehensive test suite
- `/k8s` - Kubernetes deployment manifests
- `/monitoring` - Prometheus & Grafana configs

## License

MIT License - see [LICENSE](https://github.com/mastercaleb254/self-arguing-analyst/blob/main/LICENSE)

---

**This is not a blog platform. It's documentation-as-a-site.** The code remains the engine; this page becomes the dashboard.
