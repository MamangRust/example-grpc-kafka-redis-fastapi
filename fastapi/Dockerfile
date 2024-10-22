FROM python:3.12.7-slim
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the FastAPI application code
COPY . .

# Set the PYTHONPATH to include proto directory
ENV PYTHONPATH=/app:/app/proto:$PYTHONPATH

# Run the FastAPI server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]