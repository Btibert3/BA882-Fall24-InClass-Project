# Use the official Python image as the base
FROM python:3.11-slim


# Copy and install requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the training script
COPY train.py .

# Set the entrypoint to the training script
ENTRYPOINT ["python", "train.py"]
