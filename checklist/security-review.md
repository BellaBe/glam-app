# Docker Security Review Checklist

## Image Security
- [ ] Run as non-root user
- [ ] Use specific image tags (not :latest)
- [ ] Multi-stage builds to minimize attack surface
- [ ] Scan images with trivy/grype
- [ ] Use .dockerignore to exclude secrets
- [ ] Pin dependency versions
- [ ] Minimal base images (alpine/distroless)
- [ ] No secrets in image layers (check with `docker history`)
- [ ] Base image from verified/official source
- [ ] Image size optimized (< 500MB for most apps)

## Runtime Security
- [ ] Resource limits defined (CPU, memory)
- [ ] Read-only root filesystem where possible
- [ ] Capabilities dropped (--cap-drop=ALL)
- [ ] No privileged mode
- [ ] Security profiles enabled (AppArmor/SELinux)
- [ ] Health checks implemented
- [ ] Secrets managed via Docker secrets or vault
- [ ] Environment variables don't contain sensitive data

## Network Security
- [ ] Custom bridge network (not default)
- [ ] Only required ports exposed
- [ ] TLS/SSL enabled for external communication
- [ ] Network segmentation implemented
- [ ] Firewall rules configured

## Compliance
- [ ] Container logs to centralized system
- [ ] Audit logging enabled
- [ ] Vulnerability scan results documented
- [ ] Image provenance tracked