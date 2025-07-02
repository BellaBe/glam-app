# monitoring/README.md

# GlamYouUp Monitoring Guide

This directory contains monitoring configurations, queries, and dashboards for the GlamYouUp platform.

## 📁 Directory Structure

```
monitoring/
├── README.md                          # This file
├── prometheus-queries.yml             # Collection of useful Prometheus queries
├── prometheus.yml                     # Prometheus configuration
├── prometheus/
│   └── alerts.yml                    # Alert rules
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── prometheus.yml        # Datasource config
│   │   └── dashboards/
│   │       └── dashboard.yml         # Dashboard provisioning
│   └── dashboards/
│       ├── notification-service.json # Notification service dashboard
│       ├── system-overview.json      # System overview dashboard
│       └── business-metrics.json     # Business metrics dashboard
└── scripts/
    └── import-dashboards.sh          # Script to import dashboards

```

## 🚀 Quick Start

### 1. Start Monitoring Stack
```bash
make dev  # Starts everything including monitoring
```

### 2. Access Monitoring Tools
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **NATS Dashboard**: http://localhost:8222
- **Metrics Endpoints**:
  - NATS: http://localhost:7777/metrics
  - Redis: http://localhost:9121/metrics
  - Notification Service: http://localhost:8002/metrics

### 3. Import Dashboards
```bash
# Automatic import
cd monitoring/scripts
./import-dashboards.sh

# Or manually in Grafana:
# 1. Go to Dashboards → Import
# 2. Upload JSON files from monitoring/grafana/dashboards/
```

## 📊 Available Queries

All queries are documented in `prometheus-queries.yml`. Categories include:

- **Notification Service**: Success rates, error tracking, queue metrics
- **HTTP/API Metrics**: Request rates, latency, error rates
- **NATS Messaging**: Connection stats, message flow, JetStream metrics
- **Redis**: Performance, memory usage, hit rates
- **Business Metrics**: Daily summaries, top notification types

## 🎯 Key Metrics to Monitor

### Notification Service Health
```promql
# Success rate should be > 95%
(rate(notifications_sent_total{status="success"}[5m]) / 
 rate(notifications_sent_total[5m])) * 100

# Queue size should be < 1000
email_queue_size

# Processing time should be < 5s
histogram_quantile(0.95, rate(notifications_duration_seconds_bucket[5m]))
```

### System Health
```promql
# All services should be up
up{job=~"notification-service|nats|redis"}

# Error rate should be < 5%
sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
```

## 🚨 Alerts

Alerts are configured in `prometheus/alerts.yml`. Key alerts:

- **NotificationHighErrorRate**: Error rate > 10%
- **EmailQueueBacklog**: Queue size > 1000
- **ServiceDown**: Any service is down
- **APIHighLatency**: 95th percentile > 1s

## 📈 Creating Custom Dashboards

### Example Panel Configuration
```json
{
  "title": "My Custom Metric",
  "targets": [
    {
      "expr": "rate(my_metric_total[5m])",
      "legendFormat": "{{label_name}}"
    }
  ],
  "type": "graph"
}
```

## 🔧 Troubleshooting

### No data in Grafana?
1. Check Prometheus targets: http://localhost:9090/targets
2. Verify metrics endpoints are accessible
3. Check service logs: `make dev-logs-monitoring`

### High memory usage?
```promql
# Check Redis memory
redis_memory_used_bytes

# Check Prometheus storage
prometheus_tsdb_storage_blocks_bytes
```

### Missing metrics?
1. Ensure services are running: `make dev-ps`
2. Check if metrics endpoint is exposed
3. Verify Prometheus scrape config

## 📚 Useful Resources

- [Prometheus Query Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)
- [Grafana Best Practices](https://grafana.com/docs/grafana/latest/best-practices/)
- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/)

## 🎓 Learning Queries

Start with these simple queries in Prometheus (http://localhost:9090):

```promql
# Show all metrics
{__name__=~".+"}

# Show notification metrics
{__name__=~"notification.*"}

# Simple rate calculation
rate(notifications_sent_total[5m])

# Grouping by label
sum by (type) (rate(notifications_sent_total[5m]))
```