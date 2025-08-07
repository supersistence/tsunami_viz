#!/usr/bin/env python3
"""
SIMPLE OSCILLOSCOPE DEMO - Based on proven Dash animation patterns
This demonstrates the basic structure that SHOULD work fast
"""

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import time

# Create simple synthetic data
n_frames = 100
n_stations = 5
times = pd.date_range('2025-01-01', periods=n_frames, freq='1min')
stations = [f'Station_{i}' for i in range(n_stations)]

# Generate synthetic wave data
data = []
for i, t in enumerate(times):
    for j, station in enumerate(stations):
        wave_value = np.sin(i * 0.1 + j) * np.random.normal(1, 0.1)
        data.append({'time': t, 'station': station, 'wave': wave_value})

df = pd.DataFrame(data)

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("🌊 Simple Oscilloscope Demo"),
    
    html.Div([
        html.Button('▶️ Play', id='play-btn', style={'marginRight': '10px'}),
        html.Span(f"Frame: ", style={'marginRight': '10px'}),
        html.Span("0", id='frame-display', style={'fontWeight': 'bold'}),
    ], style={'margin': '20px 0'}),
    
    dcc.Graph(id='wave-chart', style={'height': '400px'}),
    
    dcc.Slider(
        id='frame-slider',
        min=0,
        max=n_frames-1,
        value=0,
        step=1,
        marks={i: str(i) for i in range(0, n_frames, 10)}
    ),
    
    # CRITICAL: Simple interval with reasonable speed
    dcc.Interval(
        id='interval',
        interval=100,  # 100ms = 10 fps
        n_intervals=0,
        disabled=True
    ),
    
    # Store for play state
    dcc.Store(id='play-state', data={'playing': False, 'frame': 0})
])

@app.callback(
    [Output('play-state', 'data'), Output('interval', 'disabled')],
    [Input('play-btn', 'n_clicks')],
    prevent_initial_call=True
)
def toggle_play(n_clicks):
    """Toggle play/pause"""
    if n_clicks is None:
        return {'playing': False, 'frame': 0}, True
    
    # Toggle state
    playing = (n_clicks % 2) == 1
    print(f"🎮 Play clicked: {n_clicks}, Playing: {playing}")
    
    return {'playing': playing, 'frame': 0}, not playing

@app.callback(
    Output('play-state', 'data', allow_duplicate=True),
    [Input('interval', 'n_intervals')],
    prevent_initial_call=True
)
def advance_frame(n_intervals):
    """Advance to next frame"""
    if n_intervals is None:
        return dash.no_update
    
    frame = n_intervals % n_frames
    print(f"⏱️ Interval {n_intervals} → Frame {frame}")
    
    return {'playing': True, 'frame': frame}

@app.callback(
    [Output('frame-slider', 'value'), Output('frame-display', 'children'), Output('wave-chart', 'figure')],
    [Input('play-state', 'data')]
)
def update_display(play_data):
    """Update all visual elements"""
    start_time = time.time()
    
    frame = play_data.get('frame', 0)
    current_time = times[frame]
    
    # Get current frame data
    frame_data = df[df['time'] == current_time]
    
    # Create simple line chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=frame_data['station'],
        y=frame_data['wave'],
        mode='lines+markers',
        line=dict(color='blue', width=3),
        marker=dict(size=8, color='red')
    ))
    
    fig.update_layout(
        title=f"Wave Data - Frame {frame} - {current_time}",
        xaxis_title="Station",
        yaxis_title="Wave Height",
        yaxis=dict(range=[-3, 3]),
        height=400
    )
    
    elapsed = time.time() - start_time
    print(f"🔄 Display update: {elapsed*1000:.1f}ms (frame {frame})")
    
    return frame, str(frame), fig

if __name__ == '__main__':
    print("🚀 Starting Simple Oscilloscope Demo")
    print("📱 Visit: http://localhost:8051")
    app.run(debug=True, port=8051)