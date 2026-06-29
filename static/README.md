# Wave Watch — static build

A dependency-free, server-less port of the Dash app. Plain HTML + Plotly.js +
Leaflet read the same `frame_data_client.json` and run entirely in the browser,
so it can be hosted on any static CDN (Netlify, Vercel, Cloudflare Pages) for free.

## Files

| File | Purpose |
|------|---------|
| `index.html` | Page layout |
| `app.js` | All interactivity (ported from the Dash clientside callbacks) |
| `style.css` | Styling |
| `config.example.js` | Template for `config.js` (committed) |
| `config.js` | Holds the MapTiler key; **git-ignored**, generated at build time |
| `frame_data_client.json` | Frame data; copied from `../assets/` at build time (git-ignored here) |

## MapTiler key

The key ships to the browser and cannot be secret; protect it by **HTTP origin**
instead (MapTiler → Account → Keys → Allowed HTTP Origins) — list the host(s) you
serve from plus `localhost` for local dev.

The key is **never committed**. `config.js` is git-ignored and generated at build
from a `MAPTILER_API_KEY` environment variable (see `scripts/netlify-build.sh`).
Locally, `cp config.example.js config.js` and paste your key.

## Local preview

```bash
cp ../assets/frame_data_client.json frame_data_client.json   # if not already present
python3 -m http.server 8099
# open http://localhost:8099   (use localhost, NOT 127.0.0.1 — origins match by
# exact host, so a key whitelisted for "localhost" won't accept 127.0.0.1)
```

Without a real key in `config.js` the app still runs — only the basemap tiles 403.

## Deploy

Publish this folder to any static host. With the included `netlify.toml`, connect
the repo in Netlify (it reads the config automatically) or drag-and-drop the folder
after running the copy step above. Point your domain at the host via CNAME; HTTPS is
provisioned automatically.
