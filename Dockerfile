# Base Python image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy requirements first (better build caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start the API
CMD ["uvicorn", "backend.api.app:app", "--host", "0.0.0.0", "--port", "8000"]