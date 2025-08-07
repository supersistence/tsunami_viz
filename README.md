# Tsunami Wave Propagation Visualization Dashboard

This project is a scientific visualization tool for exploring tsunami wave propagation across the Pacific following the [2025 Kamchatka Peninsula earthquake](https://en.wikipedia.org/wiki/2025_Kamchatka_Peninsula_earthquake). It provides an interactive Dash dashboard that animates water level anomalies (tsunami waves) as they travel from the earthquake epicenter to NOAA tide stations across the Pacific, with supporting time series and data tables for detailed analysis.

## Project Features
- **Oscilloscope-style animation**: Visualizes the wave delta (observed - predicted tide) as a continuous trace by station distance from the epicenter, animated over time.
- **Station time series**: Stacked time series plots for each station show the evolution of wave height anomalies.
- **Live Data Table**: (Optional) View the most recent data for all stations.
- **Accurate distances**: All station distances are calculated from the precise epicenter (52.473°N, 160.396°E).

## Data Sources
- **Observed Water Levels**: [NOAA CO-OPS API](https://api.tidesandcurrents.noaa.gov/api/prod/) (`one_minute_water_level` product)
- **Predicted Tides**: [NOAA CO-OPS API](https://api.tidesandcurrents.noaa.gov/api/prod/) (`predictions` product, 1-minute interval)
- **Station Metadata**: [NOAA CO-OPS Metadata API](https://api.tidesandcurrents.noaa.gov/mdapi/prod/)

All data is fetched live from NOAA and cached locally for efficiency and reproducibility.

## Earthquake Context
This dashboard explores the aftermath of the [2025 Kamchatka Peninsula earthquake](https://en.wikipedia.org/wiki/2025_Kamchatka_Peninsula_earthquake), a major seismic event that generated a Pacific-wide tsunami. The epicenter coordinates used in this analysis are 52.473°N, 160.396°E.

## Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the dashboard
python wave_propagation_dash_app.py

# Open browser: http://localhost:8050
```

### Production Deployment
```bash
# Test locally with Docker
./local_test.sh

# Deploy to DigitalOcean
./deploy.sh
```

👉 **[Complete deployment guide →](DEPLOYMENT.md)**

## Scientific and Technical Notes
- All station coordinates and names are fetched directly from NOAA's metadata API for accuracy.
- The dashboard is designed for scientific clarity and transparency, with robust error handling and persistent caching.
- The project is intended for research, education, and outreach on tsunami science and Pacific oceanography.

---

*For questions, suggestions, or contributions, please open an issue or pull request.*
