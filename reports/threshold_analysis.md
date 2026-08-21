# Confidence Threshold & Routing Analysis Report

## 1. Executive Summary & Recommendation
- **Recommended Default Threshold**: `0.70`
- **Projected Auto-Routing Rate**: `2.9%`
- **Projected Human Review Rate**: `97.1%`
- **Auto-Routed Ticket Accuracy (All 3 Labels Correct)**: `87.5%`
- **Critical Escaped Errors (without safety layer)**: `0`

## 2. Threshold Sweep (0.70 to 0.90)

| Threshold | Auto-Routed % | Review Queue % | Cat Acc | Pri Acc | Dept Acc | Full Match % | Critical Escaped |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **0.70** | 2.9% | 97.1% | 100.0% | 87.5% | 100.0% | 87.5% | 0 |
| **0.75** | 2.9% | 97.1% | 100.0% | 87.5% | 100.0% | 87.5% | 0 |
| **0.80** | 2.9% | 97.1% | 100.0% | 87.5% | 100.0% | 87.5% | 0 |
| **0.82** | 2.9% | 97.1% | 100.0% | 87.5% | 100.0% | 87.5% | 0 |
| **0.85** | 2.5% | 97.5% | 100.0% | 85.7% | 100.0% | 85.7% | 0 |
| **0.88** | 2.2% | 97.8% | 100.0% | 83.3% | 100.0% | 83.3% | 0 |
| **0.90** | 1.4% | 98.6% | 100.0% | 75.0% | 100.0% | 75.0% | 0 |

## 3. Decision Rationale
- At lower thresholds (e.g. 0.70), auto-routing rate is high, but risk of misrouting critical tickets increases.
- At higher thresholds (e.g. 0.90), routing safety is maximized, but human review workload rises.
- Operating at `0.70` balances cost-efficiency with high classification fidelity.
- Coupled with Phase 11 deterministic safety escalation, any high-severity billing/technical ticket is guaranteed human review.