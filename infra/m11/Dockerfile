FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY app app
COPY scripts/cited_assistant.py scripts/investigation_backup.py scripts/investigation_store.py scripts/serve_product.py scripts/
COPY product/dashboard.json product/dashboard.json

RUN useradd --create-home --uid 10001 appuser
USER 10001

EXPOSE 4173
CMD ["python3", "-B", "scripts/serve_product.py", "--host", "0.0.0.0", "--port", "4173", "--payload", "/app/product/dashboard.json", "--database", "/tmp/mbs/investigations.sqlite"]
