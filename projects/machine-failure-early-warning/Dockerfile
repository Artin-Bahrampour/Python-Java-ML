FROM python:3.12-slim
WORKDIR /app
COPY maintenance_ml ./maintenance_ml
COPY README.md LICENSE ./
RUN useradd --create-home appuser && mkdir -p /app/reports && chown -R appuser:appuser /app
USER appuser
ENTRYPOINT ["python", "-m", "maintenance_ml.cli"]
CMD ["--output", "/app/reports"]
