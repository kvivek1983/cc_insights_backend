FROM python:3.11-slim

# Install SSH client for tunnel to jump server
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client autossh \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make start script executable
RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
