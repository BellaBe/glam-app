# Docker Troubleshooting Guide

## Container Won't Start

### Check Exit Code
```bash
docker inspect <container> --format '{{.State.ExitCode}}'
```

Exit Codes:

0: Clean shutdown
1: Application error (check logs)
137: OOM killed (increase memory limit)
139: Segmentation fault (code bug)
143: SIGTERM (graceful shutdown requested)

Decision Tree
Container won't start?
├─ Check logs: docker logs <container>
├─ Image built correctly? docker history <image>
├─ Port conflicts? docker ps | grep <port>
│  └─ Fix: Change port or stop conflicting container
├─ Network issues? docker network inspect <network>
│  └─ Fix: Recreate network or check DNS
└─ Resource limits? docker inspect <container> | grep -A 10 Resources
   └─ Fix: Increase limits or check host resources

## Build Issues

### Slow Builds
Check layer caching: docker history <image>
Enable BuildKit: export DOCKER_BUILDKIT=1
Optimize Dockerfile order (dependencies before code)
Minimize build context (use .dockerignore)

### Image Too Large
Use multi-stage builds
Run docker history <image> to find large layers
Combine RUN commands: RUN apt-get update && apt-get install -y pkg && rm -rf /var/lib/apt/lists/*
Switch to minimal base (alpine/slim/distroless)

## Network Problems

### Container Can't Reach Service
Check if service is on same network
docker network inspect <network> | grep <service-name>

Test connectivity from container
docker exec <container> ping <service-name>
docker exec <container> nslookup <service-name>
docker exec <container> curl <service-name>:<port>

### Port Already in Use

Find what's using the port
sudo lsof -i :<port>
or
sudo netstat -tulpn | grep <port>

Kill the process or change Docker port mapping



## Performance Issues
### High Memory Usage
```bash
# Check current usage
docker stats --no-stream

# Check for memory leaks
docker exec <container> ps aux --sort=-%mem | head

# Set memory limit
docker update --memory 512m <container>
```
### High CPU Usage
```bash
# Monitor CPU
docker stats --no-stream

# Check processes
docker top <container>

# Set CPU limit
docker update --cpus 0.5 <container>
```

## Common Commands
Cleanup
```bash
# Remove stopped containers
docker container prune -f

# Remove unused images
docker image prune -a -f

# Remove unused volumes
docker volume prune -f

# Nuclear option (all unused resources)
docker system prune -a --volumes -f
```

Inspection
```bash
# Full container details
docker inspect <container>

# Specific property
docker inspect <container> --format '{{.State.Status}}'

# Enter running container
docker exec -it <container> /bin/sh

# Copy files from container
docker cp <container>:/path/to/file ./local-path
```
