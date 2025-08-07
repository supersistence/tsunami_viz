#!/usr/bin/env python3
"""
Export frame data cache to JSON for client-side animation
This will create a JSON file that can be loaded by the browser for pure client-side animation
"""

import pickle
import json
import pandas as pd
import numpy as np
from datetime import datetime

def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, (np.int64, np.int32, np.integer)):
        return int(obj)
    elif isinstance(obj, (pd.Timestamp, np.datetime64)):
        return pd.Timestamp(obj).isoformat()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj

def export_frame_data_to_json():
    """Export the frame data cache to JSON format"""
    print("🔄 Loading frame data cache...")
    
    # Load the existing frame cache
    with open("data/frame_data_cache.pkl", "rb") as f:
        frame_data_cache = pickle.load(f)
    
    print(f"✅ Loaded {len(frame_data_cache)} frames")
    
    # Load station metadata
    with open("data/station_metadata.json", "r") as f:
        station_metadata = json.load(f)
    
    # Create the client-side data structure
    client_data = {
        "metadata": {
            "total_frames": len(frame_data_cache),
            "stations": station_metadata,
            "export_timestamp": datetime.now().isoformat(),
            "data_source": "NOAA CO-OPS API",
            "description": "Tsunami wave propagation data following 2025 Kamchatka earthquake"
        },
        "frames": {}
    }
    
    print("🔄 Converting frame data...")
    
    # Convert each frame, ensuring all numpy types are converted
    for frame_idx, frame_data in frame_data_cache.items():
        # Convert the frame data to JSON-serializable format
        converted_frame = {}
        for key, value in frame_data.items():
            converted_frame[key] = convert_numpy_types(value)
        
        client_data["frames"][str(frame_idx)] = converted_frame
        
        # Progress indicator
        if frame_idx % 100 == 0:
            print(f"  Processed {frame_idx}/{len(frame_data_cache)} frames...")
    
    print("🔄 Writing JSON file...")
    
    # Write to JSON file with optimized settings
    with open("data/frame_data_client.json", "w") as f:
        json.dump(client_data, f, separators=(',', ':'))  # Compact format
    
    # Get file size
    import os
    file_size = os.path.getsize("data/frame_data_client.json")
    file_size_mb = file_size / (1024 * 1024)
    
    print(f"✅ Export complete!")
    print(f"📁 File: data/frame_data_client.json")
    print(f"📊 Size: {file_size_mb:.2f} MB")
    print(f"🎯 Frames: {len(frame_data_cache)}")
    print(f"🏠 Stations: {len(station_metadata)}")

if __name__ == "__main__":
    export_frame_data_to_json()
