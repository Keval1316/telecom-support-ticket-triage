"""
Phase 10 - Confidence Estimation & Calibration Utilities.
Calculates token probability confidence, entropy-based uncertainty,
and provides confidence estimation utilities for local inference.
"""
from typing import List, Tuple
import numpy as np
import torch


def calculate_token_confidence(scores: List[torch.Tensor], generated_token_ids: torch.Tensor) -> Tuple[float, float]:
    """
    Computes confidence metrics from generation logits/scores.
    Returns:
        (avg_token_prob, min_token_prob):
        - avg_token_prob: Mean of top-1 token probabilities across generated sequence.
        - min_token_prob: Minimum probability observed in generated sequence (bottleneck indicator).
    """
    if not scores or len(scores) == 0:
        return 1.0, 1.0

    probs = []
    for i, score_tensor in enumerate(scores):
        if i >= len(generated_token_ids):
            break
        # Softmax over vocabulary logits
        prob_dist = torch.softmax(score_tensor[0], dim=-1)
        token_id = generated_token_ids[i].item()
        token_prob = prob_dist[token_id].item()
        probs.append(token_prob)

    if not probs:
        return 1.0, 1.0

    avg_prob = float(np.mean(probs))
    min_prob = float(np.min(probs))
    return avg_prob, min_prob


def calibrate_confidence(avg_prob: float, min_prob: float, is_valid_json: bool) -> float:
    """
    Harmonizes probability metrics into a single calibrated confidence score in [0.0, 1.0].
    If JSON structure failed to parse, drops confidence to 0.0.
    Combines average token probability with penalization if min token probability was low.
    """
    if not is_valid_json:
        return 0.0

    # Weighted blend: 75% average token confidence + 25% lowest token confidence
    score = (0.75 * avg_prob) + (0.25 * min_prob)
    return round(float(np.clip(score, 0.0, 1.0)), 4)
