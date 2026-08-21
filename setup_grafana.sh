#!/usr/bin/env bash
# ==============================================================================
# Setup script for Grafana on the Raspberry Pi Lightning Tracker
# ==============================================================================

set -e

PROJECT_DIR=$(pwd)

echo "⚡ Starting Grafana setup for RPi Lightning Tracker..."
echo "📍 Project Directory: ${PROJECT_DIR}"

# 1. Install Grafana via official APT repository
if [ -f /etc/debian_version ]; then
    echo "📦 Installing Grafana from the official repository..."
    
    # Install prerequisites
    sudo apt-get install -y apt-transport-https software-properties-common wget gpg
    
    # Add official GPG key
    sudo mkdir -p /etc/apt/keyrings/
    wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
    
    # Add stable release repository
    echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
    
    # Update and install
    sudo apt-get update
    sudo apt-get install -y grafana
else
    echo "⚠️ Warning: Non-Debian based OS detected. Skipping automated installation."
    echo "👉 Please install Grafana manually for your distribution, then rerun this script or manually copy configurations."
fi

# 2. Configure Grafana Provisioning
echo "⚙️ Provisioning Grafana datasource and dashboard..."

# Create necessary folders
sudo mkdir -p /etc/grafana/provisioning/datasources
sudo mkdir -p /etc/grafana/provisioning/dashboards
sudo mkdir -p /var/lib/grafana/dashboards

# Copy provisioning configurations
if [ -f "${PROJECT_DIR}/grafana/provisioning/datasources/postgresql.yaml" ]; then
    sudo cp "${PROJECT_DIR}/grafana/provisioning/datasources/postgresql.yaml" /etc/grafana/provisioning/datasources/postgresql.yaml
    echo "✅ Copied PostgreSQL datasource provisioning config."
else
    echo "❌ Error: postgresql.yaml datasource config not found in project directory!"
    exit 1
fi

if [ -f "${PROJECT_DIR}/grafana/provisioning/dashboards/dashboards.yaml" ]; then
    sudo cp "${PROJECT_DIR}/grafana/provisioning/dashboards/dashboards.yaml" /etc/grafana/provisioning/dashboards/dashboards.yaml
    echo "✅ Copied dashboards provider provisioning config."
else
    echo "❌ Error: dashboards.yaml provisioning config not found!"
    exit 1
fi

# Copy dashboard JSON definition
if [ -f "${PROJECT_DIR}/grafana/dashboards/lightning_dashboard.json" ]; then
    sudo cp "${PROJECT_DIR}/grafana/dashboards/lightning_dashboard.json" /var/lib/grafana/dashboards/lightning_dashboard.json
    echo "✅ Copied lightning tracker dashboard definition."
else
    echo "❌ Error: lightning_dashboard.json dashboard layout not found!"
    exit 1
fi

# 3. Correct file ownerships for Grafana user
echo "🔒 Adjusting permissions..."
sudo chown -R grafana:grafana /etc/grafana/provisioning/
sudo chown -R grafana:grafana /var/lib/grafana/dashboards/

# 4. Start and enable Grafana service
if [ -f /etc/debian_version ]; then
    echo "🔄 Starting and enabling Grafana server service..."
    sudo systemctl daemon-reload
    sudo systemctl enable grafana-server
    sudo systemctl restart grafana-server
    echo "✅ Grafana service restarted successfully."
else
    echo "👉 Please start/restart the grafana-server service manually on your system."
fi

echo "=============================================================================="
echo "🎉 Grafana Integration Successful!"
echo "=============================================================================="
echo "🔗 Grafana is now listening on port 3000 (http://localhost:3000)."
echo "👤 Default Login credentials:"
echo "   - Username: admin"
echo "   - Password: admin"
echo "📈 The 'RPi Lightning Tracker' dashboard has been pre-loaded under the"
echo "   'Lightning Tracker' folder."
echo "=============================================================================="
