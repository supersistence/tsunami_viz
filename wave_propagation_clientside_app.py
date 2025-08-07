import dash
from dash import dcc, html, Input, Output, State, clientside_callback, ClientsideFunction
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import plotly.subplots as sp
import pandas as pd
import dash_leaflet as dl
import os
import numpy as np
import plotly
import time
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("DEBUG: plotly version:", plotly.__version__)
print("DEBUG: dash version:", dash.__version__)

# Start timing app startup
startup_start_time = time.time()

# Load station metadata for coordinates and setup
with open("data/station_metadata.json", "r") as f:
    station_metadata = json.load(f)

print(f"🌊 Loading {len(station_metadata)} stations for client-side app")

# Earthquake epicenter coordinates (2025 Kamchatka Peninsula earthquake)
epicenter_lat, epicenter_lon = 52.473, 160.396

# Earthquake timing: 30 July 2025, at 11:24:52 PETT (29 July 2025, 23:24:52 UTC)
earthquake_time = pd.Timestamp('2025-07-29 23:24:52')  # timezone-naive to match data

# Station setup (from original app)
station_order = ['Midway', 'Wake Island', 'Nawiliwili', 'Honolulu', 'Kahului', 'Kawaihae', 'Hilo']
station_distances = {
    'Midway': 3262.3719497372435,
    'Wake Island': 3728.952004940343, 
    'Nawiliwili': 4815.294231640468,
    'Honolulu': 4963.230141186771,
    'Kahului': 5084.1313461574655,
    'Kawaihae': 5200.5268320141,
    'Hilo': 5275.164460167129
}

distances = [station_distances[s] for s in station_order]

# Hardcoded station coordinates (pre-transformed to Western Pacific view)
station_lats = [28.211666, 19.290556, 21.9544, 21.303333, 20.894945, 20.0366, 19.730278]
station_lons = [-177.36, -193.3825, -159.3561, -157.86453, -156.469, -155.8294, -155.05556]

# Earthquake coordinates (pre-transformed to Western Pacific view)
epicenter_lat, epicenter_lon = 52.473, -199.604

# Calculate optimal bounding box for auto-fit
all_lats = station_lats + [epicenter_lat]
all_lons = station_lons + [epicenter_lon]

min_lat, max_lat = min(all_lats), max(all_lats)
min_lon, max_lon = min(all_lons), max(all_lons)

# Use precise bounds that perfectly frame the Pacific monitoring stations
bounds = [[2.635789, -209.882813], [55.578345, -116.367188]]  # Optimal Pacific view
bounds_min_lat, bounds_min_lon = bounds[0]
bounds_max_lat, bounds_max_lon = bounds[1]

# Calculate center from hardcoded bounds
center_lat = (bounds_min_lat + bounds_max_lat) / 2
center_lon = (bounds_min_lon + bounds_max_lon) / 2

# Use Plotly's exact default color sequence for time series alignment
station_colors = [
    '#636EFA',  # cornflower blue
    '#EF553B',  # bittersweet orange  
    '#00CC96',  # persian green
    '#C490FD',  # lavender
    '#FFA15A',  # light orange
    '#1BD3F3',  # robbins egg blue
    '#FF6692'   # light crimson
]

print(f"🌍 HARDCODED COORDINATES LOADED:")
print(f"   Coordinate range: Lat {min_lat:.1f}° to {max_lat:.1f}° | Lon {min_lon:.1f}° to {max_lon:.1f}°")
print(f"   Hardcoded bounds: Lat {bounds_min_lat:.1f}° to {bounds_max_lat:.1f}° | Lon {bounds_min_lon:.1f}° to {bounds_max_lon:.1f}°")
print(f"   Map center: [{center_lat:.2f}, {center_lon:.2f}]")
print(f"🎨 Using Plotly default colors: {station_colors}")

# Timezone conversion functions
def convert_to_hst(utc_time):
    """Convert UTC time to Hawaii Standard Time (HST)"""
    # HST is UTC-10
    hst_offset = pd.Timedelta(hours=10)
    return utc_time - hst_offset

