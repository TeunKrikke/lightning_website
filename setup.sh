#!/usr/bin/env bash
# ==============================================================================
# Setup script for the Raspberry Pi Lightning Tracker
# ==============================================================================

set -e

PROJECT_DIR=$(pwd)
CURRENT_USER=$(whoami)

echo "⚡ Starting setup for RPi Lightning Tracker..."
echo "📍 Project Directory: ${PROJECT_DIR}"
echo "👤 Target User: ${CURRENT_USER}"

# 1. Update and install system dependencies
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib libpq-dev python3 python3-pip python3-venv nodejs npm git unzip python3-gpiozero python3-dev swig liblgpio-dev

# 2. Configure PostgreSQL database and users
echo "🗄️ Configuring PostgreSQL database..."
# Start PostgreSQL service if not running
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create Database and User (suppressing error if already exists)
sudo -u postgres psql -c "CREATE USER lightning_user WITH PASSWORD 'lightning_pass';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE lightning_db OWNER lightning_user;" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE lightning_db TO lightning_user;" 2>/dev/null || true
# PostgreSQL 15+ changes: grant public schema access
sudo -u postgres psql -d lightning_db -c "GRANT ALL ON SCHEMA public TO lightning_user;" 2>/dev/null || true

# 3. Enable Raspberry Pi Hardware Interfaces (I2C and SPI)
echo "🔌 Enabling I2C and SPI hardware buses..."
# Check both /boot/config.txt and newer /boot/firmware/config.txt locations
CONFIG_FILE=""
if [ -f /boot/firmware/config.txt ]; then
    CONFIG_FILE="/boot/firmware/config.txt"
elif [ -f /boot/config.txt ]; then
    CONFIG_FILE="/boot/config.txt"
fi

if [ -n "$CONFIG_FILE" ]; then
    # Enable I2C
    if ! grep -q "^dtparam=i2c_arm=on" "$CONFIG_FILE"; then
        echo "dtparam=i2c_arm=on" | sudo tee -a "$CONFIG_FILE" > /dev/null
        echo "Enabled I2C in $CONFIG_FILE"
    fi
    # Enable SPI
    if ! grep -q "^dtparam=spi=on" "$CONFIG_FILE"; then
        echo "dtparam=spi=on" | sudo tee -a "$CONFIG_FILE" > /dev/null
        echo "Enabled SPI in $CONFIG_FILE"
    fi
else
    echo "⚠️ Warning: RPi config.txt file not found. Skipping hardware interface configuration."
fi

# 4. Configure Python Virtual Environment
echo "🐍 Setting up Python Virtual Environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic smbus2 numpy pillow gpiozero spidev websockets httpx pytest pytest-asyncio

# 5. Install and Build Vue 3 Frontend
echo "💻 Building Frontend Webapp..."
cd "${PROJECT_DIR}/frontend"
npm install
npm run build
cd "${PROJECT_DIR}"

# 6. Configure systemd Service
echo "⚙️ Creating systemd service configuration..."
sudo tee /etc/systemd/system/lightning.service > /dev/null <<EOF
[Unit]
Description=Raspberry Pi Lightning Tracker Server
After=network.target postgresql.service

[Service]
Type=simple
User=${CURRENT_USER}
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/venv/bin/python main.py
Restart=on-failure
Environment=DATABASE_URL=postgresql://lightning_user:lightning_pass@localhost:5432/lightning_db

[Install]
WantedBy=multi-user.target
EOF

# Reload and enable the service
sudo systemctl daemon-reload
sudo systemctl enable lightning.service
sudo systemctl start lightning.service

echo "✅ Setup Completed Successfully!"
echo "🚀 The Lightning Tracker service is now running in the background."
echo "🔗 Open http://localhost:8000 in your browser to view the live dashboard."
