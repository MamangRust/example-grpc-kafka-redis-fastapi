FROM python:3.12.7-slim
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the gRPC service code
COPY . .

# Set the PYTHONPATH to include proto directory
ENV PYTHONPATH=/app:/app/proto:$PYTHONPATH

EXPOSE 50051

# Run the gRPC server
CMD ["python", "main.py"]