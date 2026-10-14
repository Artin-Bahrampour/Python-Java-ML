"""Deterministic synthetic telemetry benchmark."""

from __future__ import annotations

import random
from dataclasses import dataclass

FEATURES = ("vibration", "temperature", "pressure", "current", "vibration_trend")


@dataclass(frozen=True)
class Snapshot:
    machine_id: str
    hour: int
    values: tuple[float, ...]
    label: int


def generate_dataset(seed: int = 42, machines: int = 120, hours: int = 120) -> list[Snapshot]:
    """Generate telemetry snapshots labeled positive within 12 hours of failure."""
    if machines < 10 or hours < 30:
        raise ValueError("Use at least 10 machines and 30 hours")
    rng = random.Random(seed)
    rows: list[Snapshot] = []
    for machine in range(machines):
        failure_hour = rng.randint(hours * 2 // 3, hours - 1)
        onset = max(0, failure_hour - rng.randint(24, 48))
        offsets = [rng.gauss(0, sd) for sd in (0.12, 2.0, 0.08, 0.18)]
        history: list[float] = []
        for hour in range(hours):
            degradation = max(0.0, (hour - onset) / max(1, failure_hour - onset))
            vibration = 1.0 + offsets[0] + 1.9 * degradation + rng.gauss(0, 0.16)
            temperature = 65.0 + offsets[1] + 24.0 * degradation + rng.gauss(0, 2.2)
            pressure = 4.2 + offsets[2] - 0.75 * degradation + rng.gauss(0, 0.09)
            current = 8.0 + offsets[3] + 2.8 * degradation + rng.gauss(0, 0.24)
            history.append(vibration)
            recent = history[max(0, len(history) - 7):]
            trend = (recent[-1] - recent[0]) / max(1, len(recent) - 1)
            rows.append(Snapshot(f"M{machine:03d}", hour,
                (vibration, temperature, pressure, current, trend),
                int(0 <= failure_hour - hour <= 12)))
    return rows
