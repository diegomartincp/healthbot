# Dockerfile
FROM python:3.9-slim

# Set machine proxy (optional)
#ENV https_proxy=1.2.3.4
#ENV http_proxy=1.2.3.4

# Install necessary tools
RUN apt-get update

# RUN apt install curl
RUN apt-get install -y \
    ca-certificates \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# List files (for debugging; optional)
RUN ls
# Create a directory to store the application files
RUN mkdir /app

# Copy the application scripts
COPY . /app

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Configure proxy if needed
#RUN export http_proxy=http://1.2.3.4:1234; export https_proxy=http://1.2.3.4:1234

# Command to run both Python scripts
CMD ["python", "-u", "healthbot.py"]
