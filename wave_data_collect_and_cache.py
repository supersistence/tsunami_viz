
import pandas as pd
import numpy as np
import plotly.express as px
import requests
from datetime import datetime, timedelta, timezone
from math import radians, cos, sin, asin, sqrt
import os
import pickle
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Define full station list
stations = {
    "Nawiliwili": {"id": "1611400", "name": "Nawiliwili", "lat": 21.9544, "lon": -159.3561},
    "Honolulu": {"id": "1612340", "name": "Honolulu", "lat": 21.303333, "lon": -157.86453},
    "Pearl Harbor": {"id": "1612401", "name": "Pearl Harbor", "lat": 21.3675, "lon": -157.9639},
    "Mokuoloe": {"id": "1612480", "name": "Mokuoloe", "lat": 21.433056, "lon": -157.79},
    "Kahului": {"id": "1615680", "name": "Kahului, Kahului Harbor", "lat": 20.894945, "lon": -156.469},
    "Kawaihae": {"id": "1617433", "name": "Kawaihae", "lat": 20.0366, "lon": -155.8294},
    "Hilo": {"id": "1617760", "name": "Hilo, Hilo Bay, Kuhio Bay", "lat": 19.730278, "lon": -155.05556},
    "Midway": {"id": "1619910", "name": "Sand Island, Midway Islands", "lat": 28.211666, "lon": -177.36},
    "Apra Harbor": {"id": "1630000", "name": "Apra Harbor, Guam", "lat": 13.443389, "lon": 144.65636},
    "Pago Bay": {"id": "1631428", "name": "Pago Bay, Guam", "lat": 13.428333, "lon": 144.79889},
    "Pago Pago": {"id": "1770000", "name": "Pago Pago, American Samoa", "lat": -14.28, "lon": -170.69},
    "Kwajalein": {"id": "1820000", "name": "Kwajalein, Marshall Islands", "lat": 8.731667, "lon": 167.73611},
    "Wake Island": {"id": "1890000", "name": "Wake Island, Pacific Ocean", "lat": 19.290556, "lon": 166.6175}
}

epicenter_lat, epicenter_lon = 52.473, 160.396

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))

# Fetch observed and predicted water levels
fetch_cache = {}
def fetch_data(station_id, product):
    cache_key = (station_id, product, 'recent')
    if cache_key in fetch_cache:
        logging.info(f"Cache hit for {cache_key}")
        return fetch_cache[cache_key].copy()
    try:
        url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
        params = {
            "station": station_id,
            "product": product,
            "date": "recent",
            "datum": "MLLW",
            "interval": "1" if product == "predictions" else None,
            "units": "metric",
            "time_zone": "gmt",
            "format": "json"
        }
        logging.info(f"Fetching {product} for {station_id} from NOAA API with date=recent...")
        response = requests.get(url, params={k: v for k, v in params.items() if v is not None}, timeout=15)
        response.raise_for_status()
        key = "predictions" if product == "predictions" else "data"
        df = pd.DataFrame(response.json().get(key, []))
        fetch_cache[cache_key] = df.copy()
        return df
    except Exception as e:
        logging.error(f"Failed to fetch {product} for {station_id}: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    raw_cache_file = "data/raw_api_cache.pkl"
    restructured_cache_file = "data/restructured_data.pkl"
    raw_data = {}

    # Always fetch fresh data and overwrite cache
    logging.info("Fetching fresh data from NOAA API (date=recent)...")
    for name, meta in stations.items():
        raw_data[name] = {}
        for product in ["one_minute_water_level", "predictions"]:
            raw_data[name][product] = fetch_data(meta["id"], product)
    with open(raw_cache_file, "wb") as f:
        pickle.dump(raw_data, f)
    logging.info(f"Raw API data cached to {raw_cache_file}")

    logging.info("Processing and restructuring data...")
    records = []
    for name, meta in stations.items():
        try:
            obs = raw_data.get(name, {}).get("one_minute_water_level", pd.DataFrame())
            pred = raw_data.get(name, {}).get("predictions", pd.DataFrame())
            if not obs.empty and not pred.empty:
                obs['t'] = pd.to_datetime(obs['t'], errors='coerce')
                obs['v'] = pd.to_numeric(obs['v'], errors='coerce')
                pred['t'] = pd.to_datetime(pred['t'], errors='coerce')
                pred['v'] = pd.to_numeric(pred['v'], errors='coerce')
                merged = pd.merge(obs, pred, on='t', suffixes=('_obs', '_pred'))
                merged['delta'] = merged['v_obs'] - merged['v_pred']
                merged['station'] = name
                merged['distance_km'] = haversine(epicenter_lat, epicenter_lon, meta['lat'], meta['lon'])
                records.append(merged[['t', 'station', 'distance_km', 'delta']])
            else:
                logging.warning(f"No data for station {name}")
        except Exception as e:
            logging.error(f"Error processing station {name}: {e}")
    if records:
        df = pd.concat(records)
        with open(restructured_cache_file, "wb") as f:
            pickle.dump(df, f)
        logging.info(f"Restructured data cached to {restructured_cache_file}")
        # Create and save pivoted DataFrame for Dash app
        df_pivot = df.pivot(index='t', columns='station', values='delta')
        # Compute distances and sort stations
        station_distance = {name: haversine(epicenter_lat, epicenter_lon, meta['lat'], meta['lon']) for name, meta in stations.items()}
        sorted_stations = sorted(df_pivot.columns, key=lambda s: station_distance.get(s, 1e9))
        df_pivot = df_pivot[sorted_stations]
        with open('data/pivoted_wave_data.pkl', 'wb') as f:
            pickle.dump({'df_pivot': df_pivot, 'station_order': sorted_stations, 'station_distance': station_distance}, f)
        logging.info(f"Pivoted data cached to data/pivoted_wave_data.pkl")
    else:
        logging.error("No valid data to process. Exiting.")
        exit(1)
    df['t_str'] = df['t'].dt.strftime('%Y-%m-%d %H:%M')

    logging.info("Data collection, restructuring, and caching complete. Raw data: %s, Restructured data: %s, Pivoted data: %s", raw_cache_file, restructured_cache_file, 'data/pivoted_wave_data.pkl')
