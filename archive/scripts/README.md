# 🛠️ Development Scripts Archive

This directory contains scripts used during the development and data processing pipeline for the tsunami visualization project.

## 📁 Script Files

### `wave_data_collect_and_cache.py`
- **Purpose:** Primary data collection script that fetches tsunami wave data from NOAA CO-OPS API
- **Functionality:**
  - Fetches real-time wave height data for 7 Pacific monitoring stations
  - Cleans and processes raw API responses
  - Handles missing data and outliers
  - Creates time-aligned datasets
  - Generates pivoted data structure for visualization
- **Output Files:**
  - `../data_processing/raw_api_cache.pkl`
  - `../data_processing/restructured_data.pkl` 
  - `../data/pivoted_wave_data.pkl`
- **Usage:** `python wave_data_collect_and_cache.py`

### `generate_frame_cache.py`
- **Purpose:** Generates pre-calculated animation frames for smooth visualization playback
- **Functionality:**
  - Loads pivoted wave data
  - Calculates wave propagation for each time step
  - Creates animation frame cache for instant loading
  - Optimizes data structure for real-time playback
- **Input:** `../data/pivoted_wave_data.pkl`
- **Output:** `../data/frame_data_cache.pkl`
- **Usage:** `python generate_frame_cache.py`

### `fetch_station_metadata.py`
- **Purpose:** Retrieves monitoring station metadata from NOAA API
- **Functionality:**
  - Fetches station coordinates, names, and configuration
  - Creates standardized metadata structure
  - Used for map visualization and station identification
- **Output:** `../data/station_metadata.json`
- **Usage:** `python fetch_station_metadata.py`

### `export_frame_data_to_json.py`
- **Purpose:** Converts pickle-based frame cache to JSON for client-side loading
- **Functionality:**
  - Loads frame cache data
  - Handles NumPy/Pandas data type conversion
  - Exports browser-compatible JSON format
  - Enables client-side visualization without server callbacks
- **Input:** `../data/frame_data_cache.pkl`
- **Output:** `../../assets/frame_data_client.json`
- **Usage:** `python export_frame_data_to_json.py`

## 🔄 Development Workflow

### Initial Data Setup
```bash
# 1. Fetch station information
python fetch_station_metadata.py

# 2. Collect and process wave data  
python wave_data_collect_and_cache.py

# 3. Generate animation frames
python generate_frame_cache.py

# 4. Export for client-side use
python export_frame_data_to_json.py
```

### Data Updates
```bash
# To refresh with new data:
python wave_data_collect_and_cache.py
python generate_frame_cache.py  
python export_frame_data_to_json.py
```

## 📊 Data Pipeline Architecture

```
NOAA API
    ↓ [fetch_station_metadata.py]
Station Metadata (../data/station_metadata.json)

NOAA API  
    ↓ [wave_data_collect_and_cache.py]
Raw Cache → Restructured → Pivoted Data
    ↓ [generate_frame_cache.py]
Frame Cache (../data/frame_data_cache.pkl)
    ↓ [export_frame_data_to_json.py]  
Client JSON (../../assets/frame_data_client.json)
```

## 🎯 Current Production Status

These scripts were used to create the current production dataset:
- **Data Date:** July 29-30, 2025 (simulated 2025 Kamchatka earthquake)
- **Processing Date:** August 1-6, 2024
- **Status:** Archive - data pipeline complete, production apps deployed

## 🔧 Dependencies

All scripts require the packages listed in `../../requirements.txt`:
- `pandas` - Data manipulation
- `numpy` - Numerical operations  
- `requests` - API calls
- `python-dotenv` - Environment variables

## 🚨 Notes

- These scripts contain hardcoded dates/coordinates for the 2025 scenario
- For real tsunami events, update earthquake coordinates and timing
- API rate limits may require delays between requests
- Large datasets may need chunked processing for memory efficiency
