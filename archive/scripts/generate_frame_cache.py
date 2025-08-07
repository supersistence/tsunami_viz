#!/usr/bin/env python3
"""
Generate pre-calculated frame data cache for tsunami visualization.
Run this once to create the cache file, then the main app loads it instantly.
"""

import pandas as pd
import pickle
import time

def generate_frame_cache():
    print("🚀 Generating frame data cache...")
    start_time = time.time()
    
    # Load the same data as main app (exact same method)
    with open("data/pivoted_wave_data.pkl", "rb") as f:
        pivoted = pickle.load(f)
    df_pivot = pivoted['df_pivot']  # index: t, columns: station, values: delta
    station_order_orig = pivoted['station_order']
    station_distances = pivoted['station_distance']
    
    # Apply same filtering as main app
    earthquake_time = pd.Timestamp('2025-07-29 23:24:52')
    end_time = pd.Timestamp('2025-07-31 00:00:00')
    df_pivot_filtered = df_pivot[(df_pivot.index >= earthquake_time) & 
                                (df_pivot.index <= end_time)]
    
    # Interpolate and fill missing values (same as main app)
    df_pivot_interp = df_pivot_filtered.interpolate(axis=0).ffill().bfill()
    all_frames = df_pivot_interp.index
    
    # Remove filtered stations (exact same as main app)
    stations_to_remove = ['Pago Pago', 'Kwajalein', 'Apra Harbor', 'Pago Bay', 'Pearl Harbor', 'Mokuoloe']
    for station in stations_to_remove:
        if station in df_pivot_interp.columns:
            df_pivot_interp = df_pivot_interp.drop(columns=[station])
    
    # Update station_order to match filtered data
    station_order = [s for s in station_order_orig if s in df_pivot_interp.columns]
    distances = [station_distances[station] for station in station_order]
    
    print(f"📊 Processing {len(df_pivot_interp)} frames with {len(station_order)} stations...")
    
    # Pre-calculate frame data cache
    frame_data_cache = {}
    
    for i in range(len(df_pivot_interp)):
        # Pre-calculate wave data
        x_values = [float(d) for d in distances]
        wave_values = df_pivot_interp.iloc[i].values.tolist()
        timestamp = all_frames[i]
        
        # Pre-calculate time series shapes (current time markers only)
        timeseries_shapes = []
        # Add current time marker (animated) for all subplots
        for j in range(len(station_order)):
            timeseries_shapes.append({
                "type": "line",
                "xref": f"x{j+1}",
                "yref": f"y{j+1}",
                "x0": timestamp,
                "x1": timestamp,
                "y0": -1,
                "y1": 1,
                "line": {"color": "blue", "width": 2, "dash": "dot"},
                "layer": "above"
            })
        
        frame_data_cache[i] = {
            'x_values': x_values,
            'wave_values': wave_values,
            'timestamp': timestamp,
            'timeseries_shapes': timeseries_shapes
        }
        
        # Progress indicator
        if i % 200 == 0:
            print(f"  ⚡ Processed {i}/{len(df_pivot_interp)} frames...")
    
    # Save cache to disk
    cache_file = 'data/frame_data_cache.pkl'
    with open(cache_file, 'wb') as f:
        pickle.dump(frame_data_cache, f, protocol=pickle.HIGHEST_PROTOCOL)
    
    generation_time = time.time() - start_time
    total_shapes = len(df_pivot_interp) * len(station_order)
    memory_usage = total_shapes * 8 / 1024  # rough estimate in KB
    
    print(f"✅ Cache generation complete!")
    print(f"⏱️  Generation time: {generation_time:.3f}s")
    print(f"📁 Cache file: {cache_file}")
    print(f"🔢 Total shapes: {total_shapes:,}")
    print(f"💾 Estimated size: ~{memory_usage:.1f}KB")
    print(f"\n🚀 Main app startup should now be ~{generation_time*1000:.0f}ms faster!")

if __name__ == "__main__":
    generate_frame_cache()