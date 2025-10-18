# Production Readiness Checklist

## Build & Deploy
- [ ] Dockerfile optimized for layer caching
- [ ] Build time < 5 minutes (or justified)
- [ ] Image size < 500MB (or justified)
- [ ] Multi-stage builds implemented
- [ ] .dockerignore configured
- [ ] Version tags follow semantic versioning
- [ ] Build reproducible (pinned dependencies)
- [ ] CI/CD pipeline configured

## Configuration
- [ ] Environment-specific configs externalized
- [ ] Secrets not hardcoded
- [ ] Resource limits defined (CPU, memory)
- [ ] Health checks configured
- [ ] Restart policy set (unless-stopped/always)
- [ ] Logging to stdout/stderr
- [ ] Timezone configured if needed

## Monitoring & Observability
- [ ] Health check endpoint implemented
- [ ] Metrics exposed (Prometheus format preferred)
- [ ] Structured logging implemented
- [ ] Log aggregation configured
- [ ] Container stats monitored
- [ ] Alerting rules defined

## Reliability
- [ ] Graceful shutdown handling (SIGTERM)
- [ ] Database connection pooling
- [ ] Retry logic for external dependencies
- [ ] Circuit breakers implemented
- [ ] Timeout configurations set
- [ ] Backup strategy defined

## Performance
- [ ] Connection pooling configured
- [ ] Caching strategy implemented
- [ ] Static assets optimized
- [ ] Database indexes verified
- [ ] Load testing completed
- [ ] Resource usage profiled