FROM python:3.10-slim

WORKDIR /app

# Install system dependencies required for scikit-surprise
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel
# Install Cython first as it's required for scikit-surprise
RUN pip install --no-cache-dir cython==3.0.6 numpy==1.25.2
# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY apps/ .

EXPOSE 8001

CMD ["python", "main.py"]