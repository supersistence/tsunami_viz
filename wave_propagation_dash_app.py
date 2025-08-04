import dash
from dash import dcc, html
import plotly.graph_objects as go
import pandas as pd
import pickle
import dash_leaflet as dl
import os
import numpy as np
import plotly
import time
print("DEBUG: plotly version:", plotly.__version__)
print("DEBUG: dash version:", dash.__version__)

# Start timing app startup
startup_start_time = time.time()

# Load pivoted data for oscilloscope-style animation
data_load_start = time.time()
with open("data/pivoted_wave_data.pkl", "rb") as f:
    pivoted = pickle.load(f)
df_pivot = pivoted['df_pivot']  # index: t, columns: station, values: delta
station_order = pivoted['station_order']
station_distances = pivoted['station_distance']
data_load_time = time.time() - data_load_start
print(f"⏱️ Data loading: {data_load_time:.3f}s")

# Earthquake epicenter coordinates (2025 Kamchatka Peninsula earthquake)
epicenter_lat, epicenter_lon = 52.473, 160.396

# Earthquake timing: 30 July 2025, at 11:24:52 PETT (29 July 2025, 23:24:52 UTC)
earthquake_time = pd.Timestamp('2025-07-29 23:24:52')  # timezone-naive to match data

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
        return hst_time.strftime('%Y-%m-%d %H:%M:%S HST')
    else:  # UTC
        return time.strftime('%Y-%m-%d %H:%M:%S UTC')

def get_percent(t, all_frames):
    """Return percent along timeline for a given timestamp t."""
    t0, t1 = all_frames[0], all_frames[-1]
    return ((t - t0) / (t1 - t0)) * 100



# Remove unwanted stations from visualization
stations_to_remove = ['Pago Pago', 'Kwajalein', 'Apra Harbor', 'Pago Bay', 'Pearl Harbor', 'Mokuoloe']
for station in stations_to_remove:
    if station in df_pivot.columns:
        df_pivot = df_pivot.drop(columns=[station])

# Filter to times from earthquake occurrence to July 31 00:00 UTC
import pandas as pd
end_time = pd.Timestamp('2025-07-31 00:00:00')
df_pivot = df_pivot[(df_pivot.index >= earthquake_time) & (df_pivot.index <= end_time)]

# Sort columns and distances
station_order = [s for s in station_order if s in df_pivot.columns]
distances = [station_distances[s] for s in station_order]

# Get all frames (times)
all_frames = df_pivot.index.sort_values()

# Find the earthquake frame index for slider marking
earthquake_frame_idx = None
if earthquake_time in all_frames:
    earthquake_frame_idx = list(all_frames).index(earthquake_time)
else:
    # Find closest frame to earthquake time
    time_diffs = abs(all_frames - earthquake_time)
    earthquake_frame_idx = time_diffs.argmin()



def create_slider_marks(timezone_mode='UTC'):
    """Create slider marks every 3 hours from July 30 00:00 to July 31 00:00"""
    marks = {}
    
    # Create marks every 3 hours
    start_time = pd.Timestamp('2025-07-30 00:00:00')
    end_time = pd.Timestamp('2025-07-31 00:00:00')
    current_time = start_time
    
    while current_time <= end_time:
        # Find closest frame index to this time
        if len(all_frames) > 0 and current_time >= all_frames[0] and current_time <= all_frames[-1]:
            time_diffs = abs(all_frames - current_time)
            closest_idx = int(time_diffs.argmin())
            # Format time based on timezone
            if timezone_mode == 'HST':
                hst_time = convert_to_hst(current_time)
                time_label = hst_time.strftime('%H:%M')
            else:
                time_label = current_time.strftime('%H:%M')
            marks[closest_idx] = time_label
        
        current_time += pd.Timedelta(hours=3)
    
    # Add earthquake marker with special styling
    if earthquake_frame_idx is not None:
        eq_idx = int(earthquake_frame_idx)
        marks[eq_idx] = "🌋EQ"
    
    # Add hardcoded station arrival markers at specific frame numbers
    marks[245] = "📍M"  # Frame 245 for Midway
    marks[355] = "📍H"  # Frame 355 for Hawaii
    print(f"DEBUG: Added hardcoded slider marks - Midway at frame 245, Hawaii at frame 355")
    
    return marks

