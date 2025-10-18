# Docker Performance Optimization Checklist

## Image Optimization
- [ ] Multi-stage builds to reduce size
- [ ] Minimal base image (alpine/slim/distroless)
- [ ] Layer caching optimized (deps before code)
- [ ] Unnecessary files excluded (.dockerignore)
- [ ] Combined RUN commands to reduce layers
- [ ] Build cache utilized (BuildKit enabled)
- [ ] Image squashing considered for final size

## Build Performance
- [ ] BuildKit enabled (DOCKER_BUILDKIT=1)
- [ ] Build context minimized
- [ ] .dockerignore configured properly
- [ ] Dependency caching optimized
- [ ] Parallel builds utilized
- [ ] Registry mirror configured (if applicable)

## Runtime Performance
- [ ] Resource limits appropriate (not over/under-provisioned)
- [ ] Volume mounts for I/O intensive operations
- [ ] tmpfs for temporary data
- [ ] Host network mode evaluated (if latency critical)
- [ ] Connection pooling configured
- [ ] DNS caching configured

## Compose/Orchestration
- [ ] Service dependencies properly ordered
- [ ] Health checks prevent premature traffic
- [ ] Volume permissions optimized
- [ ] Network mode appropriate (bridge/host)
- [ ] Parallel service startup where possible

## Monitoring
- [ ] Container stats baseline established
- [ ] Resource usage monitored
- [ ] Performance metrics collected
- [ ] Bottlenecks identified and addressed
