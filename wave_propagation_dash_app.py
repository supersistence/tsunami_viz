import dash
from dash import dcc, html
import plotly.graph_objects as go
import pandas as pd
import pickle
import os
import numpy as np
import plotly
print("DEBUG: plotly version:", plotly.__version__)
print("DEBUG: dash version:", dash.__version__)

# Load pivoted data for oscilloscope-style animation
with open("data/pivoted_wave_data.pkl", "rb") as f:
    pivoted = pickle.load(f)
df_pivot = pivoted['df_pivot']  # index: t, columns: station, values: delta
station_order = pivoted['station_order']
station_distances = pivoted['station_distance']

# Earthquake epicenter coordinates (2025 Kamchatka Peninsula earthquake)
epicenter_lat, epicenter_lon = 52.473, 160.396

# Earthquake timing: 30 July 2025, at 11:24:52 PETT (29 July 2025, 23:24:52 UTC)
earthquake_time = pd.Timestamp('2025-07-29 23:24:52')  # timezone-naive to match data

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

def create_slider_marks():
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
            # Format: "00:00" for time display
            time_label = current_time.strftime('%H:%M')
            marks[closest_idx] = time_label
        
        current_time += pd.Timedelta(hours=3)
    
    # Add earthquake marker with special styling
    if earthquake_frame_idx is not None:
        eq_idx = int(earthquake_frame_idx)
        marks[eq_idx] = "🌋 EQ"
    
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

# Build go.Figure with animation
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

# Add initial oscilloscope-style polyline (first frame)
x0 = [float(d) for d in distances]
y0 = [float(v) for v in df_pivot_interp.iloc[0].values.tolist()]
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

