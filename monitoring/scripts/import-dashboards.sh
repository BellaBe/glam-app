#!/bin/bash
# monitoring/scripts/import-dashboards.sh

# Import Grafana dashboards via API

GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASS="admin"

echo "🚀 Importing Grafana dashboards..."

# Wait for Grafana to be ready
echo "⏳ Waiting for Grafana to be ready..."
until curl -s "${GRAFANA_URL}/api/health" > /dev/null; do
    sleep 2
done

echo "✅ Grafana is ready!"

# Import dashboards from Grafana.com
import_dashboard_from_id() {
    local dashboard_id=$1
    local dashboard_name=$2
    
    echo "📊 Importing ${dashboard_name} (ID: ${dashboard_id})..."
    
    # First, fetch the dashboard JSON
    dashboard_json=$(curl -s "https://grafana.com/api/dashboards/${dashboard_id}" | jq -r '.json')
    
    if [ "$dashboard_json" == "null" ]; then
        echo "❌ Failed to fetch dashboard ${dashboard_id}"
        return
    fi
    
    # Prepare the import payload
    import_payload=$(cat <<EOF
{
    "dashboard": ${dashboard_json},
    "overwrite": true,
    "inputs": [{
        "name": "DS_PROMETHEUS",
        "type": "datasource",
        "pluginId": "prometheus",
        "value": "Prometheus"
    }],
    "folderId": 0
}
EOF
)
    
    # Import the dashboard
    response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -H "Accept: application/json" \
        -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
        -d "${import_payload}" \
        "${GRAFANA_URL}/api/dashboards/import")
    
    if echo "$response" | grep -q "\"imported\":true"; then
        echo "✅ Successfully imported ${dashboard_name}"
    else
        echo "❌ Failed to import ${dashboard_name}: $response"
    fi
}

# Alternative method using direct dashboard JSON
import_dashboard_direct() {
    local dashboard_id=$1
    local dashboard_name=$2
    local datasource_name="Prometheus"
    
    echo "📊 Importing ${dashboard_name} (ID: ${dashboard_id})..."
    
    # Download dashboard JSON from Grafana.com
    curl -s -o "/tmp/dashboard-${dashboard_id}.json" \
        "https://grafana.com/api/dashboards/${dashboard_id}/revisions/latest/download"
    
    if [ ! -f "/tmp/dashboard-${dashboard_id}.json" ]; then
        echo "❌ Failed to download dashboard ${dashboard_id}"
        return
    fi
    
    # Update datasource references in the dashboard
    sed -i 's/${DS_PROMETHEUS}/Prometheus/g' "/tmp/dashboard-${dashboard_id}.json"
    sed -i 's/\${datasource}/Prometheus/g' "/tmp/dashboard-${dashboard_id}.json"
    
    # Import using the db endpoint
    response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -H "Accept: application/json" \
        -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
        -d "{
            \"dashboard\": $(cat /tmp/dashboard-${dashboard_id}.json),
            \"overwrite\": true,
            \"message\": \"Imported ${dashboard_name}\"
        }" \
        "${GRAFANA_URL}/api/dashboards/db")
    
    if echo "$response" | grep -q "success"; then
        echo "✅ Successfully imported ${dashboard_name}"
    else
        echo "❌ Failed to import ${dashboard_name}: $response"
    fi
    
    rm -f "/tmp/dashboard-${dashboard_id}.json"
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "⚠️  jq is not installed. Using alternative import method..."
    import_method="direct"
else
    import_method="api"
fi

# Import popular dashboards
if [ "$import_method" == "api" ]; then
    import_dashboard_from_id 2279 "NATS Dashboard"
    import_dashboard_from_id 763 "Redis Dashboard"
    import_dashboard_from_id 11159 "Prometheus 2.0 Stats"
else
    import_dashboard_direct 2279 "NATS Dashboard"
    import_dashboard_direct 763 "Redis Dashboard"
    import_dashboard_direct 11159 "Prometheus 2.0 Stats"
fi

# Import custom dashboards from JSON files
import_dashboard_from_file() {
    local file_path=$1
    local dashboard_name=$2
    
    if [ -f "$file_path" ]; then
        echo "📊 Importing ${dashboard_name} from file..."
        
        response=$(curl -s -X POST \
            -H "Content-Type: application/json" \
            -H "Accept: application/json" \
            -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
            -d "{
                \"dashboard\": $(cat "$file_path"),
                \"overwrite\": true,
                \"message\": \"Imported ${dashboard_name}\"
            }" \
            "${GRAFANA_URL}/api/dashboards/db")
        
        if echo "$response" | grep -q "success"; then
            echo "✅ Successfully imported ${dashboard_name}"
        else
            echo "❌ Failed to import ${dashboard_name}: $response"
        fi
    else
        echo "⚠️  File not found: $file_path"
    fi
}

# Import custom dashboards
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DASHBOARDS_DIR="${SCRIPT_DIR}/../grafana/dashboards"

if [ -d "$DASHBOARDS_DIR" ]; then
    for dashboard in "$DASHBOARDS_DIR"/*.json; do
        if [ -f "$dashboard" ]; then
            dashboard_name=$(basename "$dashboard" .json)
            import_dashboard_from_file "$dashboard" "$dashboard_name"
        fi
    done
fi

echo ""
echo "✅ Dashboard import complete!"
echo "🔗 Access Grafana at: ${GRAFANA_URL}"
echo "   Username: ${GRAFANA_USER}"
echo "   Password: ${GRAFANA_PASS}"
echo ""
echo "📌 Imported dashboards:"
echo "   - NATS Dashboard"
echo "   - Redis Dashboard"
echo "   - Prometheus Stats"
echo ""
echo "💡 You can also import dashboards manually:"
echo "   1. Go to ${GRAFANA_URL}"
echo "   2. Navigate to Dashboards → Import"
echo "   3. Enter dashboard ID or upload JSON"