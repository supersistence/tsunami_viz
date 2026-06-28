#!/usr/bin/env bash
# Netlify build for the static site.
# 1. Copy the frame data into the publish dir (kept single-sourced in assets/).
# 2. Generate config.js from the MAPTILER_API_KEY env var so the key is never
#    committed to the repo. Set it in Netlify -> Site settings -> Environment variables.
set -euo pipefail

cp assets/frame_data_client.json static/frame_data_client.json

if [ -z "${MAPTILER_API_KEY:-}" ]; then
  echo "WARNING: MAPTILER_API_KEY is not set — basemap tiles will fail." >&2
fi
printf 'window.MAPTILER_API_KEY = "%s";\n' "${MAPTILER_API_KEY:-}" > static/config.js

echo "Build complete: frame data copied, config.js generated."
