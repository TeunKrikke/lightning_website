This is the code for a FastAPI/Vue/TypeScript website running on the raspberry pi 3B that gets the information from a DFRobotics Gravity Lightning distance sensor. The website displays the distance of lightning from the current location within a 40km range. It will also give an overview of recently detected strikes (amount, intensity and distance). Whenever a strike is detected this will be stored in a postgresql database with all available information.

Additionally, the webapp connects to a 1.14inch Waveshare display (which is also connected to the raspberrypi) and shows the 3 most recent strikes with distance, date, time and intensity. This display will only be on between 8 and 20.

---

## 📊 Grafana Integration

This project includes built-in support for Grafana. It leverages Grafana's auto-provisioning system to automatically configure the PostgreSQL database connection and pre-load a customized, rich analytics dashboard.

### Dashboard Features
- **Key Metrics (Stat Panels)**: Real-time counts of total strikes in the selected time range, average strike distance, and maximum intensity.
- **Storm Trend Visualizer**: A scatter plot mapping strike distance over time, enabling you to visually track whether a storm is approaching or receding.
- **Strike Frequency**: Hourly bar charts tracking strike frequency.
- **Proximity Distribution**: A bar gauge breaking down strikes by proximity bands: *0-5 km (Very Close)*, *5-15 km (Close)*, *15-30 km (Moderate)*, and *30-40 km (Distant)*.
- **Detailed History Logs**: A list of the last 100 strikes with timestamp, distance, and intensity.

### Setup Instructions

#### Option 1: Native Installation (Systemd Service)
For running Grafana directly on the Raspberry Pi:
1. Make the installer script executable:
   ```bash
   chmod +x setup_grafana.sh
   ```
2. Run the script:
   ```bash
   ./setup_grafana.sh
   ```
3. Open `http://localhost:3000` in your web browser.
4. Log in using default credentials (username: `admin` / password: `admin`), and change your password when prompted.
5. The **RPi Lightning Tracker** dashboard will be available under the **Lightning Tracker** folder.

#### Option 2: Running via Docker
If you prefer running Grafana in a Docker container on the host:
1. Launch Grafana mounting the project's provisioning and dashboard directories:
   ```bash
   docker run -d -p 3000:3000 \
     --name=lightning-grafana \
     --network="host" \
     -v $(pwd)/grafana/provisioning:/etc/grafana/provisioning \
     -v $(pwd)/grafana/dashboards:/var/lib/grafana/dashboards \
     grafana/grafana-oss
   ```
2. Access Grafana at `http://localhost:3000`.
   *(Note: `--network="host"` is used so Grafana can connect directly to the database running on localhost:5432.)*