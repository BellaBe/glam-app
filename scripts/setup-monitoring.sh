#!/bin/bash
# setup-monitoring.sh

echo "🚀 Setting up monitoring stack..."

# Create directory structure
mkdir -p monitoring/prometheus
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p monitoring/grafana/provisioning/dashboards
mkdir -p monitoring/grafana/dashboards

# Create Prometheus config
cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # NATS Server metrics
  - job_name: 'nats'
    static_configs:
      - targets: ['nats-exporter:7777']
        labels:
          service: 'nats'
          environment: 'local'
EOF

# Create Grafana datasource config
cat > monitoring/grafana/provisioning/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

# Create Grafana dashboard config
cat > monitoring/grafana/provisioning/dashboards/dashboard.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF

echo "✅ Monitoring configuration created!"
echo ""
echo "📊 To start the monitoring stack:"
echo "   docker-compose -f docker-compose.local.yml up -d prometheus grafana nats-exporter"
echo ""
echo "🔗 Access points:"
echo "   - Grafana: http://localhost:3000 (admin/admin)"
echo "   - Prometheus: http://localhost:9090"
echo "   - NATS Metrics: http://localhost:7777/metrics"
echo ""
echo "📈 Next steps:"
echo "   1. Login to Grafana"
echo "   2. Import NATS dashboard: https://grafana.com/grafana/dashboards/2279"
echo "   3. Create your custom dashboards"
