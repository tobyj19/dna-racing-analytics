import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Race History", page_icon="🏁", layout="wide")

st.title("🏁 Race History & Charts")
st.markdown("Interactive visualizations of position distributions and finish times")

# Global averages by class (cb values)
GLOBAL_AVERAGES = {
    9: 50.3, 10: 56.9, 11: 63.8, 12: 70.5, 13: 76.8, 14: 82.8,
    15: 88.8, 16: 94.6, 17: 100.9, 18: 106.8, 19: 112.7, 20: 118.9,
    21: 124.4, 22: 130.7, 23: 137.6
}

# Check if core data exists
if 'mini' not in st.session_state or 'races' not in st.session_state:
    st.warning("⚠️ No core data loaded. Please search for a core in the **Core Search** page first.")
    st.stop()

mini = st.session_state.mini
races = st.session_state.races

st.header(f"Race Data for Core #{mini['hid']} - {mini.get('name', 'Unnamed')}")

# Mode selection
mode = st.selectbox("Select Racing Mode", ["bike", "car", "horse"], index=0, key="race_mode")

mode_races = [r for r in races if r.get('rvmode') == mode and r.get('cb') and r.get('pos')]

if not mode_races:
    st.warning(f"⚠️ No race data available for {mode.upper()} mode")
    st.stop()

st.divider()

# Group by distance
distance_data = {}
for race in mode_races:
    cb = race['cb']
    if cb not in distance_data:
        distance_data[cb] = []
    distance_data[cb].append(race['pos'])

sorted_distances = sorted(distance_data.keys(), key=lambda x: int(x) if isinstance(x, (int, float, str)) else x)

# Create combined charts for each distance
for dist_idx, distance in enumerate(sorted_distances):
    distance = int(distance)  # Ensure distance is an integer
    positions = distance_data[distance]
    
    # Count positions 1-14
    position_counts = {i: 0 for i in range(1, 15)}
    for pos in positions:
        if 1 <= pos <= 14:
            position_counts[pos] += 1
    
    # Calculate win percentage and avg odds
    wins = position_counts[1]
    win_pct = (wins / len(positions) * 100) if positions else 0
    
    # Get timing data for this distance
    times = sorted([r['time'] for r in mode_races if r.get('cb') == distance and r.get('time')])
    
    # Calculate average odds
    odds_races = [r for r in mode_races if r['cb'] == distance and r.get('odds')]
    avg_odds = sum(r['odds'] for r in odds_races) / len(odds_races) if odds_races else None
    
    # Create title with distance, race count, and avg odds
    title = f"**{distance * 100}m** ({len(positions)} races)"
    if avg_odds:
        title += f" • Avg Odds: {avg_odds:.2f}"
    
    st.markdown(f"### {title}")
    
    # Position Distribution Chart
    fig_pos = go.Figure(data=[
        go.Bar(
            x=list(position_counts.keys()),
            y=list(position_counts.values()),
            marker_color=['#667eea' if i == 1 else '#764ba2' if i == 2 else '#f59e0b' if i == 3 else '#969696' 
                         for i in position_counts.keys()],
            text=list(position_counts.values()),
            textposition='auto',
            hovertemplate='Position %{x}<br>Finishes: %{y}<extra></extra>'
        )
    ])
    
    fig_pos.update_layout(
        title=f"Win Rate: {win_pct:.1f}%",
        xaxis_title="Finish Position",
        yaxis_title="Number of Finishes",
        height=300,
        showlegend=False,
        xaxis=dict(tickmode='linear', tick0=1, dtick=1),
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    st.plotly_chart(fig_pos, use_container_width=True, key=f"pos_{mode}_{dist_idx}")
    
    # Finish Times Distribution (if timing data exists)
    if times:
        fastest = times[0]
        slowest = times[-1]
        average = sum(times) / len(times)
        global_avg = GLOBAL_AVERAGES.get(distance)
        
        # Create timeline chart
        fig_timing = go.Figure()
        
        # Horizontal line
        fig_timing.add_trace(go.Scatter(
            x=[fastest, slowest],
            y=[0, 0],
            mode='lines',
            line=dict(color='#569cd6', width=4),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Points
        points = [
            (fastest, 'Fastest', '#4ec9b0'),
            (average, 'Average', '#dcdcaa'),
            (slowest, 'Slowest', '#f48771')
        ]
        
        if global_avg:
            points.insert(2, (global_avg, 'Global Avg', '#c586c0'))
        
        for time, label, color in points:
            fig_timing.add_trace(go.Scatter(
                x=[time],
                y=[0],
                mode='markers',
                marker=dict(size=15, color=color),
                name=label,
                text=f"{label}: {time:.2f}s",
                hovertemplate='%{text}<extra></extra>'
            ))
        
        fig_timing.update_layout(
            title="Finish Times Distribution",
            xaxis_title="Time (seconds)",
            yaxis=dict(visible=False, range=[-0.2, 0.2]),
            height=200,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        st.plotly_chart(fig_timing, use_container_width=True, key=f"timing_{mode}_{dist_idx}")
    
    st.divider()

st.info("💡 Tip: Points closer to the left (faster times) indicate better performance. Compare your average to the global average!")
