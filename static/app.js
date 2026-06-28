/*
 * Wave Watch — static port of the Dash clientside app.
 * Reads the same assets/frame_data_client.json and drives a Leaflet map plus
 * two Plotly figures entirely in the browser. No server / no callbacks.
 */
(function () {
    "use strict";

    // ---- Constants (ported from wave_propagation_clientside_app.py) ----------
    const STATION_ORDER = ["Midway", "Wake Island", "Nawiliwili", "Honolulu", "Kahului", "Kawaihae", "Hilo"];
    const DISTANCES = [3262.37, 3728.95, 4815.29, 4963.23, 5084.13, 5200.53, 5275.16];
    const STATION_COLORS = ["#636EFA", "#EF553B", "#00CC96", "#C490FD", "#FFA15A", "#1BD3F3", "#FF6692"];

    // Coordinates pre-transformed to the Western Pacific view (lon shifted past -180)
    const STATION_LATS = [28.211666, 19.290556, 21.9544, 21.303333, 20.894945, 20.0366, 19.730278];
    const STATION_LONS = [-177.36, -193.3825, -159.3561, -157.86453, -156.469, -155.8294, -155.05556];
    const EPICENTER = [52.473, -199.604];
    const BOUNDS = [[2.635789, -209.882813], [55.578345, -116.367188]];

    const Y_RANGE = [-2, 3];
    const X_MIN = Math.min.apply(null, DISTANCES);
    const X_MAX = Math.max.apply(null, DISTANCES);
    const TOTAL_FRAMES = 1476;

    const mapKey = window.MAPTILER_API_KEY || "";
    const tileUrl = "https://api.maptiler.com/maps/ocean/256/{z}/{x}/{y}.png?key=" + mapKey;
    const tileAttribution =
        '<a href="https://www.maptiler.com/copyright/" target="_blank">&copy; MapTiler</a> ' +
        '<a href="https://www.openstreetmap.org/copyright" target="_blank">&copy; OpenStreetMap contributors</a>';

    // ---- Runtime state -------------------------------------------------------
    let frameData = null;          // parsed frames object
    let currentFrame = 0;
    let timezoneMode = "UTC";      // "UTC" | "HST"
    let playTimer = null;          // setInterval handle
    let stationMarkers = [];       // Leaflet CircleMarkers, updated in place
    let tsTracesBuilt = false;     // timeseries traces are static — build once

    // ---- DOM refs ------------------------------------------------------------
    const els = {
        play: document.getElementById("play-pause-btn"),
        speed: document.getElementById("speed-dropdown"),
        clock: document.getElementById("timeline-clock"),
        tz: document.getElementById("timezone-toggle"),
        slider: document.getElementById("frame-slider"),
        marks: document.getElementById("slider-marks"),
    };

    // ===========================================================================
    //  Map
    // ===========================================================================
    const map = L.map("bathymetry-map", { worldCopyJump: true });
    map.fitBounds(BOUNDS);

    L.tileLayer(tileUrl, { attribution: tileAttribution, maxZoom: 18 }).addTo(map);

    // Earthquake epicenter
    L.circleMarker(EPICENTER, {
        radius: 15, color: "darkred", weight: 4, fillColor: "red", fillOpacity: 0.9,
    }).bindTooltip("🌋 EARTHQUAKE EPICENTER\n29 July 2025, 23:24 UTC\nEpicenter: 0 km").addTo(map);

    // Station markers (created once, restyled per frame)
    for (let i = 0; i < STATION_ORDER.length; i++) {
        const m = L.circleMarker([STATION_LATS[i], STATION_LONS[i]], {
            radius: 8, color: "white", weight: 2, fillColor: STATION_COLORS[i], fillOpacity: 0.7,
        }).bindTooltip(STATION_ORDER[i] + ": " + Math.round(DISTANCES[i]) + " km from epicenter, Loading...");
        m.addTo(map);
        stationMarkers.push(m);
    }

    function updateMap(waveValues) {
        for (let i = 0; i < waveValues.length; i++) {
            const waveDelta = Math.round(waveValues[i] * 1000) / 1000;
            const mag = Math.abs(waveDelta);

            const sizeFactor = Math.min(1.0, mag / 0.3);
            const radius = 4 + 8 * Math.sqrt(sizeFactor);

            const opacityFactor = Math.min(1.0, mag / 0.2);
            const opacity = 0.3 + 0.7 * opacityFactor;

            const m = stationMarkers[i];
            m.setRadius(radius);
            m.setStyle({ fillOpacity: opacity });
            m.setTooltipContent(
                STATION_ORDER[i] + ": " + Math.round(DISTANCES[i]) + " km from epicenter, " +
                (waveDelta >= 0 ? "+" : "") + waveDelta.toFixed(3) + " m wave Δ"
            );
        }
    }

    // ===========================================================================
    //  Wave propagation graph (amplitude vs distance)
    // ===========================================================================
    function waveLayout() {
        const shapes = [{
            type: "line", x0: X_MIN, x1: X_MAX, y0: 0, y1: 0,
            line: { color: "gray", width: 1, dash: "dot" }, layer: "below",
        }];
        DISTANCES.forEach(function (d) {
            shapes.push({
                type: "line", x0: d, x1: d, y0: Y_RANGE[0], y1: Y_RANGE[1],
                line: { color: "gray", width: 1, dash: "dash" }, layer: "below",
            });
        });

        const annotations = STATION_ORDER.map(function (station, i) {
            const level = ["Honolulu", "Kawaihae"].includes(station) ? 1 : 0;
            return {
                x: DISTANCES[i], y: 1.05 + 0.06 * level, yref: "paper",
                text: station, showarrow: true, arrowhead: 2, arrowsize: 0.8,
                arrowwidth: 1, arrowcolor: "darkgray", ax: 0, ay: -15 - 5 * level,
                yanchor: "bottom", textangle: 0,
                font: { size: 9, color: "black", family: "Arial, sans-serif" },
                bgcolor: "rgba(255,255,255,0.95)", bordercolor: "darkgray",
                borderwidth: 1, borderpad: 2,
            };
        });

        return {
            title: { text: "Wave Amplitude vs Distance from Epicenter", font: { size: 16, color: "#2c3e50" } },
            xaxis: { title: { text: "Distance from Epicenter (km)" }, range: [X_MIN, X_MAX], fixedrange: true },
            yaxis: { title: { text: "Δ Wave Height (m)" }, range: Y_RANGE, fixedrange: true, zeroline: false, autorange: false },
            height: 400, plot_bgcolor: "white", paper_bgcolor: "white",
            margin: { t: 120, b: 40, l: 60, r: 20 }, showlegend: false,
            shapes: shapes, annotations: annotations,
        };
    }

    function initWaveGraph() {
        const trace = {
            x: DISTANCES, y: DISTANCES.map(function () { return 0; }),
            type: "scatter", mode: "lines+markers",
            line: { color: "firebrick", width: 3 }, marker: { size: 10, color: "firebrick" },
            showlegend: false,
            hovertemplate: "<b>%{text}</b><br>Distance: %{x:.0f} km<br>Wave Δ: %{y:+.3f} m<extra></extra>",
            text: STATION_ORDER,
        };
        Plotly.newPlot("wave-graph", [trace], waveLayout(), { displayModeBar: false, responsive: true });
    }

    function updateWaveGraph(waveValues) {
        const rounded = waveValues.map(function (v) { return Math.round(v * 1000) / 1000; });
        Plotly.restyle("wave-graph", { y: [rounded] }, [0]);
    }

    // ===========================================================================
    //  Time series graph (7 stacked subplots, traces static)
    // ===========================================================================
    function timeseriesLayout() {
        const n = STATION_ORDER.length;
        const spacing = 0.02;
        const h = (1 - spacing * (n - 1)) / n;

        const layout = {
            height: 600,
            title: { text: "Wave Height Anomalies Over Time", font: { size: 16, color: "#2c3e50" } },
            margin: { t: 50, b: 60, l: 80, r: 20 },
            plot_bgcolor: "white", paper_bgcolor: "white",
            showlegend: false, shapes: [], annotations: [],
        };

        for (let i = 0; i < n; i++) {
            const top = 1 - i * (h + spacing);
            const bottom = top - h;
            const xa = "xaxis" + (i + 1);
            const ya = "yaxis" + (i + 1);

            layout[ya] = {
                domain: [bottom, top], range: Y_RANGE, fixedrange: true,
                zeroline: false, showgrid: true, gridcolor: "#f0f0f0",
                anchor: "x" + (i + 1),
                title: i === Math.ceil(n / 2) - 1 ? "Δ Wave Height (m)" : "",
            };
            layout[xa] = {
                domain: [0, 1], anchor: "y" + (i + 1),
                showgrid: true, gridcolor: "#f0f0f0",
                showticklabels: i === n - 1,
                title: i === n - 1 ? "Time (UTC)" : "",
            };

            // Subplot title
            layout.annotations.push({
                text: STATION_ORDER[i], showarrow: false,
                x: 0.5, y: top, xref: "paper", yref: "paper",
                xanchor: "center", yanchor: "bottom",
                font: { size: 12, color: "#2c3e50" },
            });
        }
        return layout;
    }

    function buildTimeseriesTraces() {
        const n = STATION_ORDER.length;
        const frameKeys = Object.keys(frameData);
        const traces = [];
        for (let i = 0; i < n; i++) {
            const x = [];
            const y = [];
            frameKeys.forEach(function (k) {
                const f = frameData[k];
                if (f.timestamp && f.wave_values && f.wave_values[i] !== undefined) {
                    x.push(f.timestamp);
                    y.push(f.wave_values[i]);
                }
            });
            traces.push({
                x: x, y: y, type: "scatter", mode: "lines",
                name: STATION_ORDER[i], showlegend: false,
                line: { width: 2, color: STATION_COLORS[i] },
                xaxis: "x" + (i + 1), yaxis: "y" + (i + 1),
            });
        }
        return traces;
    }

    function indicatorShapes(timestamp) {
        const shapes = [];
        for (let i = 0; i < STATION_ORDER.length; i++) {
            shapes.push({
                type: "line", xref: "x" + (i + 1), yref: "y" + (i + 1),
                x0: timestamp, x1: timestamp, y0: -1, y1: 1,
                line: { color: "blue", width: 2, dash: "dot" }, layer: "above",
            });
        }
        return shapes;
    }

    function initTimeseriesGraph() {
        const layout = timeseriesLayout();
        layout.shapes = indicatorShapes(frameData["0"].timestamp);
        Plotly.newPlot("timeseries-graph", buildTimeseriesTraces(), layout, { displayModeBar: false, responsive: true });
        tsTracesBuilt = true;
    }

    function updateTimeseriesGraph(timestamp) {
        // Only the indicator lines move — relayout shapes, leave the static traces alone.
        Plotly.relayout("timeseries-graph", { shapes: indicatorShapes(timestamp) });
    }

    // ===========================================================================
    //  Clock + slider marks
    // ===========================================================================
    function formatClock(timestamp) {
        const t = new Date(timestamp + "Z"); // ensure UTC interpretation
        if (timezoneMode === "HST") {
            const hst = new Date(t.getTime() - 10 * 3600 * 1000);
            return hst.toISOString().slice(0, 16).replace("T", " ") + " HST";
        }
        return t.toISOString().slice(0, 16).replace("T", " ") + " UTC";
    }

    function buildSliderMarks() {
        const marks = {};
        for (let i = 0; i < TOTAL_FRAMES; i += 180) {
            marks[i] = (i / 60).toFixed(0) + "h";
        }
        marks[0] = "🌋EQ";
        marks[245] = "📍M";
        marks[355] = "📍H";

        els.marks.innerHTML = "";
        Object.keys(marks).forEach(function (k) {
            const span = document.createElement("span");
            span.textContent = marks[k];
            span.style.left = (100 * k / (TOTAL_FRAMES - 1)) + "%";
            els.marks.appendChild(span);
        });
    }

    // ===========================================================================
    //  Frame update (the single per-frame entry point)
    // ===========================================================================
    function showFrame(index) {
        currentFrame = index;
        const f = frameData[index.toString()];
        if (!f) return;

        updateMap(f.wave_values);
        updateWaveGraph(f.wave_values);
        updateTimeseriesGraph(f.timestamp);
        els.clock.textContent = formatClock(f.timestamp);

        if (els.slider.value !== String(index)) els.slider.value = index;
    }

    // ===========================================================================
    //  Playback
    // ===========================================================================
    function isPlaying() { return playTimer !== null; }

    function play() {
        if (isPlaying()) return;
        const interval = parseInt(els.speed.value, 10) || 65;
        playTimer = setInterval(function () {
            showFrame((currentFrame + 1) % TOTAL_FRAMES);
        }, interval);
        els.play.textContent = "⏸️ Pause";
        els.play.classList.add("playing");
    }

    function pause() {
        if (!isPlaying()) return;
        clearInterval(playTimer);
        playTimer = null;
        els.play.textContent = "▶️ Play";
        els.play.classList.remove("playing");
    }

    function togglePlay() { isPlaying() ? pause() : play(); }

    // ===========================================================================
    //  Event wiring
    // ===========================================================================
    els.play.addEventListener("click", togglePlay);

    els.speed.addEventListener("change", function () {
        if (isPlaying()) { pause(); play(); } // restart timer at new rate
    });

    els.slider.addEventListener("input", function () {
        showFrame(parseInt(els.slider.value, 10) || 0);
    });

    els.tz.addEventListener("click", function () {
        timezoneMode = timezoneMode === "HST" ? "UTC" : "HST";
        els.tz.textContent = timezoneMode === "HST" ? "Show UTC" : "Show HST";
        if (frameData) els.clock.textContent = formatClock(frameData[currentFrame.toString()].timestamp);
    });

    document.addEventListener("keydown", function (e) {
        if (e.key === " ") {
            e.preventDefault();
            togglePlay();
        } else if (e.key === "ArrowRight") {
            e.preventDefault();
            pause();
            showFrame((currentFrame + 1) % TOTAL_FRAMES);
        } else if (e.key === "ArrowLeft") {
            e.preventDefault();
            pause();
            showFrame((currentFrame - 1 + TOTAL_FRAMES) % TOTAL_FRAMES);
        } else if (e.key === "ArrowUp" || e.key === "ArrowDown") {
            e.preventDefault();
            const opts = Array.from(els.speed.options);
            let idx = els.speed.selectedIndex;
            idx = e.key === "ArrowUp" ? Math.max(0, idx - 1) : Math.min(opts.length - 1, idx + 1);
            els.speed.selectedIndex = idx;
            els.speed.dispatchEvent(new Event("change"));
        }
    });

    // ===========================================================================
    //  Boot
    // ===========================================================================
    if (mapKey === "" || mapKey === "YOUR_MAPTILER_KEY") {
        console.warn("MapTiler key not set — basemap tiles will fail. Edit config.js.");
    }

    initWaveGraph();

    fetch("frame_data_client.json")
        .then(function (res) {
            if (!res.ok) throw new Error("HTTP " + res.status);
            return res.json();
        })
        .then(function (data) {
            frameData = data.frames;
            console.log("✅ Loaded " + Object.keys(frameData).length + " frames");
            initTimeseriesGraph();
            buildSliderMarks();
            showFrame(0);
            play(); // autostart
        })
        .catch(function (err) {
            console.error("❌ Error loading frame data:", err);
            els.clock.textContent = "Data load failed";
        });
})();
