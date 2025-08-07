# 📚 Tsunami Visualization - Development Archive

This directory contains historical development files and intermediate data from the tsunami visualization project development process.

## 📂 Directory Structure

### `data_processing/`
Contains intermediate data files from the processing pipeline:
- Raw API cache files
- Restructured data files  
- Processing pipeline documentation

### `scripts/`
Contains development and data processing scripts:
- Data collection utilities
- Cache generation tools
- Export/conversion scripts
- Metadata fetching tools

## 🎯 Purpose

These files represent the complete development history and data processing pipeline for the tsunami visualization project. While not used in production, they are preserved for:

- **Historical Reference:** Understanding how the data was processed
- **Reproducibility:** Ability to regenerate datasets if needed
- **Documentation:** Complete record of the development process
- **Future Updates:** Scripts available for processing new data

## 🚀 Production Files

The active production files are located in the project root:
- `wave_propagation_clientside_app.py` - Client-side production app
- `wave_propagation_dash_app.py` - Server-side production app
- `data/` - Active production data files
- `assets/` - Client-side assets

## 📊 Data Flow Summary

```
Historical Development → Current Archive → Active Production
     (July-August 2024)      (This folder)     (Project root)
```

## 🔧 Usage

To reference or reuse any archived components:
1. Check the README in each subdirectory for detailed information
2. Scripts can be run from the project root with path adjustments
3. Data files provide insight into the processing methodology

## 📈 Project Evolution

This archive represents the transition from:
- **Initial development** → Server-side callbacks with performance issues
- **Problem solving** → Rate limiting and loading problems identified  
- **Architecture shift** → Client-side visualization with pre-loaded data
- **Production ready** → Optimized, scalable deployment on DigitalOcean

The files here document this complete journey and the lessons learned along the way.
