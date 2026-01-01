FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY webhook/requirements.txt ./webhook/
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r webhook/requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run the webhook server
CMD ["python", "-m", "uvicorn", "webhook.server:app", "--host", "0.0.0.0", "--port", "8000"]
