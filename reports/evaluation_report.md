# Model Evaluation Report — Fine-Tuned Qwen2.5-3B

## 1. Executive Summary
- **Test Set Size**: 276 tickets
- **Valid JSON Output Rate**: 3.3% (9/276)
- **Average Model Confidence**: 0.905

| Task | Accuracy | Macro Precision | Macro Recall | Macro F1 |
| :--- | :--- | :--- | :--- | :--- |
| **Category** | 15.58% | 42.80% | 21.36% | 7.55% |
| **Priority** | 37.32% | 52.88% | 26.10% | 15.93% |
| **Department** | 12.32% | 42.14% | 21.29% | 6.36% |

## 2. Priority & Safety Critical Analysis
- **Total True Critical Tickets**: 28
- **Critical Priority Recall**: 0.00%
- **Critical Tickets Underestimated (Predicted as Low/Medium)**: 28
  > [!WARNING]
  > 28 critical ticket(s) were predicted as Low/Medium. These MUST be caught by the Phase 11 deterministic safety escalation layer.

## 3. Per-Class Performance Breakdown

### Category Breakdown
| Class | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
| Billing | 100.0% | 2.9% | 5.6% | 69.0 |
| Technical | 100.0% | 3.9% | 7.5% | 77.0 |
| Account | 0.0% | 0.0% | 0.0% | 51.0 |
| Refund | 0.0% | 0.0% | 0.0% | 41.0 |
| General | 14.0% | 100.0% | 24.6% | 38.0 |

### Priority Breakdown
| Class | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
| Critical | 0.0% | 0.0% | 0.0% | 28.0 |
| High | 100.0% | 1.4% | 2.7% | 74.0 |
| Medium | 36.5% | 99.0% | 53.4% | 100.0 |
| Low | 75.0% | 4.1% | 7.7% | 74.0 |

### Department Breakdown
| Class | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
| Finance | 100.0% | 2.8% | 5.5% | 71.0 |
| Technical | 100.0% | 3.6% | 7.0% | 83.0 |
| Account | 0.0% | 0.0% | 0.0% | 48.0 |
| Refunds | 0.0% | 0.0% | 0.0% | 45.0 |
| General Support | 10.7% | 100.0% | 19.3% | 29.0 |