# Animation frames: one continuous polyline per frame
frames = []
for i, t in enumerate(all_frames):
    frame_y = df_pivot_interp.iloc[i].values.tolist()
    x = [float(d) for d in distances]
    y = [float(v) for v in frame_y]
    frames.append(go.Frame(
        data=[go.Scatter(
            x=x,
            y=y,
            mode='lines+markers',
            line=dict(color='firebrick', width=3),
            marker=dict(size=10, color='firebrick'),
            showlegend=False
        )],
        name=str(t)
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
# Load station lat/lon from station metadata
with open("data/station_metadata.json", "r") as f:
    station_meta = pd.read_json(f).T

# Build display name -> id mapping
from wave_data_collect_and_cache import stations
# Map display name in station_order to station_id for metadata lookup
station_ids = []
for name in station_order:
    # Try direct lookup in stations dict
    if name in stations:
        station_ids.append(stations[name]['id'])
    else:
        # Fallback: try to match by canonical name in metadata
        found = False
        for sid, meta in station_meta.iterrows():
            if meta['name'] == name:
                station_ids.append(sid)
                found = True
                break
        if not found:
            raise KeyError(f"Cannot map station display name '{name}' to station ID for metadata lookup. Check station_order and metadata consistency.")
station_lats = [station_meta.loc[int(sid), 'lat'] for sid in station_ids]
station_lons = [station_meta.loc[int(sid), 'lng'] for sid in station_ids]

# Prepare initial map frame with improved station focus
map_marker_sizes = [max(12, min(35, abs(y0[i])*20)) for i in range(len(y0))]  # larger, more visible markers
map_marker_colors = y0  # use delta directly for color

map_fig = go.Figure()

# Add earthquake epicenter first (so it appears behind stations)
map_fig.add_trace(go.Scattergeo(
    lon=[epicenter_lon],
    lat=[epicenter_lat],
    text=['Earthquake<br>Epicenter'],
    marker=dict(
        size=20,
        color='red',
        symbol='star',
        line=dict(width=2, color='darkred')
    ),
    mode='markers+text',
    textposition="bottom center",
    textfont=dict(size=12, color='darkred'),
    name='Epicenter',
    showlegend=False
))

# Add tsunami monitoring stations
map_fig.add_trace(go.Scattergeo(
    lon=station_lons,
    lat=station_lats,
    text=[f'{name}' for name in station_order],
    marker=dict(
        size=map_marker_sizes,
        color=map_marker_colors,
        colorscale='RdBu',
        cmin=y_range[0],
        cmax=y_range[1],
        # colorbar=dict(
        #     title=dict(text="Wave Height Δ (m)", font=dict(size=12)), 
        #     len=0.6, 
        #     y=0.75,
        #     thickness=15
        # ),
        line=dict(width=2, color='black'),
        symbol='circle'
    ),
    mode='markers+text',
    textposition="top center",
    textfont=dict(size=10, color='black'),
    name='Monitoring Stations',
    showlegend=False
))
map_fig.update_geos(
    projection_type="natural earth",
    showcountries=True, 
    showcoastlines=True, 
    showland=True, 
    landcolor='lightgray',
    oceancolor='lightblue',
    coastlinecolor='gray',
    center=dict(lat=40, lon=180),  # Center on Pacific using positive longitude
    projection_scale=0.6
)
map_fig.update_layout(
    title=dict(
        text="Pacific Station Locations & Wave Δs",
        font=dict(size=16, color='#2c3e50')
    ),
    margin=dict(l=0, r=0, t=50, b=0),
    height=400,
    paper_bgcolor="white",
    showlegend=False#,  # Remove legend to save space
    # geo=dict(
    #     # Add padding around the automatically fitted bounds for better view
    #     lonaxis=dict(range=[min(station_lons + [epicenter_lon]) - 10, max(station_lons + [epicenter_lon]) + 10]),
    #     lataxis=dict(range=[min(station_lats + [epicenter_lat]) - 5, max(station_lats + [epicenter_lat]) + 5])
    # )
)

# Animation frames for map
map_frames = []
for i, t in enumerate(all_frames):
    frame_y = df_pivot_interp.iloc[i].values.tolist()
    sizes = [max(12, min(35, abs(val)*20)) for val in frame_y]  # match improved sizing
    colors = frame_y
    map_frames.append(go.Frame(
        data=[
            # Epicenter (static)
            go.Scattergeo(
                lon=[epicenter_lon],
                lat=[epicenter_lat],
                text=['🌋 Earthquake<br>Epicenter'],
                marker=dict(
                    size=20,
                    color='red',
                    symbol='star',
                    line=dict(width=2, color='darkred')
                ),
                mode='markers+text',
                textposition="bottom center",
                textfont=dict(size=12, color='darkred'),
                showlegend=False
            ),
            # Stations (animated)
            go.Scattergeo(
                lon=station_lons,
                lat=station_lats,
                marker=dict(
                    size=sizes,
                    color=colors,
                    colorscale='RdBu',
                    cmin=y_range[0],
                    cmax=y_range[1],
                    line=dict(width=2, color='black'),
                    symbol='circle'
                ),
                text=[f'📊 {name}' for name in station_order],
                mode='markers+text',
                textposition="top center",
                textfont=dict(size=10, color='black'),
                showlegend=False
            )
        ],
        name=str(t)
    ))
map_fig.frames = map_frames
# Map animation controlled by unified dashboard controls

# --- Dash Layout with Map ---
from dash.dependencies import Input, Output

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
        html.P("🌋 Earthquake: 29 July 2025, 23:24:52 UTC | 📍 52.473°N, 160.396°E | ⏰ Timeline: Earthquake to July 31 00:00",
               style={'margin': '0', 'color': '#e74c3c', 'fontSize': '1.0rem', 'fontWeight': 'bold'})
    ], style={'textAlign': 'center', 'padding': '20px', 'background': 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)', 
              'borderRadius': '10px', 'marginBottom': '25px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}),
    
    # Master Control Panel
    html.Div([
        html.H3("🎮 Animation Controls", style={'margin': '0 0 15px 0', 'color': '#34495e', 'fontSize': '1.3rem'}),
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
                    })
                ], style={'display': 'flex', 'alignItems': 'center'})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),
            
            html.Div([
                html.Label("Timeline Navigation:", style={'fontSize': '14px', 'fontWeight': 'bold', 'color': '#2c3e50', 'marginBottom': '10px', 'display': 'block'}),
                # html.P("🌋 Red marker shows earthquake occurrence", style={'fontSize': '12px', 'color': '#e74c3c', 'margin': '5px 0', 'fontStyle': 'italic'}),
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
            dcc.Graph(id="overview-map", style={'height': '400px'}),
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingRight': '2%'}),
        
        # Right Column - Wave Propagation Analysis
        html.Div([
            html.H3("📊 Wave Propagation Analysis", style={'color': '#2c3e50', 'marginBottom': '15px', 'fontSize': '1.2rem'}),
            dcc.Graph(id="wave-graph", style={'height': '400px'}),
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingLeft': '2%'}),
    ]),
    
    # Bottom Row - Station Time Series (Full Width)
    html.Div([
        html.H3("📈 Station Time Series", style={'color': '#2c3e50', 'marginTop': '30px', 'marginBottom': '15px', 'fontSize': '1.2rem'}),
        html.P("Individual wave height anomalies (observed - predicted) for each monitoring station",
               style={'color': '#7f8c8d', 'fontSize': '0.9rem', 'marginBottom': '15px', 'fontStyle': 'italic'}),
        dcc.Graph(id="timeseries-graph", style={'height': '600px'}),
    ], style={'width': '100%', 'marginTop': '20px'}),
    
    # Footer Info
    html.Div([
        html.P([
           # "📍 Earthquake to July 31 00:00 UTC (52.473°N, 160.396°E) | ",
            "📊 Data Source: NOAA CO-OPS API | ",
            "⏱️ Update Frequency: 1-minute intervals | "#,
            #"🏝️ Excluded stations: Apra Harbor, Pago Bay, Pearl Harbor, Mokuoloe"
        ], style={'margin': '0', 'color': '#95a5a6', 'fontSize': '0.9rem', 'textAlign': 'center'})
    ], style={'marginTop': '30px', 'padding': '15px', 'background': '#ecf0f1', 'borderRadius': '8px'}),
    
    dcc.Interval(id="interval", interval=50, n_intervals=0, disabled=True)
], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '20px', 'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#f8f9fa'})

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
    Output("timeline-clock", "children"),
    [Input("frame-slider", "value")]
)
def update_timeline_clock(frame_index):
    """Update the clock display with current timeline time"""
    if frame_index is None or frame_index >= len(all_frames):
        return "Loading..."
    
    current_time = all_frames[frame_index]
    # Format as: "Jul 29, 23:24 UTC" 
    formatted_time = current_time.strftime("%b %d, %H:%M UTC")
    return formatted_time

@app.callback(
    [Output("overview-map", "figure"), Output("wave-graph", "figure"), Output("timeseries-graph", "figure")],
    [Input("frame-slider", "value")]
)
def update_all_figures(frame_idx):
    t = all_frames[frame_idx]
    # --- Update overview map ---
    frame_y = df_pivot_interp.loc[t].values.tolist()
    sizes = [max(12, min(35, abs(val)*20)) for val in frame_y]  # match improved sizing
    colors = frame_y
    map_fig_c = map_fig.to_dict()
    # Update only the stations trace (index 1), epicenter (index 0) stays static
    map_fig_c['data'][1]['marker']['size'] = sizes
    map_fig_c['data'][1]['marker']['color'] = colors
    # --- Update oscilloscope ---
    x = [float(d) for d in distances]
    y = [float(v) for v in frame_y]
    fig_c = fig.to_dict()
    fig_c['data'][0]['x'] = x
    fig_c['data'][0]['y'] = y
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
    return map_fig_c, fig_c, fig_ts

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

if __name__ == "__main__":
    app.run(debug=True)
