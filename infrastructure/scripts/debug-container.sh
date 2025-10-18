#!/bin/bash
# Container Debugging Script
# Source: Docker Troubleshooting Ch.7, pg 98-105

set -e

CONTAINER=$1

if [ -z "$CONTAINER" ]; then
    echo "Usage: $0 <container-name-or-id>"
    exit 1
fi

echo "=== Container Status ==="
docker inspect $CONTAINER --format '{{.State.Status}}'
docker inspect $CONTAINER --format 'Exit Code: {{.State.ExitCode}}'
# Exit codes: 0=clean, 1=app error, 137=OOM killed, 139=segfault

echo -e "\n=== Last 50 Log Lines ==="
docker logs --tail 50 $CONTAINER

echo -e "\n=== Resource Usage ==="
docker stats --no-stream $CONTAINER

echo -e "\n=== Running Processes ==="
docker top $CONTAINER

echo -e "\n=== Port Bindings ==="
docker port $CONTAINER

echo -e "\n=== Network Config ==="
docker inspect $CONTAINER --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'

echo -e "\n=== Volume Mounts ==="
docker inspect $CONTAINER --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'

echo -e "\n=== Environment Variables ==="
docker exec $CONTAINER env | sort