def format_time_display(time, timezone_mode):
    """Format time for display based on timezone mode"""
    if timezone_mode == 'HST':
        hst_time = convert_to_hst(time)
        return hst_time.strftime('%Y-%m-%d %H:%M HST')
    else:  # UTC
        return time.strftime('%Y-%m-%d %H:%M UTC')

# Create initial empty figures - these will be populated by client-side code
initial_wave_fig = go.Figure()
initial_wave_fig.add_trace(go.Scatter(
    x=distances,
    y=[0] * len(distances),
    mode='lines+markers',
    line=dict(color='firebrick', width=3),
    marker=dict(size=10, color='firebrick'),
    name='Wave Δ',
    showlegend=False
))

# Add baseline and station vertical lines
initial_wave_fig.add_shape(
    type="line",
    x0=min(distances), x1=max(distances),
    y0=0, y1=0,
    line=dict(color="gray", width=1, dash="dot"),
    layer="below"
)

for x in distances:
    initial_wave_fig.add_shape(
        type="line",
        x0=x, x1=x,
        y0=-2, y1=3,
        line=dict(color="gray", width=1, dash="dash"),
        layer="below"
    )

initial_wave_fig.update_layout(
    title=dict(
        text="Wave Amplitude vs Distance from Epicenter",
        font=dict(size=16, color='#2c3e50')
    ),
    xaxis_title="Distance from Epicenter (km)",
    yaxis_title="Δ Wave Height (m)",
    yaxis=dict(range=[-2, 3], fixedrange=True, zeroline=False, autorange=False),
    xaxis=dict(range=[min(distances), max(distances)], fixedrange=True),
    height=400,
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(t=120, b=40, l=60, r=20),
    showlegend=False
)

# Create initial timeseries figure
initial_timeseries_fig = sp.make_subplots(
    rows=len(station_order), cols=1, shared_xaxes=True,
    subplot_titles=station_order, vertical_spacing=0.01
)

# Add empty traces for each station
for i, station in enumerate(station_order):
    initial_timeseries_fig.add_trace(
        go.Scatter(
            x=[],
            y=[],
            mode='lines',
            name=station,
            showlegend=False,
            line=dict(width=2, color=station_colors[i])
        ),
        row=i+1, col=1
    )

initial_timeseries_fig.update_layout(
    height=600,
    title=dict(
        text="Wave Height Anomalies Over Time",
        font=dict(size=16, color='#2c3e50')
    ),
    margin=dict(t=50, b=60, l=80, r=20),
    plot_bgcolor="white",
    paper_bgcolor="white"
)

initial_timeseries_fig.update_xaxes(
    title_text="Time (UTC)",
    title_standoff=1,
    row=len(station_order), col=1
)

# Initialize Dash app
app = dash.Dash(__name__, title="Wave Watch")

