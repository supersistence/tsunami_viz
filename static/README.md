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

The key ships to the browser and cannot be secret. It is protected by **origin**:
MapTiler → Account → Keys → Allowed HTTP Origins = `*.supersistence.org`, `localhost`.
`tsunami.supersistence.org` matches the wildcard, so production tiles work.

The key is **never committed**. `config.js` is git-ignored and generated at build:

- **On Netlify:** set `MAPTILER_API_KEY` in Site settings → Environment variables.
  `scripts/netlify-build.sh` writes it into `config.js` during the build.
- **Locally:** `cp config.example.js config.js` and paste your key (stays git-ignored).

## Local preview

```bash
cp ../assets/frame_data_client.json frame_data_client.json   # if not already present
python3 -m http.server 8099
# open http://localhost:8099   (use localhost, NOT 127.0.0.1 — only localhost is a
# whitelisted MapTiler origin, and origin matching is by exact host)
```

Without a real key in `config.js` the app still runs — only the basemap tiles 403.

## Deploy to Netlify

Repo root has `netlify.toml` (publish dir = `static/`, build step copies the JSON in).

- **Connect the GitHub repo** in Netlify → it picks up `netlify.toml` automatically, or
- **Drag-and-drop:** run the copy step above, then drop this folder into the Netlify UI.

Then point DNS: add a CNAME for `tsunami.supersistence.org` → your Netlify site.
HTTPS is provisioned automatically — no more certbot renewal.