# Interpolate and fill missing values for continuous line
# (axis=0: fill down each station column by time)
df_pivot_interp = df_pivot.interpolate(axis=0).ffill().bfill()

# Debug: print first frame's distances and y-values
print('DEBUG: distances:', distances)
# print('DEBUG: first frame y:', df_pivot_interp.iloc[0].values.tolist())

# Filter out frames where all y are NaN (should be none after fill, but for safety)
valid_frame_mask = ~np.all(np.isnan(df_pivot_interp.values), axis=1)
df_pivot_interp = df_pivot_interp[valid_frame_mask]
all_frames = df_pivot_interp.index.sort_values()

# Recalculate y_range using only non-NaN values from all frames
all_y = df_pivot_interp.values.flatten()
y_range = [float(np.nanmin(all_y[np.isfinite(all_y)])) - 0.1, float(np.nanmax(all_y[np.isfinite(all_y)])) + 0.1]

# Debug: print y values for first 3 frames
for i in range(min(3, len(df_pivot_interp))):
    print(f'DEBUG: frame {i} y:', df_pivot_interp.iloc[i].values.tolist())

# ⚡ OPTIMIZATION #2: Pre-calculate all frame data to eliminate DataFrame lookups
print("⚡ Pre-calculating frame data for performance optimization...")
precalc_start = time.time()

# Pre-calculate wave values for all frames
frame_data_cache = {}
for i, t in enumerate(all_frames):
    frame_y = df_pivot_interp.iloc[i].values.tolist()
    frame_data_cache[i] = {
        'timestamp': t,
        'wave_values': frame_y,
        'x_values': [float(d) for d in distances]  # Pre-calculate x values too
    }

precalc_time = time.time() - precalc_start
print(f"⚡ Frame data pre-calculation: {precalc_time:.3f}s ({len(frame_data_cache)} frames)")
print(f"⚡ Memory usage: ~{len(frame_data_cache) * len(station_order) * 8 / 1024:.1f}KB for wave data")

# Build go.Figure with animation
figure_build_start = time.time()
fig = go.Figure()

# Add horizontal baseline at delta = 0
fig.add_shape(
    type="line",
    x0=min(station_distances.values()),
    x1=max(station_distances.values()),
    y0=0,
    y1=0,
    line=dict(color="gray", width=1, dash="dot"),
    layer="below"
)

# Add initial oscilloscope-style polyline (first frame) - using pre-calculated data
x0 = frame_data_cache[0]['x_values']
y0 = frame_data_cache[0]['wave_values']
print('DEBUG: initial trace x:', x0)
print('DEBUG: initial trace y:', y0)
fig.add_trace(go.Scatter(
    x=x0,
    y=y0,
    mode='lines+markers',
    line=dict(color='firebrick', width=3),
    marker=dict(size=10, color='firebrick'),
    name='Wave Δ',
    showlegend=False
))

# Add vertical dashed lines for each station
for i, x in enumerate(distances):
    fig.add_shape(
        type="line",
        x0=x, x1=x,
        y0=y_range[0], y1=y_range[1],
        line=dict(color="gray", width=1, dash="dash"),
        layer="below"
    )

