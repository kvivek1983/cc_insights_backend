#!/bin/bash
set -e

# --- SSH Tunnel Setup ---
# The SSH_PRIVATE_KEY env var contains the PEM key contents (set in Railway secrets)
if [ -n "$SSH_PRIVATE_KEY" ]; then
    echo "Setting up SSH tunnel to jump server..."

    # Write key to file
    mkdir -p /root/.ssh
    echo "$SSH_PRIVATE_KEY" > /root/.ssh/tunnel_key.pem
    chmod 600 /root/.ssh/tunnel_key.pem

    # Disable strict host key checking for the jump server
    cat > /root/.ssh/config <<SSHEOF
Host jump
    HostName ${JUMP_HOST:-13.234.98.188}
    User ${JUMP_USER:-ubuntu}
    IdentityFile /root/.ssh/tunnel_key.pem
    StrictHostKeyChecking no
    ServerAliveInterval 30
    ServerAliveCountMax 3
SSHEOF

    # Start tunnel with autossh (auto-reconnects on drop)
    # Maps localhost:15432 -> private DB server 172.17.5.229:5432
    AUTOSSH_PIDFILE=/tmp/autossh.pid
    autossh -M 0 \
        -f -N \
        -o "StrictHostKeyChecking=no" \
        -o "ServerAliveInterval=30" \
        -o "ServerAliveCountMax=3" \
        -i /root/.ssh/tunnel_key.pem \
        -L ${DB_PORT:-15432}:${DB_PRIVATE_HOST:-172.17.5.229}:5432 \
        ${JUMP_USER:-ubuntu}@${JUMP_HOST:-13.234.98.188}

    # Wait for tunnel to be ready
    echo "Waiting for SSH tunnel..."
    for i in $(seq 1 30); do
        if nc -z 127.0.0.1 ${DB_PORT:-15432} 2>/dev/null; then
            echo "SSH tunnel established on port ${DB_PORT:-15432}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "ERROR: SSH tunnel failed to establish after 30s"
            exit 1
        fi
        sleep 1
    done
else
    echo "No SSH_PRIVATE_KEY set — assuming direct DB access"
fi

# --- Start API Server ---
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
