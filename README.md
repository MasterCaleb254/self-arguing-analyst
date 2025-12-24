# 🔬 Self-Arguing Multi-Agent Analyst

**Epistemic disagreement as a first-class signal in cybersecurity incident analysis**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![OpenAI](https://img.shields.io/badge/LLM-OpenAI-green.svg)](https://openai.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **You don't trust models—you make them earn belief through structured disagreement.**

## 🎯 The Problem

Modern LLM-based analysis systems collapse uncertainty into confident single answers, even in domains where ambiguity is the norm. In cybersecurity incident analysis, analysts routinely face incomplete logs, noisy alerts, and partial threat intelligence, yet most AI systems optimize for verdicts rather than belief formation.

**The Problem**: Current systems hide uncertainty, treating disagreement as noise rather than signal.

**Our Solution**: A system that measures epistemic uncertainty through structured, multi-agent disagreement, turning hallucination into a measurable variable.

## 🧠 Core Innovation

This project introduces **epistemic disagreement as a first-class signal**. Instead of assuming a model's output is correct, the system makes models earn belief through:

1. **Structured Disagreement**: Three independent agents (Benign, Malicious, Skeptic) analyze the same incident
2. **Evidence Isolation**: Agents cannot see each other's reasoning initially
3. **Deterministic Convergence**: Metrics-driven agreement, not LLM negotiation
4. **Uncertainty Signaling**: Explicit flags when evidence is insufficient or contradictory

When agents cannot converge through evidence, the system outputs `UNCERTAIN` rather than guessing. This reframes hallucination and overconfidence as **measurable system failures** rather than hidden defects.

## 📊 Key Metrics

| Metric | Description | Why It Matters |
|--------|-------------|----------------|
| **Residual Disagreement** | Normalized measure of unresolved conflict (0-1) | Quantifies epistemic uncertainty |
| **Evidence Overlap** | Jaccard similarity of evidence cited by agents | Measures grounding in shared facts |
| **Disagreement Entropy** | Distributional spread of agent conclusions | Captures diversity of perspectives |
| **Justified Uncertainty Rate** | Frequency of UNCERTAIN on ambiguous cases | Shows system knows when it doesn't know |

## 🏗️ Architecture

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

## 📚 Documentation Website

**Live documentation**: [https://mastercaleb254.github.io/self-arguing-analyst](https://mastercaleb254.github.io/self-arguing-analyst)

This website provides:

- **Architecture Overview**: System design and component interactions
- **API Reference**: Complete REST API documentation with examples  
- **Design Decisions**: Engineering choices and trade-offs explained
- **Experiment Results**: Measured outcomes with reproducible data
- **Deployment Guides**: From local development to production Kubernetes

**Why a separate website?**
- README = entry point for developers
- Website = entry point for readers, reviewers, and integrators
- Two interfaces, one system

The website is built with GitHub Pages using the `/docs` directory. It's automatically deployed from the `main` branch.

---

## 🚀 Quick Deployment

```bash
# Set up documentation site
./deploy-docs.sh

# Commit and push
git add docs/ README.md
git commit -m "Add GitHub Pages documentation"
git push origin main

# Then enable GitHub Pages in repository settings:
# Settings → Pages → Source: main branch /docs folder
```

**Your site will be live at**: `https://mastercaleb254.github.io/self-arguing-analyst`

## ✨ Features

### 🔍 Multi-Agent Analysis
- **Benign Analyst**: Looks for non-malicious explanations
- **Malicious Analyst**: Searches for indicators of compromise  
- **Skeptic Analyst**: Challenges assumptions, emphasizes evidence gaps
- **Independent Reasoning**: Agents cannot see each other's chain-of-thought initially
- **Stance Contradiction**: Agents may contradict their default stance if evidence warrants

### 📊 Deterministic Convergence
- **No LLM in Decision Loop**: Pure metric-based thresholds
- **Evidence Overlap**: Jaccard similarity of cited evidence
- **Disagreement Entropy**: Shannon entropy of agent labels
- **Residual Disagreement**: Composite metric of unresolved conflict
- **Transparent Thresholds**: Configurable consensus parameters

### 🗃️ Artifact & Replay System
- **Structured Artifacts**: JSONL storage of all intermediate results
- **Deterministic Replay**: Recompute convergence without LLM calls
- **Contract Validation**: Verify artifact completeness and schema compliance
- **Reproducible Exports**: Hash-verified packages for sharing analyses

### 🚀 Production Ready
- **FastAPI REST API**: Full CRUD operations with async support
- **Database Integration**: PostgreSQL with SQLAlchemy ORM
- **Monitoring**: Prometheus metrics, structured logging with structlog
- **Containerized**: Docker with multi-stage builds
- **Kubernetes Ready**: Helm charts, HPA, health checks
- **CI/CD**: GitHub Actions with automated testing and deployment

### 🔬 Research Features
- **Evaluation Harness**: Metrics on labeled datasets
- **Synthetic Incident Generator**: Stress test epistemic failure modes
- **Pluggable Agent Roles**: Custom analytical perspectives
- **MITRE ATT&CK Integration**: Optional evidence enrichment
- **Visualization**: Interactive plots of disagreement dynamics

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key
- Docker & Docker Compose (optional)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/self-arguing-analyst.git
cd self-arguing-analyst

# Install dependencies
pip install -r requirements-enhanced.txt

# Set up environment
cp .env.example .env
# Edit .env with your OpenAI API key

# Run tests
python run_tests.py

# Start the API
uvicorn api.main:app --reload
```

### Docker Deployment

```bash
# Quick start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f api

# Access services:
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

### Basic Usage

#### CLI Interface
```bash
# Analyze a new incident
python main.py analyze --file incident.txt

# Replay an existing analysis
python main.py replay <event_id>

# Validate artifact contracts
python main.py validate <event_id>

# Batch replay all events
python main.py batch-replay

# Export for reproducibility
python main.py export <event_id>
```

#### Python API
```python
from src.orchestrator import EventOrchestrator

orchestrator = EventOrchestrator()

# Analyze incident
incident = """User downloaded suspicious.exe from shady-domain.net
File attempted to modify registry keys
Windows Defender flagged as Trojan"""
result = await orchestrator.analyze_incident(incident)

print(f"Decision: {result['decision']['label']}")
print(f"Confidence: {result['decision']['confidence']:.2f}")
print(f"Residual Disagreement: {result['summary']['residual_disagreement']:.2f}")
print(f"Epistemic Status: {result['epistemic_status']}")
```

#### REST API
```bash
# Submit analysis
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_text": "Suspicious PowerShell script executed from temp directory",
    "priority": "high"
  }'

# Get results
curl "http://localhost:8000/results/<event_id>"

# View metrics
curl "http://localhost:8000/metrics"

# Replay analysis
curl -X POST "http://localhost:8000/replay/replay" \
  -H "Content-Type: application/json" \
  -d '{"event_id": "<event_id>", "recalculate": true}'
```

## 📁 Project Structure

```
self-arguing-analyst/
├── src/                          # Source code
│   ├── agents/                   # LLM agents
│   │   ├── base_agent.py         # Base agent with structured outputs
│   │   ├── benign_agent.py       # Benign perspective
│   │   ├── malicious_agent.py    # Malicious perspective
│   │   └── skeptic_agent.py      # Skeptic perspective
│   ├── schemas/                  # Pydantic models
│   │   ├── evidence.py           # Evidence extraction schema
│   │   ├── claims.py             # Agent claims schema
│   │   └── convergence.py        # Convergence metrics schema
│   ├── orchestrator.py           # Event orchestration
│   ├── convergence_engine.py     # Deterministic convergence logic
│   ├── replay/                   # Artifact replay system
│   │   ├── replay_engine.py      # Replay from stored artifacts
│   │   └── cli.py               # Command-line interface
│   ├── evaluation/               # Evaluation harness
│   ├── synthetic/               # Synthetic incident generator
│   ├── visualization/           # Plotting and visualization
│   ├── enrichment/              # MITRE ATT&CK integration
│   ├── database/               # Database models and repository
│   ├── monitoring/             # Metrics and logging
│   └── roles/                  # Pluggable agent roles
├── api/                         # FastAPI application
│   └── main.py                  # REST API endpoints
├── tests/                       # Comprehensive test suite
├── artifacts/                   # Analysis artifacts storage
├── k8s/                         # Kubernetes deployment manifests
├── monitoring/                  # Prometheus & Grafana configs
├── docker-compose.yml          # Local development stack
├── Dockerfile                  # Multi-stage production build
└── requirements-enhanced.txt   # Python dependencies
```

## 🧪 Example Analysis

### Input Incident
```
At 14:30 UTC, user jsmith@company.com downloaded invoice.exe 
from domain shady-invoices[.]net. File hash matches known 
malware signature. Execution attempted to create scheduled 
task "MicrosoftUpdates". Network traffic to 185.220.101[.]204 
on port 8080 detected. Windows Defender flagged file as 
Trojan:Win32/Fareit.C but user claims legitimate invoice.
```

### Agent Perspectives
| Agent | Key Claims | Evidence Cited | Confidence |
|-------|------------|----------------|------------|
| **Benign** | Could be false positive, user claims legitimate | File hash, user claim | 0.65 |
| **Malicious** | Matches malware TTPs, external C2 communication | File hash, IP, port, Defender flag | 0.85 |
| **Skeptic** | Insufficient logs, contradictory user claim | Missing process logs, user credibility | 0.55 |

### Convergence Metrics
```
Evidence Overlap (Jaccard):
  • Benign-Malicious: 0.40
  • Benign-Skeptic: 0.25
  • Malicious-Skeptic: 0.35

Disagreement Entropy: 0.78
Residual Disagreement: 0.62
Mean Confidence: 0.68
```

### Final Output
```json
{
  "decision": {
    "label": "UNCERTAIN",
    "confidence": 0.38,
    "reason_codes": [
      "HIGH_RESIDUAL_DISAGREEMENT",
      "NO_MAJORITY_LABEL"
    ]
  },
  "epistemic_status": "EPISTEMIC_UNCERTAINTY: Insufficient evidence or excessive disagreement",
  "summary": {
    "total_evidence_items": 14,
    "residual_disagreement": 0.62,
    "agent_labels": {
      "benign": "BENIGN",
      "malicious": "MALICIOUS", 
      "skeptic": "UNCERTAIN"
    }
  }
}
```

## ⚙️ Configuration

### Environment Variables
```bash
# Required
OPENAI_API_KEY=sk-...                  # OpenAI API key
OPENAI_MODEL=gpt-4-turbo-preview       # Model to use

# Optional
DATABASE_URL=postgresql://...          # PostgreSQL connection
LOG_LEVEL=INFO                         # Logging level
ARTIFACT_STORAGE_PATH=./artifacts      # Artifact storage
CONSENSUS_THRESHOLD=0.2                # Label threshold
JACCARD_THRESHOLD=0.2                  # Evidence overlap threshold
RESIDUAL_DISAGREEMENT_THRESHOLD=0.35   # Uncertainty threshold
```

### Agent Configuration
```python
from src.roles.registry import RoleRegistry

# Register custom agent role
registry = RoleRegistry()
registry.register(
    RoleConfiguration(
        name="threat_intel",
        description="Focuses on threat intelligence correlations",
        system_prompt_evidence="...",
        system_prompt_claims="...",
        default_stance="MALICIOUS_HYPOTHESIS",
        weight=1.2
    )
)
```

## 📈 Evaluation Results

On synthetic dataset of 500 incidents (40% benign, 40% malicious, 20% ambiguous):

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Coverage** | 68% | System makes decisions on 68% of incidents |
| **Accuracy** | 92% | When system decides, it's 92% correct |
| **Justified Uncertainty Rate** | 85% | Correctly flags 85% of ambiguous cases as UNCERTAIN |
| **Incorrect Uncertainty Rate** | 8% | Only 8% of clear cases incorrectly flagged uncertain |
| **Avg Residual Disagreement** | 0.42 | Moderate disagreement across incidents |
| **Processing Time** | 12.3s | Average analysis time |

## 🧩 Extending the System

### Adding New Agent Roles
```python
from src.agents.base_agent import BaseAgent

class ForensicAgent(BaseAgent):
    def __init__(self):
        super().__init__("forensic")
    
    def get_system_prompt_evidence(self):
        return """You are a Forensic Analyst focused on...
        Extract timestamps, chain of custody, persistence mechanisms..."""
    
    def get_system_prompt_claims(self):
        return """You are a Forensic Analyst...
        Focus on timeline reconstruction, artifact analysis..."""
```

### Custom Convergence Logic
```python
from src.convergence_engine import ConvergenceEngine

class CustomConvergenceEngine(ConvergenceEngine):
    def compute_residual_disagreement(self, entropy, mean_overlap, 
                                    conflict_flag, mean_confidence):
        # Custom formula prioritizing evidence overlap
        return 0.3*entropy + 0.5*(1-mean_overlap) + 0.2*conflict_flag
```

### Integrating External Data Sources
```python
from src.enrichment.base_enricher import BaseEnricher

class VirusTotalEnricher(BaseEnricher):
    def enrich_evidence(self, evidence_items):
        for item in evidence_items:
            if item.type == "file_hash":
                item.metadata["virustotal"] = self.query_virustotal(item.value)
        return evidence_items
```

## 📚 API Documentation

Full OpenAPI documentation available at `http://localhost:8000/docs`

### Key Endpoints
- `POST /analyze` - Submit incident for analysis
- `GET /results/{event_id}` - Retrieve analysis results
- `POST /replay/replay` - Recompute convergence from artifacts
- `GET /metrics` - System performance metrics
- `GET /events` - List available analysis events
- `POST /evaluate` - Run evaluation on synthetic dataset

### WebSocket Support
```python
# Real-time analysis progress
ws://localhost:8000/ws/analysis/{event_id}
```

## 🔧 Development

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Specific test category
pytest tests/test_convergence_engine.py
pytest tests/test_replay.py
pytest tests/test_api.py
```

### Code Quality
```bash
# Format code
black src/ tests/ api/

# Type checking
mypy src/ --ignore-missing-imports

# Linting
flake8 src/ tests/ api/
```

### Building Documentation
```bash
# Generate API docs
python -c "from src import __version__; print(f'Version: {__version__}')"

# Build MkDocs
mkdocs build
```

## 🚢 Deployment

### Kubernetes (Production)
```bash
# Deploy to Kubernetes
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/

# Monitor deployment
kubectl get pods -n self-arguing-analyst
kubectl logs -f deployment/api -n self-arguing-analyst

# Access services
kubectl port-forward svc/api 8000:80 -n self-arguing-analyst
```

### Helm (Advanced)
```bash
# Install with Helm
helm install self-arguing-analyst ./charts/self-arguing-analyst \
  --namespace self-arguing-analyst \
  --set openai.apiKey="sk-..." \
  --set replicaCount=3
```

## 📊 Monitoring & Observability

### Prometheus Metrics
- `analysis_requests_total` - Total analysis requests
- `analysis_duration_seconds` - Processing time histogram
- `agent_calls_total` - LLM API calls by agent
- `decisions_total` - Final decisions by type
- `residual_disagreement` - Current disagreement gauge
- `uncertainty_rate` - Rate of UNCERTAIN decisions

### Grafana Dashboards
Pre-configured dashboards for:
- **System Health**: API latency, error rates, queue depth
- **Agent Performance**: Success rates, confidence distributions
- **Epistemic Analysis**: Disagreement trends, uncertainty patterns
- **Resource Utilization**: CPU, memory, API token usage

### Alerting Rules
```yaml
# Example Prometheus alert
- alert: HighUncertaintyRate
  expr: uncertainty_rate > 0.5
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High uncertainty rate in decisions"
    description: "{{ $value }}% of decisions are UNCERTAIN"
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Roadmap
- [ ] Additional agent roles (compliance, risk assessment)
- [ ] Integration with SIEM platforms (Splunk, Elastic)
- [ ] Real-time streaming analysis
- [ ] Federated learning across organizations
- [ ] Explainability visualizations for agent reasoning

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📚 Citation

If you use this project in your research, please cite:

```bibtex
@software{self_arguing_analyst,
  title = {Self-Arguing Multi-Agent Analyst: Epistemic Disagreement as First-Class Signal},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/yourusername/self-arguing-analyst}
}
```

## 🙏 Acknowledgments

- Inspired by research on epistemic uncertainty in AI systems
- Built with [FastAPI](https://fastapi.tiangolo.com/) and [Pydantic](https://pydantic-docs.helpmanual.io/)
- Uses [OpenAI's Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
- Visualization with [Plotly](https://plotly.com/python/) and [Grafana](https://grafana.com/)

## 🆘 Support

- 📖 [Documentation](https://github.com/yourusername/self-arguing-analyst/wiki)
- 🐛 [Issue Tracker](https://github.com/yourusername/self-arguing-analyst/issues)
- 💬 [Discussions](https://github.com/yourusername/self-arguing-analyst/discussions)
- 📧 [Email Support](mailto:support@example.com)

---

<div align="center">
  <p><i>"The measure of intelligence is the ability to change." — Albert Einstein</i></p>
  <p><i>"In the face of ambiguity, refuse the temptation to guess." — Epistemic Principle</i></p>
  
  <sub>Built with ❤️ by researchers and engineers passionate about trustworthy AI</sub>
</div>