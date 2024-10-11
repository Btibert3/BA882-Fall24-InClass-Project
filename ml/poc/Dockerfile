FROM us-docker.pkg.dev/vertex-ai/training/sklearn-cpu.1-0:latest

# Set up working directory
WORKDIR /app

# Copy your script
COPY train.py /app/train.py

# Install additional dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Run your training script
ENTRYPOINT ["python", "/app/train.py"]
