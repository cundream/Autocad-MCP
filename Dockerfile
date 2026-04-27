FROM python:3.11-slim

WORKDIR /app

RUN useradd --create-home --shell /bin/bash mcp

COPY pyproject.toml ./
COPY server.py config.py security.py ./
COPY backends/ ./backends/

RUN pip install --no-cache-dir -e .

USER mcp

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import server; print('ok')" || exit 1

CMD ["python", "server.py"]
