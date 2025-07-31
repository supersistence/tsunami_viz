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
with open("pivoted_wave_data.pkl", "rb") as f:
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

app.layout = html.Div([
    html.H1("Tsunami Wave Propagation: Oscilloscope Animation"),
    dcc.Graph(id="wave-graph", figure=fig),
    # html.H3("Recent Data (last 10 time steps)"),
    # dash_table.DataTable(
    #     id="pivoted-data-table",
    #     columns=[{"name": col, "id": col} for col in preview_df_reset.columns],
    #     data=preview_df_reset.to_dict("records"),
    #     page_size=preview_rows,
    #     style_table={"overflowX": "auto", "maxHeight": "400px", "overflowY": "auto"},
    #     style_cell={"fontSize": 12, "textAlign": "center", "minWidth": "80px", "maxWidth": "120px"},
    #     style_header={"backgroundColor": "#eee", "fontWeight": "bold"},
    # ),
    html.H3("Time Series: Wave Height at Each Station"),
    dcc.Graph(id="timeseries-graph", figure=station_timeseries_fig),
    dcc.Interval(id="interval", interval=1000, n_intervals=0)
])

if __name__ == "__main__":
    app.run(debug=True)
