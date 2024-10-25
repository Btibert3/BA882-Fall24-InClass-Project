FROM python:3.12-slim

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy prediction code
COPY main.py .

# Set environment variables
ENV AIP_HEALTH_ROUTE=/health
ENV AIP_PREDICT_ROUTE=/predict
ENV AIP_HTTP_PORT=8080
ENV PYTHONUNBUFFERED=TRUE

# Run the application
ENTRYPOINT ["python", "main.py"]