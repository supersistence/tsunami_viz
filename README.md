# 🌊 Tsunami Wave Propagation Visualization

An interactive scientific visualization tool for exploring tsunami wave propagation across the Pacific following the [2025 Kamchatka Peninsula earthquake](https://en.wikipedia.org/wiki/2025_Kamchatka_Peninsula_earthquake). This project provides a real-time animated dashboard showing how tsunami waves travel from the earthquake epicenter to NOAA monitoring stations across the Pacific.

**🌐 Live Demo:** [https://tsunami.supersistence.org](https://tsunami.supersistence.org)

## ✨ Features

### 🎬 Interactive Visualizations
- **Real-time Animation**: Smooth playback of tsunami wave propagation over 24+ hours
- **Wave Propagation Graph**: Oscilloscope-style visualization showing wave amplitude vs distance from epicenter  
- **Station Time Series**: Individual wave height anomaly plots for each monitoring station
- **Interactive Map**: Pacific-wide view with dynamic station markers and real-time wave data

### ⚡ Performance & Usability  
- **Client-side Architecture**: Instant performance with pre-loaded data (no server callbacks)
- **Responsive Design**: Professional UI optimized for desktop and mobile
- **Timezone Support**: Switch between UTC and HST for Hawaii-focused analysis
- **Keyboard Controls**: Spacebar to play/pause, intuitive slider controls

### 🔬 Scientific Accuracy
- **Precise Calculations**: All distances calculated from exact epicenter (52.473°N, 160.396°E)
- **Real NOAA Data**: Uses actual water level measurements and tide predictions
- **7 Monitoring Stations**: From Midway Atoll to Hilo, Hawaii covering 5,275 km
- **1-Minute Resolution**: High-frequency data capture for detailed wave analysis

## 📊 Data Sources

- **📍 Station Metadata**: [NOAA CO-OPS Metadata API](https://api.tidesandcurrents.noaa.gov/mdapi/prod/)
- **🌊 Observed Water Levels**: [NOAA CO-OPS API](https://api.tidesandcurrents.noaa.gov/api/prod/) (`one_minute_water_level`)
- **🌙 Predicted Tides**: [NOAA CO-OPS API](https://api.tidesandcurrents.noaa.gov/api/prod/) (`predictions`, 1-minute interval)
- **🗺️ Map Tiles**: [MapTiler Ocean Theme](https://www.maptiler.com/) for beautiful cartographic visualization

**Data Pipeline**: Raw NOAA data → Processing & cleaning → Animation frame generation → Client-side JSON for instant loading

## 🌋 2025 Kamchatka Peninsula Earthquake

This visualization analyzes the [2025 Kamchatka Peninsula earthquake](https://en.wikipedia.org/wiki/2025_Kamchatka_Peninsula_earthquake), a significant seismic event that generated Pacific-wide tsunami waves.

**Event Details:**
- **📅 Date/Time**: July 29, 2025, 23:24:52 UTC
- **📍 Epicenter**: 52.473°N, 160.396°E  
- **🌊 Tsunami Impact**: Pacific-wide propagation affecting monitoring stations from Midway to Hawaii
- **⏱️ Timeline**: 24+ hours of wave propagation data captured

## 🚀 Quick Start

### 🌐 Live Demo
Visit **[tsunami.supersistence.org](https://tsunami.supersistence.org)** for the live application.

### 💻 Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run client-side app (recommended)
python wave_propagation_clientside_app.py

# OR run original server-side app
python wave_propagation_dash_app.py

# Open browser: http://localhost:8050
```

### 🐳 Production Deployment
```bash
# Test locally with Docker
./deployment/local_test.sh

# Deploy to DigitalOcean
./deploy.sh
```

📚 **[Complete deployment guide →](deployment/docs/DEPLOYMENT.md)**

## 🏗️ Architecture

### 📁 Project Structure
```
tsunami_viz/
├── 🎯 Production Apps
│   ├── wave_propagation_clientside_app.py    # Client-side architecture (recommended)
│   └── wave_propagation_dash_app.py          # Original server-side app
├── 📊 Active Data
│   ├── data/                                 # Production datasets
│   └── assets/                               # Client-side assets (4.8MB JSON)
├── 🚀 Deployment
│   ├── deploy.sh                             # Production deployment script
│   ├── docker-compose.yml                    # Multi-container orchestration
│   ├── Dockerfile                            # Container definition
│   └── deployment/                           # Documentation & utilities
├── 📚 Development Archive
│   ├── archive/scripts/                      # Data processing pipeline
│   └── archive/data_processing/              # Intermediate datasets
└── 🔧 Configuration
    ├── requirements.txt                       # Python dependencies
    ├── nginx/                                # Reverse proxy config
    └── .env                                  # Environment variables
```

### ⚡ Performance Optimizations
- **Client-side Architecture**: Pre-loads 4.8MB of animation data for instant playback
- **Docker Containerization**: Consistent deployments with Gunicorn WSGI server
- **Nginx Reverse Proxy**: SSL termination and rate limiting
- **Data Pipeline**: Efficient pickle → JSON conversion for browser compatibility

## 🔬 Scientific & Technical Notes

- **🎯 Accuracy**: Station coordinates fetched directly from NOAA metadata API
- **📊 Data Quality**: Robust error handling with missing data interpolation
- **🌊 Wave Calculation**: Δ = Observed - Predicted tide levels
- **📐 Distance Precision**: Great circle calculations from exact epicenter coordinates
- **🎓 Use Cases**: Research, education, tsunami science outreach, and Pacific oceanography

## 🛠️ Development

### 🔄 Data Processing Pipeline
```bash
# Located in archive/scripts/ (historical reference)
python fetch_station_metadata.py          # Get station info from NOAA
python wave_data_collect_and_cache.py     # Fetch & process wave data  
python generate_frame_cache.py            # Create animation frames
python export_frame_data_to_json.py       # Export for client-side use
```

### 🧪 Testing & Validation
```bash
# Local testing
./deployment/local_test.sh

# Production health check
curl -I https://tsunami.supersistence.org
```

## 📈 Production Deployment

- **🌐 Live URL**: [tsunami.supersistence.org](https://tsunami.supersistence.org)
- **☁️ Infrastructure**: DigitalOcean Droplet ($6/month)
- **🔒 Security**: SSL/TLS with Let's Encrypt certificates
- **📊 Monitoring**: Docker health checks and nginx access logs
- **⚡ Performance**: Client-side rendering eliminates server callback bottlenecks