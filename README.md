# 🌊 Tsunami Wave Propagation Visualization

An interactive visualization of tsunami wave propagation across the Pacific
following the [2025 Kamchatka Peninsula earthquake](https://en.wikipedia.org/wiki/2025_Kamchatka_Peninsula_earthquake).
It animates how tsunami waves travel from the epicenter to NOAA monitoring
stations from Midway Atoll to Hilo, Hawaii.

**🌐 Live:** [tsunami.supersistence.org](https://tsunami.supersistence.org)

## Features

- **Real-time animation** of wave propagation over 24+ hours
- **Wave propagation graph** — amplitude vs. distance from the epicenter
- **Per-station time series** of wave-height anomalies
- **Interactive bathymetry map** with dynamic station markers
- **UTC / HST toggle** and keyboard controls (Space = play/pause, ←/→ = step, ↑/↓ = speed)

## Architecture

This is a **fully static, client-side site** — no server or backend at runtime.
Everything renders in the browser from a single precomputed data file.

```
Browser loads index.html
  → Plotly.js + Leaflet (from CDN) + app.js
  → fetches frame_data_client.json (1476 frames, 1-min resolution)
  → renders map, wave graph, and time series entirely client-side
```

Hosted on **Netlify** (static CDN), fronted by **Cloudflare**. Pushing to `main`
triggers an automatic deploy.

### Project structure

```
tsunami_viz/
├── static/                     # The deployed site
│   ├── index.html              #   layout
│   ├── app.js                  #   all interactivity (no framework)
│   ├── style.css
│   └── config.example.js       #   template for the git-ignored config.js
├── assets/
│   └── frame_data_client.json  # animation data (served as-is)
├── scripts/netlify-build.sh    # build: copy data + generate config.js from env
├── netlify.toml                # Netlify build config
├── archive/                    # data-processing pipeline + original Dash app
└── data/                       # intermediate datasets (pickles)
```

## Local development

```bash
cd static
cp ../assets/frame_data_client.json frame_data_client.json   # served as-is
cp config.example.js config.js                               # paste your MapTiler key
python3 -m http.server 8099
# open http://localhost:8099   (use localhost, NOT 127.0.0.1 — see below)
```

See [`static/README.md`](static/README.md) for details.

## MapTiler key

The basemap uses a MapTiler key that necessarily ships to the browser, so it is
**protected by origin** rather than kept secret:
MapTiler → Account → Keys → Allowed HTTP Origins = `*.supersistence.org`, `localhost`.

The key is **never committed**. `static/config.js` is git-ignored and generated at
build time from the `MAPTILER_API_KEY` environment variable (set in Netlify →
Site settings → Environment variables). Locally, copy `config.example.js` to
`config.js` and paste a key. Use `http://localhost` for previews — `127.0.0.1` is a
different origin and is not whitelisted.

## Deployment

Automatic via Netlify on push to `main` (build = `scripts/netlify-build.sh`,
publish dir = `static/`). No manual steps.

## Data

- **Station metadata** — [NOAA CO-OPS Metadata API](https://api.tidesandcurrents.noaa.gov/mdapi/prod/)
- **Observed water levels & predicted tides** — [NOAA CO-OPS API](https://api.tidesandcurrents.noaa.gov/api/prod/)
- **Map tiles** — [MapTiler Ocean theme](https://www.maptiler.com/)

Wave anomaly Δ = observed water level − predicted tide. Distances are great-circle
from the epicenter (52.473°N, 160.396°E).

### Regenerating `frame_data_client.json`

The pipeline that produced the data lives in `archive/scripts/` (historical reference):

```bash
python fetch_station_metadata.py        # station info from NOAA
python wave_data_collect_and_cache.py   # fetch & process wave data
python generate_frame_cache.py          # build animation frames
python export_frame_data_to_json.py     # export client-side JSON
```

## Event details

- **Date/Time:** 29 July 2025, 23:24:52 UTC
- **Epicenter:** 52.473°N, 160.396°E
- **Stations (7):** Midway, Wake Island, Nawiliwili, Honolulu, Kahului, Kawaihae, Hilo (≈5,275 km span)
- **Timeline:** ~24 hours, 1-minute resolution
