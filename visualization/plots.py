# src/visualization/plots.py
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import List, Dict, Any
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

class VisualizationEngine:
    """Visualize agent disagreement and convergence dynamics"""
    
    def __init__(self):
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
    
    def plot_disagreement_dynamics(self, results: List[Dict], output_path: Path = None):
        """Plot disagreement metrics over incidents"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Residual Disagreement Distribution', 
                          'Evidence Overlap vs Confidence',
                          'Decision Confidence Distribution',
                          'Processing Time by Outcome'),
            specs=[[{'type': 'histogram'}, {'type': 'scatter'}],
                   [{'type': 'box'}, {'type': 'bar'}]]
        )
        
        # Extract data
        residual_disagreements = [r['summary']['residual_disagreement'] for r in results]
        confidences = [r['decision']['confidence'] for r in results]
        evidence_overlaps = [np.mean(list(r['summary']['evidence_overlap'].values())) 
                           for r in results]
        labels = [r['decision']['label'] for r in results]
        processing_times = [r.get('processing_time', 0) for r in results]
        
        # Plot 1: Residual Disagreement Distribution
        fig.add_trace(
            go.Histogram(x=residual_disagreements, name='Residual Disagreement',
                        nbinsx=20, marker_color='coral'),
            row=1, col=1
        )
        
        # Plot 2: Evidence Overlap vs Confidence
        fig.add_trace(
            go.Scatter(x=evidence_overlaps, y=confidences, mode='markers',
                      marker=dict(size=8, color=residual_disagreements,
                                 colorscale='Viridis', showscale=True,
                                 colorbar=dict(title="Residual<br>Disagreement")),
                      name='Incidents'),
            row=1, col=2
        )
        
        # Plot 3: Decision Confidence Distribution
        for label in set(labels):
            label_confidences = [c for c, l in zip(confidences, labels) if l == label]
            fig.add_trace(
                go.Box(y=label_confidences, name=label, boxpoints='outliers'),
                row=2, col=1
            )
        
        # Plot 4: Processing Time by Outcome
        label_processing = {}
        for label in set(labels):
            times = [t for t, l in zip(processing_times, labels) if l == label]
            label_processing[label] = np.mean(times) if times else 0
        
        fig.add_trace(
            go.Bar(x=list(label_processing.keys()), 
                  y=list(label_processing.values()),
                  name='Avg Processing Time',
                  marker_color='lightseagreen'),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title_text="Multi-Agent Analysis Dynamics",
            height=800,
            showlegend=False
        )
        
        fig.update_xaxes(title_text="Residual Disagreement", row=1, col=1)
        fig.update_yaxes(title_text="Count", row=1, col=1)
        fig.update_xaxes(title_text="Evidence Overlap", row=1, col=2)
        fig.update_yaxes(title_text="Confidence", row=1, col=2)
        fig.update_xaxes(title_text="Label", row=2, col=1)
        fig.update_yaxes(title_text="Confidence", row=2, col=1)
        fig.update_xaxes(title_text="Label", row=2, col=2)
        fig.update_yaxes(title_text="Seconds", row=2, col=2)
        
        if output_path:
            fig.write_html(str(output_path))
        
        return fig
    
    def plot_agent_agreement_matrix(self, results: List[Dict], output_path: Path = None):
        """Plot agreement matrix between agents"""
        agent_labels = {'benign': [], 'malicious': [], 'skeptic': []}
        
        for result in results:
            for agent, info in result['summary']['agent_labels'].items():
                agent_labels[agent].append(info['label'])
        
        # Calculate agreement matrix
        agents = list(agent_labels.keys())
        agreement_matrix = np.zeros((len(agents), len(agents)))
        
        for i, agent1 in enumerate(agents):
            for j, agent2 in enumerate(agents):
                if i == j:
                    agreement_matrix[i, j] = 1.0
                else:
                    matches = sum(1 for l1, l2 in zip(agent_labels[agent1], agent_labels[agent2]) 
                                if l1 == l2)
                    agreement_matrix[i, j] = matches / len(agent_labels[agent1])
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(agreement_matrix, cmap='YlOrRd', vmin=0, vmax=1)
        
        # Add labels
        ax.set_xticks(np.arange(len(agents)))
        ax.set_yticks(np.arange(len(agents)))
        ax.set_xticklabels(agents)
        ax.set_yticklabels(agents)
        
        # Add text annotations
        for i in range(len(agents)):
            for j in range(len(agents)):
                text = ax.text(j, i, f"{agreement_matrix[i, j]:.2f}",
                              ha="center", va="center", color="black")
        
        ax.set_title("Agent Label Agreement Matrix")
        plt.colorbar(im, ax=ax, label="Agreement Rate")
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def plot_epistemic_uncertainty_breakdown(self, results: List[Dict], output_path: Path = None):
        """Visualize reasons for epistemic uncertainty"""
        uncertain_results = [r for r in results if r['decision']['label'] == 'UNCERTAIN']
        
        if not uncertain_results:
            print("No uncertain results to visualize")
            return None
        
        reason_counts = {}
        for result in uncertain_results:
            for reason in result['decision']['reason_codes']:
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Pie chart of uncertainty reasons
        ax1.pie(reason_counts.values(), labels=reason_counts.keys(), autopct='%1.1f%%')
        ax1.set_title("Reasons for Epistemic Uncertainty")
        
        # Box plot of residual disagreement by reason
        reason_disagreements = {}
        for result in uncertain_results:
            for reason in result['decision']['reason_codes']:
                if reason not in reason_disagreements:
                    reason_disagreements[reason] = []
                reason_disagreements[reason].append(result['summary']['residual_disagreement'])
        
        data = [reason_disagreements[reason] for reason in reason_counts.keys()]
        ax2.boxplot(data, labels=reason_counts.keys())
        ax2.set_title("Residual Disagreement by Uncertainty Reason")
        ax2.set_ylabel("Residual Disagreement")
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
        
        return fig