"""Binary classification metrics with explicit edge-case behavior."""

from __future__ import annotations


def confusion(labels: list[int], scores: list[float], threshold: float) -> dict[str, int]:
    tp = fp = tn = fn = 0
    for y, score in zip(labels, scores):
        pred = int(score >= threshold)
        if y and pred:
            tp += 1
        elif pred:
            fp += 1
        elif y:
            fn += 1
        else:
            tn += 1
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def classification_metrics(labels: list[int], scores: list[float], threshold: float) -> dict:
    if len(labels) != len(scores) or not labels:
        raise ValueError("Labels and scores must be non-empty and aligned")
    cm = confusion(labels, scores, threshold)
    precision = cm["tp"] / max(1, cm["tp"] + cm["fp"])
    recall = cm["tp"] / max(1, cm["tp"] + cm["fn"])
    f1 = 2 * precision * recall / max(1e-15, precision + recall)
    positives = sum(labels)
    negatives = len(labels) - positives
    ordered = sorted(zip(scores, labels), reverse=True)
    seen_pos = seen_neg = 0
    average_precision = 0.0
    previous_recall = 0.0
    index = 0
    while index < len(ordered):
        end = index
        while end < len(ordered) and ordered[end][0] == ordered[index][0]:
            end += 1
        group_pos = sum(label for _, label in ordered[index:end])
        group_neg = end - index - group_pos
        seen_pos += group_pos
        seen_neg += group_neg
        recall_at_cut = seen_pos / max(1, positives)
        average_precision += (recall_at_cut - previous_recall) * (seen_pos / (seen_pos + seen_neg))
        previous_recall = recall_at_cut
        index = end
    # Mann-Whitney rank-sum implementation of ROC-AUC, with half credit for ties.
    ascending = sorted(zip(scores, labels))
    positive_rank_sum = 0.0
    rank = 1
    index = 0
    while index < len(ascending):
        end = index
        while end < len(ascending) and ascending[end][0] == ascending[index][0]:
            end += 1
        average_rank = (rank + rank + (end - index) - 1) / 2
        positive_rank_sum += average_rank * sum(label for _, label in ascending[index:end])
        rank += end - index
        index = end
    roc_auc = ((positive_rank_sum - positives * (positives + 1) / 2) /
               max(1, positives * negatives))
    return {**cm, "precision": precision, "recall": recall, "f1": f1,
            "pr_auc": average_precision,
            "roc_auc": roc_auc,
            "alert_rate": sum(score >= threshold for score in scores) / len(scores)}


def best_f1_threshold(labels: list[int], scores: list[float]) -> float:
    if len(labels) != len(scores) or not labels:
        raise ValueError("Labels and scores must be non-empty and aligned")
    ordered = sorted(zip(scores, labels), reverse=True)
    tp = fp = 0
    best_threshold, best_f1 = 1.0, -1.0
    index = 0
    while index < len(ordered):
        end = index
        while end < len(ordered) and ordered[end][0] == ordered[index][0]:
            end += 1
        group_pos = sum(label for _, label in ordered[index:end])
        tp += group_pos
        fp += end - index - group_pos
        precision = tp / (tp + fp)
        recall = tp / max(1, sum(labels))
        f1 = 2 * precision * recall / max(1e-15, precision + recall)
        threshold = ordered[index][0]
        if f1 > best_f1 or (f1 == best_f1 and threshold < best_threshold):
            best_f1, best_threshold = f1, threshold
        index = end
    return best_threshold
