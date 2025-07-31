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
with open("data/pivotdata/restructured_data.pkl", "rb") as f:
    pivoted = pickle.load(f)
df_pivot = pivoted['df_pivot']  # index: t, columns: station, values: delta
station_order = pivoted['station_order']
station_distances = pivoted['station_distance']

# Remove Pago Pago and Kwajalein if present
if 'Pago Pago' in df_pivot.columns:
    df_pivot = df_pivot.drop(columns=['Pago Pago'])
if 'Kwajalein' in df_pivot.columns:
    df_pivot = df_pivot.drop(columns=['Kwajalein'])

# Filter to times from 2025-07-29 12:00 onward
import pandas as pd
df_pivot = df_pivot[df_pivot.index >= pd.Timestamp('2025-07-29 12:00')]

# Sort columns and distances
station_order = [s for s in station_order if s in df_pivot.columns]
distances = [station_distances[s] for s in station_order]

# Get all frames (times)
all_frames = df_pivot.index.sort_values()

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
    showlegend=True
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

# Add station labels as annotations after layout, using yref='paper' to keep them above plot
for i, x in enumerate(distances):
    fig.add_annotation(
        x=x,
        y=1.02,  # a bit above the top of the plot area
        yref="paper",
        text=station_order[i],
        showarrow=False,
        yanchor="bottom",
        textangle=45,
        font=dict(size=10, color="black")
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
    title="Tsunami Wave Propagation: Oscilloscope Animation",
    xaxis_title="Distance from Epicenter (km)",
    yaxis_title="Δ Wave Height (m)",
    yaxis=dict(range=y_range, fixedrange=True, zeroline=False, autorange=False),
    xaxis=dict(range=[min(distances), max(distances)], fixedrange=True),
    updatemenus=[{
        "type": "buttons",
        "buttons": [{
            "label": "Play",
            "method": "animate",
            "args": [None, {"frame": {"duration": 50, "redraw": True}, "fromcurrent": True}]
        }, {
            "label": "Pause",
            "method": "animate",
            "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate", "transition": {"duration": 0}}]
        }]
    }],
    sliders=[{
        "steps": [
            {"args": [[str(t)], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}], "label": str(t), "method": "animate"}
            for t in all_frames
        ],
        "transition": {"duration": 0},
        "x": 0.1,
        "len": 0.9,
        "xanchor": "left",
        "y": 0,
        "yanchor": "top"
    }],
    height=600,
    plot_bgcolor="white"
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
    height=150*len(station_order),
    title="Wave Height Time Series for Each Station",
    xaxis_title="Time (UTC)",
    yaxis_title="Δ Wave Height (m)",
    margin=dict(t=40, b=40, l=60, r=20)
)

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

# Prepare initial map frame
map_marker_sizes = [max(8, min(30, abs(y0[i])*15)) for i in range(len(y0))]  # scale delta for size
map_marker_colors = y0  # use delta directly for color

map_fig = go.Figure()
map_fig.add_trace(go.Scattergeo(
    lon=station_lons,
    lat=station_lats,
    text=station_order,
    marker=dict(
        size=map_marker_sizes,
        color=map_marker_colors,
        colorscale='RdBu',
        cmin=y_range[0],
        cmax=y_range[1],
        colorbar=dict(title="Δ Wave Height (m)", len=0.5, y=0.7),
        line=dict(width=1, color='black')
    ),
    mode='markers+text',
    textposition="top center",
    name='Stations',
    showlegend=False
))
map_fig.update_geos(
    projection_type="natural earth",
    showcountries=True, showcoastlines=True, showland=True, fitbounds="locations"
)
map_fig.update_layout(
    title="Station Overview Map (Animated)",
    margin=dict(l=0, r=0, t=40, b=0),
    height=350
)

# Animation frames for map
map_frames = []
for i, t in enumerate(all_frames):
    frame_y = df_pivot_interp.iloc[i].values.tolist()
    sizes = [max(8, min(30, abs(val)*15)) for val in frame_y]
    colors = frame_y
    map_frames.append(go.Frame(
        data=[go.Scattergeo(
            lon=station_lons,
            lat=station_lats,
            marker=dict(
                size=sizes,
                color=colors,
                colorscale='RdBu',
                cmin=y_range[0],
                cmax=y_range[1],
                line=dict(width=1, color='black')
            ),
            text=station_order,
            mode='markers+text',
            textposition="top center",
            showlegend=False
        )],
        name=str(t)
    ))