# Add station labels as annotations with smart positioning to prevent overlap
label_positions = []
for i, x in enumerate(distances):
    # Calculate positions to avoid overlap
    base_y = 1.05
    offset = 0.06
    
    # Custom level mapping based on station names
    station_name = station_order[i]
    if station_name in ['Midway', 'Wake Island', 'Nawiliwili', 'Kahului', 'Hilo']:
        level = 0  # Same height as Midway
    elif station_name in ['Honolulu', 'Kawaihae']:
        level = 1  # Middle height
    else:
        level = 0  # Default to level 0
    
    y_pos = base_y + (offset * level)
    
    fig.add_annotation(
        x=x,
        y=y_pos,
        yref="paper",
        text=station_order[i],
        showarrow=True,
        arrowhead=2,
        arrowsize=0.8,
        arrowwidth=1,
        arrowcolor="darkgray",
        ax=0,
        ay=-15 - (5 * level),  # Variable arrow lengths based on level
        yanchor="bottom",
        textangle=0,
        font=dict(size=9, color="black", family="Arial", weight="bold"),
        bgcolor="rgba(255,255,255,0.95)",
        bordercolor="darkgray",
        borderwidth=1,
        borderpad=2
    )

# Add horizontal baseline at y=0
fig.add_shape(
    type="line",
    x0=min(distances), x1=max(distances),
    y0=0, y1=0,
    line=dict(color="black", width=2),
    layer="below"
)

# Animation frames: one continuous polyline per frame - using pre-calculated data
frames = []
for i in range(len(all_frames)):
    frame_data = frame_data_cache[i]
    x = frame_data['x_values']
    y = frame_data['wave_values']
    frames.append(go.Frame(
        data=[go.Scatter(
            x=x,
            y=y,
            mode='lines+markers',
            line=dict(color='firebrick', width=3),
            marker=dict(size=10, color='firebrick'),
            showlegend=False
        )],
        name=str(frame_data['timestamp'])
    ))
fig.frames = frames

# Layout
fig.update_layout(
    title=dict(
        text="Wave Amplitude vs Distance from Epicenter",
        font=dict(size=16, color='#2c3e50')
    ),
    xaxis_title="Distance from Epicenter (km)",
    yaxis_title="Δ Wave Height (m)",
    yaxis=dict(range=y_range, fixedrange=True, zeroline=False, autorange=False),
    xaxis=dict(range=[min(distances), max(distances)], fixedrange=True),
    height=400,
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(t=120, b=40, l=60, r=20),  # More space for 3-level labels
    showlegend=False  # Remove legend to save space - single trace is self-explanatory
)

figure_build_time = time.time() - figure_build_start
print(f"⏱️ Figure building: {figure_build_time:.3f}s")


# Dash app layout
app = dash.Dash(__name__)
from dash import dash_table
import plotly.subplots as sp

# Prepare table data: show last 10 time steps
preview_rows = 10
preview_df = df_pivot_interp.tail(preview_rows)
preview_df_reset = preview_df.reset_index()

# Create a timeseries figure for each station
station_timeseries_fig = sp.make_subplots(
    rows=len(station_order), cols=1, shared_xaxes=True,
    subplot_titles=station_order, vertical_spacing=0.01
)
for i, station in enumerate(station_order):
    station_timeseries_fig.add_trace(
        go.Scatter(
            x=df_pivot_interp.index,
            y=df_pivot_interp[station],
            mode='lines',
            name=station,
            showlegend=False,
            line=dict(width=2)
        ),
        row=i+1, col=1
    )
# Set all y-axes to the same range
yaxis_range = y_range  # use the same as oscilloscope plot
for i in range(1, len(station_order)+1):
    station_timeseries_fig.update_yaxes(range=yaxis_range, row=i, col=1)

# Colors now use Plotly's standard defaults to match time series

station_timeseries_fig.update_layout(
    height=600,
    title=dict(
        text="Wave Height Anomalies Over Time",
        font=dict(size=16, color='#2c3e50')
    ),
    margin=dict(t=50, b=60, l=80, r=20),  # More bottom margin for x-axis label, more left for y-axis
    plot_bgcolor="white",
    paper_bgcolor="white"
)

