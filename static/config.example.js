// Template for config.js — DO NOT put the real key here (this file is committed).
//
// config.js itself is git-ignored and is generated two ways:
//   • On Netlify: from the MAPTILER_API_KEY environment variable at build time
//     (see scripts/netlify-build.sh). Set it in Netlify -> Site settings ->
//     Environment variables.
//   • Locally: copy this file to config.js and paste your key for previewing.
//
// The key ships to the browser and cannot be secret; protect it by origin:
// MapTiler -> Account -> Keys -> Allowed HTTP Origins = your domain(s) + localhost
// (use http://localhost:PORT for local preview, NOT 127.0.0.1 — origins match by
// exact host).
window.MAPTILER_API_KEY = "YOUR_MAPTILER_KEY";