map_fig.frames = map_frames
map_fig.update_layout(
    updatemenus=[{
        "type": "buttons",
        "buttons": [{
            "label": "Play",
            "method": "animate",
            "args": [None, {"frame": {"duration": 50, "redraw": True}, "fromcurrent": True}]
        }, {
            "label": "Pause",
            "method": "animate",
            "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate", "transition": {"duration": 0}}]
        }]
    }],
    sliders=[{
        "steps": [
            {"args": [[str(t)], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}], "label": str(t), "method": "animate"}
            for t in all_frames
        ],
        "transition": {"duration": 0},
        "x": 0.1,
        "len": 0.9,
        "xanchor": "left",
        "y": 0,
        "yanchor": "top"
    }]
)

# --- Dash Layout with Map ---
from dash.dependencies import Input, Output

from dash.dependencies import Input, Output, State

# Remove per-figure animation controls from map_fig and fig
map_fig.update_layout(updatemenus=[], sliders=[])
fig.update_layout(updatemenus=[], sliders=[])

app.layout = html.Div([
    html.H1("Tsunami Wave Propagation: Oscilloscope Animation"),
    html.Div([
        html.Button('Play', id='play-btn', n_clicks=0, style={'marginRight': '10px'}),
        html.Button('Pause', id='pause-btn', n_clicks=0, style={'marginRight': '20px'}),
        dcc.Slider(
            id="frame-slider",
            min=0,
            max=len(all_frames)-1,
            value=0,
            marks={i: str(all_frames[i])[:16] for i in range(0, len(all_frames), max(1, len(all_frames)//10))},
            step=1,
            updatemode='drag'
        ),
    ], style={"marginBottom": "20px"}),
    dcc.Graph(id="overview-map"),
    dcc.Graph(id="wave-graph"),
    html.H3("Time Series: Wave Height at Each Station"),
    dcc.Graph(id="timeseries-graph"),
    dcc.Interval(id="interval", interval=100, n_intervals=0, disabled=True)
])

@app.callback(
    Output("interval", "disabled"),
    [Input("play-btn", "n_clicks"), Input("pause-btn", "n_clicks")],
    [State("interval", "disabled")]
)
def toggle_play_pause(play_clicks, pause_clicks, interval_disabled):
    # Play enables interval, pause disables it
    ctx = dash.callback_context
    if not ctx.triggered:
        return True
    btn_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if btn_id == 'play-btn':
        return False
    elif btn_id == 'pause-btn':
        return True
    return interval_disabled

@app.callback(
    Output("frame-slider", "value"),
    [Input("interval", "n_intervals")],
    [State("frame-slider", "value")]
)
def advance_frame(n_intervals, slider_val):
    if slider_val is None:
        return 0
    next_val = slider_val + 1
    if next_val >= len(all_frames):
        return 0  # loop back to start
    return next_val

@app.callback(
    [Output("overview-map", "figure"), Output("wave-graph", "figure"), Output("timeseries-graph", "figure")],
    [Input("frame-slider", "value")]
)
def update_all_figures(frame_idx):
    t = all_frames[frame_idx]
    # --- Update overview map ---
    frame_y = df_pivot_interp.loc[t].values.tolist()
    sizes = [max(8, min(30, abs(val)*15)) for val in frame_y]
    colors = frame_y
    map_fig_c = map_fig.to_dict()
    map_fig_c['data'][0]['marker']['size'] = sizes
    map_fig_c['data'][0]['marker']['color'] = colors
    # --- Update oscilloscope ---
    x = [float(d) for d in distances]
    y = [float(v) for v in frame_y]
    fig_c = fig.to_dict()
    fig_c['data'][0]['x'] = x
    fig_c['data'][0]['y'] = y
    # --- Update time series with vertical line ---
    fig_ts = station_timeseries_fig.to_dict()
    shapes = []
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

if __name__ == "__main__":
    app.run(debug=True)