# Update x-axis to show label only at bottom
station_timeseries_fig.update_xaxes(
    title_text="Time (UTC)",
    title_standoff=1,
    row=len(station_order), col=1  # Only show on bottom subplot
)

# Update y-axis label positioning to center
station_timeseries_fig.update_layout(
    yaxis=dict(
        title="Δ Wave Height (m)",
        title_standoff=5
    )
)




# Add earthquake marker to all time series subplots
earthquake_shapes = []
for i in range(1, len(station_order)+1):
    earthquake_shapes.append({
        "type": "line",
        "xref": f"x{i}",
        "yref": f"y{i}",
        "x0": earthquake_time,
        "x1": earthquake_time,
        "y0": yaxis_range[0],
        "y1": yaxis_range[1],
        "line": {"color": "red", "width": 1, "dash": "dash"},
        "layer": "above"
    })

station_timeseries_fig.update_layout(shapes=earthquake_shapes)

# Add earthquake annotation to the first subplot
# station_timeseries_fig.add_annotation(
#     x=earthquake_time,
#     y=yaxis_range[1] * 0.9,
#     xref="x1",
#     yref="y1",
#     text="Earthquake<br>29 July 23:24 UTC",
#     showarrow=True,
#     arrowhead=2,
#     arrowsize=1,
#     arrowwidth=2,
#     arrowcolor="red",
#     bgcolor="rgba(255,255,255,0.9)",
#     bordercolor="red",
#     borderwidth=2,
#     font=dict(size=10, color="red")
# )

# --- Animated Overview Map Construction ---
# Hardcoded station coordinates (pre-transformed to Western Pacific view)
# These coordinates have already been shifted to avoid IDL rendering issues
# Station order: ['Midway', 'Wake Island', 'Nawiliwili', 'Honolulu', 'Kahului', 'Kawaihae', 'Hilo']
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

# Show improved circle scaling examples
print()
print("🎯 IMPROVED CIRCLE SCALING EXAMPLES:")
print("   Formula: size = 4 + (8 * sqrt(min(1.0, |wave_delta|/0.3)))")
print("   Opacity: 0.3 + (0.7 * min(1.0, |wave_delta|/0.2))")
print("   Border: White outline, size/opacity shows magnitude")
sample_deltas = [0.01, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, -0.1, -0.2]
for delta in sample_deltas:
    wave_magnitude = abs(delta)
    size_factor = min(1.0, wave_magnitude / 0.3)
    size = 4 + (8 * np.sqrt(size_factor))
    opacity_factor = min(1.0, wave_magnitude / 0.2)
    opacity = 0.3 + (0.7 * opacity_factor)
    print(f"   Wave Δ {delta:+5.2f}m → Size {size:4.1f}px, Opacity {opacity:.2f}")

# Prepare initial map frame with improved station focus - using pre-calculated data
initial_wave_values = frame_data_cache[0]['wave_values']
# Use same improved sizing logic as in callback
initial_marker_data = []
for i in range(len(initial_wave_values)):
    wave_delta = initial_wave_values[i]  # Keep sign
    wave_magnitude = abs(wave_delta)
    
    # Match callback sizing logic
    base_size = 4
    max_additional_size = 8
    size_factor = min(1.0, wave_magnitude / 0.3)
    size = base_size + (max_additional_size * np.sqrt(size_factor))
    
    opacity_factor = min(1.0, wave_magnitude / 0.2)
    opacity = 0.3 + (0.7 * opacity_factor)
    
    # Keep clean white border like original
    border_color = 'white'
    border_weight = 2
    
    initial_marker_data.append({
        'size': size, 
        'opacity': opacity,
        'border_color': border_color,
        'border_weight': border_weight,
        'wave_delta': wave_delta
    })

# OLD PLOTLY MAP CODE REMOVED - NOW USING DASH LEAFLET BATHYMETRY MAP

# --- Dash Layout with Map ---
from dash.dependencies import Input, Output, State
from dash import clientside_callback, ClientsideFunction