# Add custom favicon using wave emoji
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Wave Watch</title>
        <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🌊</text></svg>">
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# App layout - matches original exactly
app.layout = html.Div([
    # Hidden div to store the frame data
    html.Div(id="frame-data-store", style={"display": "none"}),
    
    # Keyboard event listener
    html.Div(id="keyboard-listener", tabIndex=0, style={'outline': 'none'}),
    
    # Header Section
    html.Div([
        html.H1("🌊 Wave Watch: Kamchatka to Hawai'i", 
                style={'margin': '0', 'color': '#2c3e50', 'fontSize': '2.5rem', 'fontWeight': 'bold'}),
        html.P("Interactive visualization of tsunami waves following the 2025 Kamchatka Peninsula earthquake",
               style={'margin': '10px 0 5px 0', 'color': '#7f8c8d', 'fontSize': '1.1rem'}),
        html.P("⚠️ Earthquake: 29 July 2025, 23:24:52 UTC | 📍 Epicenter: 52.473°N, 160.396°E | ⏰ Timeline: ~24 hrs post-quake | ⏱️ Frequency: 1-minute intervals",
               style={'margin': '0', 'color': '#e74c3c', 'fontSize': '1.0rem', 'fontWeight': 'bold'})
    ], style={'textAlign': 'center', 'padding': '20px', 'background': 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)', 
              'borderRadius': '10px', 'marginBottom': '25px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}),
    
    # Master Control Panel
    html.Div([
        html.H3("🎮 Animation Controls", style={'margin': '0 0 15px 0', 'color': '#34495e', 'fontSize': '1.3rem'}),
        html.P("Explore tsunami wave propagation following the 2025 Kamchatka earthquake through three synchronized views: geographic map, wave front progression, and station time series record.",
               style={'color': '#2c3e50', 'fontSize': '1.0rem', 'marginBottom': '10px', 'fontWeight': 'normal'}),
        html.P("Hover for station details, drag timeline for navigation, and use keyboard shortcuts (Space=play/pause, arrows=step) - all panels update simultaneously with instant client-side performance.",
               style={'color': '#7f8c8d', 'fontSize': '0.9rem', 'marginBottom': '15px', 'fontStyle': 'italic'}),
        html.Div([
            html.Div([
                html.Button('▶️ Play', id='play-pause-btn', n_clicks=0, 
                           style={'padding': '12px 24px', 'fontSize': '16px', 'fontWeight': 'bold', 
                                 'backgroundColor': '#27ae60', 'color': 'white', 'border': 'none', 
                                 'borderRadius': '8px', 'cursor': 'pointer', 'marginRight': '20px',
                                 'boxShadow': '0 3px 6px rgba(0,0,0,0.2)', 'transition': 'all 0.3s'},
                           title="Click to start/stop animation"),

                html.Span("Speed: ", style={'fontSize': '16px', 'fontWeight': 'bold', 'color': '#2c3e50', 'marginRight': '10px'}),
                dcc.Dropdown(
                    id='speed-dropdown',
                    options=[
                        {'label': '🐌 Slow', 'value': 50},
                        {'label': '🚶 Normal', 'value': 20},
                        {'label': '🏃 Fast', 'value': 10}
                    ],
                    value=20,
                    style={'width': '120px', 'marginLeft': '10px'},
                    clearable=False
                ),
                html.Div([
                    html.Span("🕐 ", style={'fontSize': '16px', 'marginLeft': '30px', 'marginRight': '5px'}),
                    html.Span("", id="timeline-clock", style={
                        'fontSize': '16px', 'fontWeight': 'bold', 'color': '#2c3e50',
                        'backgroundColor': '#ecf0f1', 'padding': '8px 12px', 'borderRadius': '6px',
                        'border': '2px solid #bdc3c7', 'fontFamily': 'monospace'
                    }),
                    html.Button('🔄 UTC', id='timezone-toggle', n_clicks=0,
                               style={'padding': '8px 16px', 'fontSize': '14px', 'fontWeight': 'bold',
                                     'backgroundColor': '#3498db', 'color': 'white', 'border': 'none',
                                     'borderRadius': '6px', 'cursor': 'pointer', 'marginLeft': '20px',
                                     'boxShadow': '0 2px 4px rgba(0,0,0,0.2)', 'transition': 'all 0.3s'})
                ], style={'display': 'flex', 'alignItems': 'center'})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),
            
            html.Div([
                html.Label("Timeline Navigation: 🌋EQ = Earthquake, 📍M = Midway, 📍H = Hawaii", style={'fontSize': '14px', 'fontWeight': 'bold', 'color': '#2c3e50', 'marginBottom': '10px', 'display': 'block'}),
                html.P("⌨️ Keyboard: Space=Play/Pause, ←/→=Manual step, ↑/↓=Speed", style={'fontSize': '11px', 'color': '#95a5a6', 'margin': '2px 0', 'fontStyle': 'italic'}),
                dcc.Slider(
                    id="frame-slider",
                    min=0,
                    max=1475,  # Will be updated by client-side code
                    value=0,
                    step=1,
                    updatemode='drag',
                    tooltip={"placement": "bottom", "always_visible": False},
                    marks={}  # Will be populated by client-side code
                ),
            ], style={'marginTop': '10px'})
        ])
    ], style={'background': '#ffffff', 'padding': '25px', 'borderRadius': '10px', 'marginBottom': '25px',
              'boxShadow': '0 4px 8px rgba(0,0,0,0.1)', 'border': '1px solid #e1e8ed'}),
    
    # Visualization Grid - Top Row: Map and Wave Propagation
    html.Div([
        # Left Column - Geographic Overview
        html.Div([
            html.H3("🗺️ Geographic Overview", style={'color': '#2c3e50', 'marginBottom': '15px', 'fontSize': '1.2rem'}),
            html.P("Interactive bathymetry map showing earthquake epicenter (red) and monitoring stations (colored circles) with real-time wave amplitude data.",
                   style={'color': '#7f8c8d', 'fontSize': '0.9rem', 'marginBottom': '15px', 'fontStyle': 'italic'}),
            dl.Map(
                id="bathymetry-map",
                style={'width': '100%', 'height': '400px'},
                center=[center_lat, center_lon],
                zoom=3,
                bounds=[[bounds_min_lat, bounds_min_lon], [bounds_max_lat, bounds_max_lon]],
                worldCopyJump=True,
                children=[
                    # MapTiler Ocean bathymetry tile layer
                    dl.TileLayer(
                        url=f"https://api.maptiler.com/maps/ocean/256/{{z}}/{{x}}/{{y}}.png?key={os.environ.get('MAPTILER_API_KEY', '')}",
                        attribution='<a href="https://www.maptiler.com/copyright/" target="_blank">&copy; MapTiler</a> <a href="https://www.openstreetmap.org/copyright" target="_blank">&copy; OpenStreetMap contributors</a>',
                        maxZoom=18
                    ),
                    # Earthquake epicenter - large and prominent
                    dl.CircleMarker(
                        center=[epicenter_lat, epicenter_lon],
                        radius=15,
                        color='darkred',
                        weight=4,
                        fillColor='red',
                        fillOpacity=0.9,
                        children=[dl.Tooltip("🌋 EARTHQUAKE EPICENTER\n29 July 2025, 23:24 UTC")]
                    ),
                    # Initial station markers
                    *[dl.CircleMarker(
                        center=[station_lats[i], station_lons[i]],
                        radius=8,
                        color='white',
                        weight=2,
                        fillColor=station_colors[i],
                        fillOpacity=0.7,
                        children=[dl.Tooltip(f"{station_order[i]}: Loading...")]
                    ) for i in range(len(station_order))]
                ]
            ),
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingRight': '2%'}),
        
        # Right Column - Wave Propagation Analysis
        html.Div([
            html.H3("📊 Wave Propagation", style={'color': '#2c3e50', 'marginBottom': '15px', 'fontSize': '1.2rem'}),
            html.P("Oscilloscope-style visualization showing wave front progression across all stations, with distance from epicenter on X-axis and wave height anomaly on Y-axis.",
                   style={'color': '#7f8c8d', 'fontSize': '0.9rem', 'marginBottom': '15px', 'fontStyle': 'italic'}),
            dcc.Graph(id="wave-graph", figure=initial_wave_fig, style={'height': '400px'}),
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingLeft': '2%'}),
    ]),
    
    # Bottom Row - Station Time Series (Full Width)
    html.Div([
        html.H3("📈 Station Time Series", style={'color': '#2c3e50', 'marginTop': '30px', 'marginBottom': '15px', 'fontSize': '1.2rem'}),
        html.P("Individual wave height records for each monitoring station over time, showing how tsunami waves arrive at different locations across the Pacific.",
               style={'color': '#7f8c8d', 'fontSize': '0.9rem', 'marginBottom': '15px', 'fontStyle': 'italic'}),
        dcc.Graph(id="timeseries-graph", figure=initial_timeseries_fig, style={'height': '600px'}),
    ], style={'width': '100%', 'marginTop': '20px'}),
    
    # Footer Info
    html.Div([
        html.P([
           "📊 Data Source: ",
            html.A("NOAA CO-OPS API", href="https://tidesandcurrents.noaa.gov/web_services_info.html", target="_blank")
        ], style={'margin': '0', 'color': '#95a5a6', 'fontSize': '0.9rem', 'textAlign': 'center'})
    ], style={'marginTop': '30px', 'padding': '15px', 'background': '#ecf0f1', 'borderRadius': '8px'}),
    
    # Animation interval component
    dcc.Interval(id="animation-interval", interval=20, n_intervals=0, disabled=True),
    
    # Hidden divs for state management
    html.Div(id="current-frame", children="0", style={"display": "none"}),
    html.Div(id="total-frames", children="1476", style={"display": "none"}),
    
], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '20px', 'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#f8f9fa'})

# Client-side callback to load frame data once at startup
app.clientside_callback(
    """
    function(id) {
        if (window.tsunamiFrameData) {
            return JSON.stringify({status: 'already_loaded', frames: Object.keys(window.tsunamiFrameData.frames).length});
        }
        
        console.log('🔄 Loading tsunami frame data...');
        
        // Use fetch with .then() instead of async/await for better Dash compatibility
        fetch('/assets/frame_data_client.json')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                window.tsunamiFrameData = data;
                
                // Also store some useful derived data
                window.tsunamiStationOrder = ['Midway', 'Wake Island', 'Nawiliwili', 'Honolulu', 'Kahului', 'Kawaihae', 'Hilo'];
                window.tsunamiDistances = [3262.37, 3728.95, 4815.29, 4963.23, 5084.13, 5200.53, 5275.16];
                window.tsunamiStationColors = ['#636EFA', '#EF553B', '#00CC96', '#C490FD', '#FFA15A', '#1BD3F3', '#FF6692'];
                
                // Store MapTiler API key for client-side use
                window.MAPTILER_API_KEY = '""" + os.environ.get('MAPTILER_API_KEY', '') + """';
                
                console.log(`✅ Loaded ${Object.keys(data.frames).length} frames`);
                console.log('🎯 Frame data structure:', Object.keys(data.frames['0'] || {}));
                
                // Trigger a callback update by setting a flag
                window.tsunamiDataLoaded = true;
            })
            .catch(error => {
                console.error('❌ Error loading frame data:', error);
                window.tsunamiDataLoadError = error.message;
            });
        
        return JSON.stringify({status: 'loading'});
    }
    """,
    Output('frame-data-store', 'children'),
    Input('frame-data-store', 'id')
)

# Client-side callback for play/pause functionality
app.clientside_callback(
    """
    function(n_clicks, speed_value, is_disabled) {
        if (n_clicks === null || n_clicks === 0) {
            return [true, speed_value || 20, "▶️ Play", {
                'padding': '12px 24px', 'fontSize': '16px', 'fontWeight': 'bold', 
                'backgroundColor': '#27ae60', 'color': 'white', 'border': 'none', 
                'borderRadius': '8px', 'cursor': 'pointer', 'marginRight': '20px',
                'boxShadow': '0 3px 6px rgba(0,0,0,0.2)', 'transition': 'all 0.3s'
            }];
        }
        
        const speed = speed_value || 20;
        
        if (is_disabled) {
            // Currently paused, start playing
            return [false, speed, "⏸️ Pause", {
                'padding': '12px 24px', 'fontSize': '16px', 'fontWeight': 'bold', 
                'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 
                'borderRadius': '8px', 'cursor': 'pointer', 'marginRight': '20px',
                'boxShadow': '0 3px 6px rgba(0,0,0,0.2)', 'transition': 'all 0.3s'
            }];
        } else {
            // Currently playing, pause
            return [true, speed, "▶️ Play", {
                'padding': '12px 24px', 'fontSize': '16px', 'fontWeight': 'bold', 
                'backgroundColor': '#27ae60', 'color': 'white', 'border': 'none', 
                'borderRadius': '8px', 'cursor': 'pointer', 'marginRight': '20px',
                'boxShadow': '0 3px 6px rgba(0,0,0,0.2)', 'transition': 'all 0.3s'
            }];
        }
    }
    """,
    [Output("animation-interval", "disabled"), 
     Output("animation-interval", "interval"), 
     Output("play-pause-btn", "children"), 
     Output("play-pause-btn", "style")],
    [Input("play-pause-btn", "n_clicks"), Input("speed-dropdown", "value")],
    [State("animation-interval", "disabled")]
)

# Client-side callback for frame advancement during animation
app.clientside_callback(
    """
    function(n_intervals, current_frame, total_frames) {
        const frameNum = parseInt(current_frame) || 0;
        const totalFrames = parseInt(total_frames) || 1476;
        const nextFrame = (frameNum + 1) % totalFrames;
        return nextFrame;
    }
    """,
    Output("frame-slider", "value"),
    [Input("animation-interval", "n_intervals")],
    [State("frame-slider", "value"), State("total-frames", "children")]
)

# Main client-side callback to update all visualizations
app.clientside_callback(
    """
    function(frame_index, frame_data_json, timezone_clicks) {
        // Define proper empty figures to return when data isn't loaded
        const emptyWaveFig = {
            data: [],
            layout: {
                title: {
                    text: 'Loading Wave Data...',
                    font: {size: 16, color: '#2c3e50'}
                },
                xaxis: {title: 'Distance from Epicenter (km)'},
                yaxis: {title: 'Δ Wave Height (m)', range: [-2, 3]},
                height: 400,
                plot_bgcolor: 'white',
                paper_bgcolor: 'white',
                margin: {t: 120, b: 40, l: 60, r: 20}
            }
        };
        
        const emptyTimeseriesFig = {
            data: [],
            layout: {
                title: {
                    text: 'Loading Station Time Series...',
                    font: {size: 16, color: '#2c3e50'}
                },
                height: 600,
                plot_bgcolor: 'white',
                paper_bgcolor: 'white',
                margin: {t: 50, b: 60, l: 80, r: 20}
            }
        };
        
        if (!window.tsunamiFrameData || !window.tsunamiFrameData.frames) {
            return [[], emptyWaveFig, emptyTimeseriesFig, "Loading...", "🔄 UTC", {}];
        }
        
        const frameData = window.tsunamiFrameData.frames[frame_index.toString()];
        if (!frameData) {
            return [[], emptyWaveFig, emptyTimeseriesFig, "Frame not found", "🔄 UTC", {}];
        }
        
        const stationOrder = window.tsunamiStationOrder;
        const distances = window.tsunamiDistances;
        const stationColors = window.tsunamiStationColors;
        
        // Determine timezone mode
        const timezoneMode = (timezone_clicks && timezone_clicks % 2 === 1) ? 'HST' : 'UTC';
        
        // Update map with dynamic station markers
        const stationMarkers = [];
        for (let i = 0; i < frameData.wave_values.length; i++) {
            const waveDelta = frameData.wave_values[i];
            const waveMagnitude = Math.abs(waveDelta);
            
            // Improved circle sizing
            const baseSize = 4;
            const maxAdditionalSize = 8;
            const sizeFactor = Math.min(1.0, waveMagnitude / 0.3);
            const size = baseSize + (maxAdditionalSize * Math.sqrt(sizeFactor));
            
            // Enhanced opacity
            const opacityFactor = Math.min(1.0, waveMagnitude / 0.2);
            const opacity = 0.3 + (0.7 * opacityFactor);
            
            stationMarkers.push({
                namespace: 'dash_leaflet',
                type: 'CircleMarker',
                props: {
                    center: [
                        [28.211666, 19.290556, 21.9544, 21.303333, 20.894945, 20.0366, 19.730278][i],
                        [-177.36, -193.3825, -159.3561, -157.86453, -156.469, -155.8294, -155.05556][i]
                    ],
                    radius: size,
                    color: 'white',
                    weight: 2,
                    fillColor: stationColors[i],
                    fillOpacity: opacity,
                    children: [{
                        namespace: 'dash_leaflet',
                        type: 'Tooltip',
                        props: {
                            children: `${stationOrder[i]}: ${waveDelta >= 0 ? '+' : ''}${waveDelta.toFixed(3)}m wave Δ`
                        }
                    }]
                }
            });
        }
        
        // Create map children array
        const mapChildren = [
            {
                namespace: 'dash_leaflet',
                type: 'TileLayer',
                props: {
                    url: `https://api.maptiler.com/maps/ocean/256/{z}/{x}/{y}.png?key=${window.MAPTILER_API_KEY || ''}`,
                    attribution: '<a href="https://www.maptiler.com/copyright/" target="_blank">&copy; MapTiler</a> <a href="https://www.openstreetmap.org/copyright" target="_blank">&copy; OpenStreetMap contributors</a>',
                    maxZoom: 18
                }
            },
            {
                namespace: 'dash_leaflet',
                type: 'CircleMarker',
                props: {
                    center: [52.473, -199.604],
                    radius: 15,
                    color: 'darkred',
                    weight: 4,
                    fillColor: 'red',
                    fillOpacity: 0.9,
                    children: [{
                        namespace: 'dash_leaflet',
                        type: 'Tooltip',
                        props: {
                            children: '🌋 EARTHQUAKE EPICENTER\\n29 July 2025, 23:24 UTC'
                        }
                    }]
                }
            },
            ...stationMarkers
        ];
        
        // Update wave propagation graph
        const waveTrace = {
            x: frameData.x_values,
            y: frameData.wave_values,
            type: 'scatter',
            mode: 'lines+markers',
            line: {color: 'firebrick', width: 3},
            marker: {size: 10, color: 'firebrick'},
            showlegend: false
        };
        
        const waveFig = {
            data: [waveTrace],
            layout: {
                title: {
                    text: 'Wave Amplitude vs Distance from Epicenter',
                    font: {size: 16, color: '#2c3e50'}
                },
                xaxis: {
                    title: 'Distance from Epicenter (km)',
                    range: [Math.min(...distances), Math.max(...distances)],
                    fixedrange: true
                },
                yaxis: {
                    title: 'Δ Wave Height (m)',
                    range: [-2, 3],  // Updated to requested range
                    fixedrange: true,
                    zeroline: false,
                    autorange: false
                },
                height: 400,
                plot_bgcolor: 'white',
                paper_bgcolor: 'white',
                margin: {t: 120, b: 40, l: 60, r: 20},
                showlegend: false,
                shapes: [
                    // Horizontal baseline
                    {
                        type: 'line',
                        x0: Math.min(...distances),
                        x1: Math.max(...distances),
                        y0: 0,
                        y1: 0,
                        line: {color: 'gray', width: 1, dash: 'dot'},
                        layer: 'below'
                    },
                    // Vertical lines for each station
                    ...distances.map(d => ({
                        type: 'line',
                        x0: d,
                        x1: d,
                        y0: -2,
                        y1: 3,
                        line: {color: 'gray', width: 1, dash: 'dash'},
                        layer: 'below'
                    }))
                ]
            }
        };
        
        // Create timeseries figure with actual data traces and current time indicator
        const timeseriesData = [];
        const timeseriesShapes = [];
        
        // Add data traces for each station (full time series)
        for (let i = 0; i < stationOrder.length; i++) {
            // Extract all timestamps and wave values for this station across all frames
            const timestamps = [];
            const waveValues = [];
            
            // Get data from all frames for this station
            Object.keys(window.tsunamiFrameData.frames).forEach(frameIdx => {
                const frame = window.tsunamiFrameData.frames[frameIdx];
                if (frame.timestamp && frame.wave_values && frame.wave_values[i] !== undefined) {
                    timestamps.push(frame.timestamp);
                    waveValues.push(frame.wave_values[i]);
                }
            });
            
            timeseriesData.push({
                x: timestamps,
                y: waveValues,
                type: 'scatter',
                mode: 'lines',
                name: stationOrder[i],
                showlegend: false,
                line: {width: 2, color: stationColors[i]},
                xaxis: `x${i+1}`,
                yaxis: `y${i+1}`
            });
            
            // Add current time indicator line for each subplot
            timeseriesShapes.push({
                type: 'line',
                xref: `x${i+1}`,
                yref: `y${i+1}`,
                x0: frameData.timestamp,
                x1: frameData.timestamp,
                y0: -1,
                y1: 1,
                line: {color: 'blue', width: 2, dash: 'dot'},
                layer: 'above'
            });
        }
        
        // Add earthquake time marker to all subplots
        const earthquakeTime = '2025-07-29T23:24:52.000Z';
        for (let i = 0; i < stationOrder.length; i++) {
            timeseriesShapes.push({
                type: 'line',
                xref: `x${i+1}`,
                yref: `y${i+1}`,
                x0: earthquakeTime,
                x1: earthquakeTime,
                y0: -1,
                y1: 1,
                line: {color: 'red', width: 1, dash: 'dash'},
                layer: 'above'
            });
        }
        
        // Create subplot layout with proper subplot configuration
        const timeseriesFig = {
            data: timeseriesData,
            layout: {
                height: 600,
                title: {
                    text: 'Wave Height Anomalies Over Time',
                    font: {size: 16, color: '#2c3e50'}
                },
                margin: {t: 50, b: 60, l: 80, r: 20},
                plot_bgcolor: 'white',
                paper_bgcolor: 'white',
                shapes: timeseriesShapes,
                grid: {rows: stationOrder.length, columns: 1, pattern: 'independent'},
                // Configure subplot titles and axes
                annotations: stationOrder.map((station, i) => ({
                    text: station,
                    showarrow: false,
                    x: 0.5,
                    y: 1 - (i + 0.5) / stationOrder.length,
                    xref: 'paper',
                    yref: 'paper',
                    xanchor: 'center',
                    yanchor: 'middle',
                    font: {size: 12, color: '#2c3e50'}
                }))
            }
        };
        
        // Set up individual subplot axes with proper ranges (match original app)
        for (let i = 1; i <= stationOrder.length; i++) {
            const axisConfig = {
                range: [-2, 3],  // Updated to requested range
                fixedrange: true,
                zeroline: false,
                showgrid: true,
                gridcolor: '#f0f0f0'
            };
            
            timeseriesFig.layout[`yaxis${i === 1 ? '' : i}`] = {
                ...axisConfig,
                title: i === Math.ceil(stationOrder.length / 2) ? 'Δ Wave Height (m)' : ''
            };
            
            timeseriesFig.layout[`xaxis${i === 1 ? '' : i}`] = {
                showgrid: true,
                gridcolor: '#f0f0f0',
                title: i === stationOrder.length ? 'Time (UTC)' : '',
                fixedrange: false
            };
        }
        
        // Format timestamp for display (remove seconds to match original)
        const timestamp = new Date(frameData.timestamp);
        let displayTime;
        if (timezoneMode === 'HST') {
            const hstTime = new Date(timestamp.getTime() - (10 * 60 * 60 * 1000)); // UTC-10
            displayTime = hstTime.toISOString().slice(0, 16).replace('T', ' ') + ' HST';
        } else {
            displayTime = timestamp.toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
        }
        
        // Create slider marks
        const marks = {};
        
        // Add basic time marks every 180 frames (3 hours)
        for (let i = 0; i < 1476; i += 180) {
            marks[i] = (i / 60).toFixed(0) + 'h';
        }
        
        // Add special markers
        marks[0] = '🌋EQ';
        marks[245] = '📍M';  // Midway
        marks[355] = '📍H';  // Hawaii
        
        const toggleText = timezoneMode === 'HST' ? 'Show UTC' : 'Show HST';
        
        return [mapChildren, waveFig, timeseriesFig, displayTime, toggleText, marks];
    }
    """,
    [Output("bathymetry-map", "children"),
     Output("wave-graph", "figure"), 
     Output("timeseries-graph", "figure"),
     Output("timeline-clock", "children"),
     Output("timezone-toggle", "children"),
     Output("frame-slider", "marks")],
    [Input("frame-slider", "value"), Input("timezone-toggle", "n_clicks")],
    [State("frame-data-store", "children")]
)

# Keyboard controls
app.clientside_callback(
    """
    function(id) {
        document.addEventListener('keydown', function(event) {
            if (event.key === ' ') {
                event.preventDefault();
                const playBtn = document.getElementById('play-pause-btn');
                if (playBtn) playBtn.click();
            }
        });
        return '';
    }
    """,
    Output('keyboard-listener', 'children'),
    Input('keyboard-listener', 'id')
)

# Expose the Flask server for Gunicorn
server = app.server

if __name__ == '__main__':
    import os
    
    # Calculate and display total startup time
    total_startup_time = time.time() - startup_start_time
    print(f"🚀 TOTAL STARTUP TIME: {total_startup_time:.3f}s")
    print("🌊 Client-side tsunami visualization ready!")
    print("⚡ All data will be loaded client-side for instant performance!")
    
    # Get port from environment variable (for cloud deployment)
    port = int(os.environ.get('PORT', 8050))
    
    # Get debug mode from environment variable 
    debug_mode = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print(f"🚀 Starting Tsunami Visualization App on port {port}")
    print(f"🌊 Debug mode: {debug_mode}")
    print("🎯 MapTiler API Key:", "✅ Loaded" if os.environ.get('MAPTILER_API_KEY') else "❌ Missing")
    
    app.run(
        debug=debug_mode,
        host='0.0.0.0',  # Allow external connections
        port=port
    )