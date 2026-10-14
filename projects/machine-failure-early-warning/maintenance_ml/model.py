"""Dependency-free L2 logistic regression implementation."""

from __future__ import annotations

import math


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-min(value, 700))
        return 1.0 / (1.0 + z)
    z = math.exp(max(value, -700))
    return z / (1.0 + z)


class Standardizer:
    def fit(self, rows: list[tuple[float, ...]]) -> "Standardizer":
        if not rows:
            raise ValueError("Cannot fit on empty data")
        width = len(rows[0])
        if any(len(row) != width for row in rows):
            raise ValueError("Feature rows must have equal width")
        self.means = [sum(row[j] for row in rows) / len(rows) for j in range(width)]
        self.scales = []
        for j, mean in enumerate(self.means):
            variance = sum((row[j] - mean) ** 2 for row in rows) / len(rows)
            self.scales.append(math.sqrt(variance) or 1.0)
        return self

    def transform(self, rows: list[tuple[float, ...]]) -> list[list[float]]:
        return [[(x - mean) / scale for x, mean, scale in zip(row, self.means, self.scales)]
                for row in rows]


class LogisticRegression:
    def __init__(self, learning_rate: float = 0.15, epochs: int = 1200, l2: float = 0.01):
        self.learning_rate, self.epochs, self.l2 = learning_rate, epochs, l2

    def fit(self, rows: list[list[float]], labels: list[int]) -> "LogisticRegression":
        if not rows or len(rows) != len(labels) or len(set(labels)) < 2:
            raise ValueError("Training requires aligned rows with both classes")
        self.weights = [0.0] * len(rows[0])
        self.bias = 0.0
        n = len(rows)
        for _ in range(self.epochs):
            grad = [0.0] * len(self.weights)
            bias_grad = 0.0
            for row, label in zip(rows, labels):
                error = sigmoid(sum(w * x for w, x in zip(self.weights, row)) + self.bias) - label
                for j, x in enumerate(row):
                    grad[j] += error * x
                bias_grad += error
            for j in range(len(grad)):
                grad[j] = grad[j] / n + self.l2 * self.weights[j]
                self.weights[j] -= self.learning_rate * grad[j]
            self.bias -= self.learning_rate * bias_grad / n
        return self

    def predict_proba(self, rows: list[list[float]]) -> list[float]:
        return [sigmoid(sum(w * x for w, x in zip(self.weights, row)) + self.bias) for row in rows]
