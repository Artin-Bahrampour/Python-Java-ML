from datetime import datetime, timedelta, timezone
import random


def generate_telemetry(count: int, seed: int = 42, anomaly_ratio: float = 0.05):
    rng = random.Random(seed)
    start = datetime.now(timezone.utc) - timedelta(minutes=count)
    rows = []

    for i in range(count):
        anomaly = rng.random() < anomaly_ratio
        if anomaly:
            latency = rng.uniform(500, 1800)
            error_rate = rng.uniform(0.08, 0.4)
            rpm = rng.uniform(10, 80)
            cpu = rng.uniform(85, 100)
            memory = rng.uniform(80, 99)
        else:
            latency = max(10, rng.gauss(120, 25))
            error_rate = max(0, min(1, rng.gauss(0.01, 0.006)))
            rpm = max(20, rng.gauss(250, 45))
            cpu = max(5, min(100, rng.gauss(48, 10)))
            memory = max(10, min(100, rng.gauss(55, 9)))

        rows.append({
            "service": rng.choice(["payments-api", "orders-api", "catalog-api"]),
            "timestamp": start + timedelta(minutes=i),
            "latency_ms": round(latency, 2),
            "error_rate": round(error_rate, 5),
            "requests_per_minute": round(rpm, 2),
            "cpu_percent": round(cpu, 2),
            "memory_percent": round(memory, 2),
            "synthetic_anomaly": anomaly,
        })
    return rows
