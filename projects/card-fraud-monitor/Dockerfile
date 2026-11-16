FROM python:3.11-slim
WORKDIR /app
COPY python/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY python/ .
RUN python -m app.train
ENV MODEL_PATH=/app/artifacts/fraud.joblib
CMD ["uvicorn","app.api:app","--host","0.0.0.0","--port","8000"]