# Unified animation controls are handled through the main dashboard interface

app.layout = html.Div([
    # Keyboard event listener
    html.Div(id="keyboard-listener", tabIndex=0, style={'outline': 'none'}),
    
    # Header Section
    html.Div([
        html.H1("🌊 Wave Watch: Kamchatka to Hawai‘i", 
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
        html.P("Hover for station details, drag timeline for navigation, and use keyboard shortcuts (Space=play/pause, arrows=step) - all panels update simultaneously.",
               style={'color': '#7f8c8d', 'fontSize': '0.9rem', 'marginBottom': '15px', 'fontStyle': 'italic'}),
        html.Div([
            html.Div([
                html.Button('▶️ Play', id='play-pause-btn', n_clicks=0, 
                           style={'padding': '12px 24px', 'fontSize': '16px', 'fontWeight': 'bold', 
                                 'backgroundColor': '#27ae60', 'color': 'white', 'border': 'none', 
                                 'borderRadius': '8px', 'cursor': 'pointer', 'marginRight': '20px',
                                 'boxShadow': '0 3px 6px rgba(0,0,0,0.2)', 'transition': 'all 0.3s'}),
                html.Span("Speed: ", style={'fontSize': '16px', 'fontWeight': 'bold', 'color': '#2c3e50', 'marginRight': '10px'}),
                dcc.Dropdown(
                    id='speed-dropdown',
                    options=[
                        {'label': '🐌 Slow', 'value': 200},
                        {'label': '🚶 Normal', 'value': 100},
                        {'label': '🏃 Fast', 'value': 50}
                    ],
                    value=100,
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
                #html.P("🌋 Red marker shows earthquake occurrence", style={'fontSize': '12px', 'color': '#e74c3c', 'margin': '5px 0', 'fontStyle': 'italic'}),
                html.P("⌨️ Keyboard: Space=Play/Pause, ←/→=Manual step, ↑/↓=Speed", style={'fontSize': '11px', 'color': '#95a5a6', 'margin': '2px 0', 'fontStyle': 'italic'}),
        dcc.Slider(
            id="frame-slider",
            min=0,
            max=len(all_frames)-1,
            value=0,
                    marks=create_slider_marks(),
            step=1,
                    updatemode='drag',
                    tooltip={"placement": "bottom", "always_visible": False}
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
            # Real bathymetry map using MapTiler Ocean tiles
            # Based on: https://docs.maptiler.com/sdk-js/examples/ocean-bathymetry/
            dl.Map(
                id="bathymetry-map",
                style={'width': '100%', 'height': '400px'},
                center=[center_lat, center_lon],  # Auto-calculated optimal center
                zoom=3,
                bounds=[[bounds_min_lat, bounds_min_lon], [bounds_max_lat, bounds_max_lon]],  # Auto-fit bounds
                worldCopyJump=True,  # Handle IDL properly
                children=[
                    # MapTiler Ocean bathymetry tile layer
                    dl.TileLayer(
                        url="https://api.maptiler.com/maps/ocean/256/{z}/{x}/{y}.png?key=get_your_own_OpIi9ZULNHzrESv6T2vL",
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
                    # Dynamic station markers with improved sizing and opacity
                    *[dl.CircleMarker(
                        center=[station_lats[i], station_lons[i]],
                        radius=initial_marker_data[i]['size'],
                        color=initial_marker_data[i]['border_color'],
                        weight=initial_marker_data[i]['border_weight'],
                        fillColor=station_colors[i],
                        fillOpacity=initial_marker_data[i]['opacity'],
                        children=[dl.Tooltip(f"{station_order[i]}: {initial_marker_data[i]['wave_delta']:+.3f}m wave Δ")]
                    ) for i in range(len(station_order))]
                ]
            ),
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingRight': '2%'}),
        
        # Right Column - Wave Propagation Analysis
        html.Div([
            html.H3("📊 Wave Propagation", style={'color': '#2c3e50', 'marginBottom': '15px', 'fontSize': '1.2rem'}),
            html.P("Oscilloscope-style visualization showing wave front progression across all stations, with distance from epicenter on X-axis and wave height anomaly on Y-axis.",
                   style={'color': '#7f8c8d', 'fontSize': '0.9rem', 'marginBottom': '15px', 'fontStyle': 'italic'}),
            dcc.Graph(id="wave-graph", style={'height': '400px'}),
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingLeft': '2%'}),
    ]),
    
    # Bottom Row - Station Time Series (Full Width)
    html.Div([
        html.H3("📈 Station Time Series", style={'color': '#2c3e50', 'marginTop': '30px', 'marginBottom': '15px', 'fontSize': '1.2rem'}),
        html.P("Individual wave height records for each monitoring station over time, showing how tsunami waves arrive at different locations across the Pacific.",
               style={'color': '#7f8c8d', 'fontSize': '0.9rem', 'marginBottom': '15px', 'fontStyle': 'italic'}),
        dcc.Graph(id="timeseries-graph", style={'height': '600px'}),
    ], style={'width': '100%', 'marginTop': '20px'}),
    
    # Footer Info
    html.Div([
        html.P([
           # "📍 Earthquake to July 31 00:00 UTC (52.473°N, 160.396°E) | ",
           "📊 Data Source: ",
            html.A("NOAA CO-OPS API", href="https://tidesandcurrents.noaa.gov/web_services_info.html", target="_blank")
        ], style={'margin': '0', 'color': '#95a5a6', 'fontSize': '0.9rem', 'textAlign': 'center'})
    ], style={'marginTop': '30px', 'padding': '15px', 'background': '#ecf0f1', 'borderRadius': '8px'}),
    
    dcc.Interval(id="interval", interval=50, n_intervals=0, disabled=True)
], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '20px', 'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#f8f9fa'})

# Calculate and display total startup time
total_startup_time = time.time() - startup_start_time
print(f"🚀 TOTAL STARTUP TIME: {total_startup_time:.3f}s")

@app.callback(
    [Output("interval", "disabled"), Output("interval", "interval"), Output("play-pause-btn", "children"), Output("play-pause-btn", "style")],
    [Input("play-pause-btn", "n_clicks"), Input("speed-dropdown", "value")],
    [State("interval", "disabled")]
)
def toggle_play_pause(n_clicks, speed_value, interval_disabled):
    # Use speed_value for interval, default to 100ms (original speed)
    if speed_value is None:
        speed_value = 100
    
    # Button styles
    play_style = {
        'padding': '12px 24px', 'fontSize': '16px', 'fontWeight': 'bold', 
        'backgroundColor': '#27ae60', 'color': 'white', 'border': 'none', 
        'borderRadius': '8px', 'cursor': 'pointer', 'marginRight': '20px',
        'boxShadow': '0 3px 6px rgba(0,0,0,0.2)', 'transition': 'all 0.3s'
    }
    pause_style = {
        'padding': '12px 24px', 'fontSize': '16px', 'fontWeight': 'bold',
        'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none',
        'borderRadius': '8px', 'cursor': 'pointer', 'marginRight': '20px',
        'boxShadow': '0 3px 6px rgba(0,0,0,0.2)', 'transition': 'all 0.3s'
    }
    
    # Toggle between play and pause states
    if n_clicks is None or n_clicks == 0:
        # Initial state - stopped
        return True, speed_value, "▶️ Play", play_style
    
    # Toggle state
    if interval_disabled:
        # Currently paused, so start playing
        return False, speed_value, "⏸️ Pause", pause_style
    else:
        # Currently playing, so pause
        return True, speed_value, "▶️ Play", play_style

@app.callback(
    Output("frame-slider", "value"),
    [Input("interval", "n_intervals")],
    [State("frame-slider", "value")]
)
def advance_frame(n_intervals, slider_val):
    if slider_val is None:
        return 0
    
    # Advance by 1 frame (original behavior - no frame skipping)
    next_val = slider_val + 1
    if next_val >= len(all_frames):
        return 0  # loop back to start
    return next_val

@app.callback(
    [Output("timeline-clock", "children"), Output("timezone-toggle", "children")],
    [Input("frame-slider", "value"), Input("timezone-toggle", "n_clicks")]
)
def update_timeline_clock(frame_index, timezone_clicks):
    """Update the clock display with current timeline time and timezone toggle"""
    if frame_index is None or frame_index >= len(all_frames):
        return "Loading...", "🔄 UTC"
    
    # Determine timezone mode based on toggle clicks
    timezone_mode = 'HST' if timezone_clicks and timezone_clicks % 2 == 1 else 'UTC'
    
    current_time = all_frames[frame_index]
    formatted_time = format_time_display(current_time, timezone_mode)
    
    # Update toggle button text
    toggle_text = "Show UTC" if timezone_mode == 'HST' else "Show HST"
    
    return formatted_time, toggle_text

@app.callback(
    Output("frame-slider", "marks"),
    [Input("timezone-toggle", "n_clicks")]
)
def update_slider_marks(timezone_clicks):
    """Update slider marks when timezone is toggled"""
    timezone_mode = 'HST' if timezone_clicks and timezone_clicks % 2 == 1 else 'UTC'
    return create_slider_marks(timezone_mode)

@app.callback(
    [Output("bathymetry-map", "children"), Output("wave-graph", "figure"), Output("timeseries-graph", "figure")],
    [Input("frame-slider", "value")],
    prevent_initial_call=True
)
def update_all_figures(frame_idx):
    callback_start_time = time.time()
    
    # ⚡ OPTIMIZATION #2: Use pre-calculated frame data instead of DataFrame lookup
    frame_data = frame_data_cache[frame_idx]
    t = frame_data['timestamp']
    frame_y = frame_data['wave_values']
    frame_x = frame_data['x_values']
    
    # Create updated station markers
    station_markers = []
    for i, (lat, lon, name) in enumerate(zip(station_lats, station_lons, station_order)):
        # 🎯 IMPROVED: More sensitive circle sizing and visual feedback
        wave_delta = frame_y[i]  # Keep sign for positive/negative indication
        wave_magnitude = abs(wave_delta)
        
        # Base size for neutral/small waves, then scale based on magnitude
        base_size = 4  # Much smaller base
        max_additional_size = 8  # Smaller range: 4px to 12px
        size_factor = min(1.0, wave_magnitude / 0.3)  # More sensitive threshold
        size = base_size + (max_additional_size * np.sqrt(size_factor))
        
        # Enhanced opacity - more dramatic changes for visual impact
        opacity_factor = min(1.0, wave_magnitude / 0.2)  # Even more sensitive threshold
        opacity = 0.3 + (0.7 * opacity_factor)  # 0.3 to 1.0 range
        
        # Color intensity based on wave magnitude for additional visual cue
        base_color = station_colors[i]
        
        # Keep clean white border like original
        border_color = 'white'
        border_weight = 2
        
        station_markers.append(
            dl.CircleMarker(
                center=[lat, lon],
                radius=size,
                color=border_color,
                weight=border_weight,
                fillColor=base_color,
                fillOpacity=opacity,
                children=[
                    dl.Tooltip(f"{name}: {wave_delta:+.3f}m wave Δ")
                ]
            )
        )
    
    # Create epicenter marker (static) - use CircleMarker for consistency
    epicenter_marker = dl.CircleMarker(
        center=[epicenter_lat, epicenter_lon],
        radius=20,
        color='darkred',
        weight=4,
        fillColor='red',
        fillOpacity=0.9,
        children=[dl.Tooltip("🌋 EARTHQUAKE EPICENTER\n29 July 2025, 23:24 UTC")]
    )
    
    # Updated map children with bathymetry tiles
    map_children = [
        # MapTiler Ocean bathymetry tile layer
        dl.TileLayer(
            url="https://api.maptiler.com/maps/ocean/256/{z}/{x}/{y}.png?key=get_your_own_OpIi9ZULNHzrESv6T2vL",
            attribution='<a href="https://www.maptiler.com/copyright/" target="_blank">&copy; MapTiler</a> <a href="https://www.openstreetmap.org/copyright" target="_blank">&copy; OpenStreetMap contributors</a>',
            maxZoom=18
        ),
        # Epicenter marker
        epicenter_marker,
        # Updated station markers with Plotly colors
        *station_markers
    ]
    # --- Update oscilloscope --- ⚡ Using pre-calculated data
    fig_c = fig.to_dict()
    fig_c['data'][0]['x'] = frame_x
    fig_c['data'][0]['y'] = frame_y
    # --- Update time series with vertical line ---
    fig_ts = station_timeseries_fig.to_dict()
    shapes = []
    
    # Add earthquake marker (static)
    for i in range(len(station_order)):
        shapes.append({
            "type": "line",
            "xref": f"x{i+1}",
            "yref": f"y{i+1}",
            "x0": earthquake_time,
            "x1": earthquake_time,
            "y0": y_range[0],
            "y1": y_range[1],
            "line": {"color": "red", "width": 3, "dash": "dash"},
            "layer": "above"
        })
    
    # Add current time marker (animated)
    for i in range(len(station_order)):
        shapes.append({
            "type": "line",
            "xref": f"x{i+1}",
            "yref": f"y{i+1}",
            "x0": t,
            "x1": t,
            "y0": y_range[0],
            "y1": y_range[1],
            "line": {"color": "blue", "width": 2, "dash": "dot"},
            "layer": "above"
        })
    fig_ts["layout"]["shapes"] = shapes
    
    callback_time = time.time() - callback_start_time
    print(f"⏱️ Callback execution: {callback_time:.3f}s (frame {frame_idx})")
    
    return map_children, fig_c, fig_ts

# Add clientside callback for keyboard controls
app.clientside_callback(
    """
    function(id) {
        document.addEventListener('keydown', function(event) {
            // Focus on the keyboard listener to capture events
            if (event.key === ' ') {
                event.preventDefault();
                // Toggle play/pause (trigger button clicks)
                document.getElementById('play-pause-btn').click();
            } else if (event.key === 'ArrowRight') {
                event.preventDefault();
                // Manual step forward
                var slider = document.getElementById('frame-slider');
                var currentVal = parseInt(slider.value) || 0;
                var maxVal = parseInt(slider.max) || 0;
                slider.value = currentVal < maxVal ? currentVal + 1 : 0;
                slider.dispatchEvent(new Event('change'));
            } else if (event.key === 'ArrowLeft') {
                event.preventDefault();
                // Manual step backward
                var slider = document.getElementById('frame-slider');
                var currentVal = parseInt(slider.value) || 0;
                var maxVal = parseInt(slider.max) || 0;
                slider.value = currentVal > 0 ? currentVal - 1 : maxVal;
                slider.dispatchEvent(new Event('change'));
            }
        });
        return '';
    }
    """,
    Output('keyboard-listener', 'children'),
    Input('keyboard-listener', 'id')
)

if __name__ == '__main__':
    import os
    
    # Get port from environment variable (for cloud deployment)
    port = int(os.environ.get('PORT', 8050))
    
    # Deployment vs local development settings
    debug_mode = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print(f"🚀 Starting Tsunami Visualization App on port {port}")
    print(f"🌊 Debug mode: {debug_mode}")
    
    app.run(
        debug=debug_mode,
        host='0.0.0.0',  # Allow external connections
        port=port
    )
