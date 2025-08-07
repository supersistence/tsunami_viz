# 📊 Data Processing Pipeline Archive

This directory contains intermediate data files from the tsunami visualization data processing pipeline.

## 📁 Files

### `raw_api_cache.pkl` (2.9MB)
- **Purpose:** Raw tsunami wave data fetched directly from NOAA CO-OPS API
- **Format:** Pickled pandas DataFrame with original API responses
- **Created by:** `wave_data_collect_and_cache.py`
- **Date:** August 1, 2024
- **Contains:** Unprocessed wave height measurements from all monitoring stations

### `restructured_data.pkl` (1.8MB)  
- **Purpose:** Intermediate processing step - data cleaned and restructured
- **Format:** Pickled pandas DataFrame with standardized time series
- **Created by:** `wave_data_collect_and_cache.py`
- **Date:** August 1, 2024
- **Contains:** Time-aligned wave measurements, missing data filled, outliers removed

## 🔄 Data Processing Flow

```
Raw API Data (raw_api_cache.pkl)
    ↓ [Clean, standardize, fill gaps]
Restructured Data (restructured_data.pkl) 
    ↓ [Pivot by station, calculate deltas]
Pivoted Wave Data (../pivoted_wave_data.pkl)
    ↓ [Generate animation frames]
Frame Cache (../frame_data_cache.pkl)
    ↓ [Export for client-side use]
Client JSON (../../assets/frame_data_client.json)
```

## 🎯 Current Status

These files represent historical steps in the data pipeline. The active production data files are:
- `../pivoted_wave_data.pkl` - Used by server-side app
- `../frame_data_cache.pkl` - Used by server-side app  
- `../station_metadata.json` - Used by client-side app
- `../../assets/frame_data_client.json` - Used by client-side app

## 🔧 Regeneration

To regenerate this data pipeline:
1. Run `../scripts/wave_data_collect_and_cache.py` to create these archived files
2. Run `../scripts/generate_frame_cache.py` to create frame cache
3. Run `../scripts/export_frame_data_to_json.py` to create client JSON

## 📈 Data Statistics

- **Time Range:** 2025-07-29 23:24:52 UTC (earthquake) + ~24 hours
- **Frequency:** 1-minute intervals (1,476 data points)
- **Stations:** 7 monitoring locations across Pacific (Midway to Hawaii)
- **Data Size:** ~5MB total raw data compressed to ~1MB active data
