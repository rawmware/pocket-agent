FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV WORKSPACE_DIR=/app/workspace MEMORY_DIR=/app/memory DATA_DIR=/app/data
VOLUME ["/app/workspace", "/app/memory", "/app/data"]
EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
