FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV EXPORT_DIR=/data/exports
EXPOSE 8000
CMD ["uvicorn", "webapp.app:app", "--host", "0.0.0.0", "--port", "8000"]
