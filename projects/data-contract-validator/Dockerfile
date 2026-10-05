FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml requirements-dev.txt ./
COPY src ./src
RUN pip install --no-cache-dir .
USER 65532:65532
ENTRYPOINT ["dcv"]
