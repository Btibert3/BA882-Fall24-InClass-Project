# Use an official Python runtime as a base image
FROM python:3.11-slim

# Install necessary system dependencies for Quarto
RUN apt-get update && apt-get install -y \
    curl \
    pandoc \
    libssl-dev \
    libxml2-dev \
    libcairo2-dev \
    libxtst6 \
    libx11-6 \
    libglu1-mesa \
    wget \
    && apt-get clean

# Install Quarto
RUN wget https://github.com/quarto-dev/quarto-cli/releases/download/v1.5.57/quarto-1.5.57-linux-amd64.deb \
    && dpkg -i quarto-1.5.57-linux-amd64.deb \
    && rm quarto-1.5.57-linux-amd64.deb

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file for Python dependencies (if any)
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --upgrade pip ipython ipykernel


# Copy the rest of your application code
COPY report_render.py /app/report_render.py
COPY template.qmd /app/template.qmd

# Set environment variable for Google Cloud Run
ENV PORT 8080
EXPOSE 8080

# Run the Python application
CMD ["gunicorn", "-b", "0.0.0.0:8080", "report_render:app"]
