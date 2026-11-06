# Water Leak Risk Service

An operational ML service that prioritizes pipe segments for leak investigation from pressure-drop, flow variance, age, and repair-history signals. Python trains and serves the model; Java 17 demonstrates work-order integration. The data generator is synthetic.

```bash
cd python && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.train --synthetic --output artifacts/leak.joblib
uvicorn app.api:app --port 8000
```

Compile the client: `cd java && javac -d out src/main/java/com/example/water/*.java && java -cp out com.example.water.LeakClient http://127.0.0.1:8000`.

The score prioritizes inspections only; it must not automatically change water-network controls. See [docs/OPERATIONS.md](docs/OPERATIONS.md).
