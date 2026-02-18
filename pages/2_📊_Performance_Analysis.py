import streamlit as st
import pandas as pd

st.set_page_config(page_title="Performance Analysis", page_icon="📊", layout="wide")

st.title("📊 Performance Analysis")
st.markdown("Find the best distances for your core using advanced statistical methods")

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

st.header(f"Analysis for Core #{mini['hid']} - {mini.get('name', 'Unnamed')}")

# Mode selection
mode = st.selectbox("Select Racing Mode", ["bike", "car", "horse"], index=0)

st.divider()

# Calculate analysis
def calculate_best_distance(races_list, selected_mode):
    mode_races = [r for r in races_list if r.get('rvmode') == selected_mode and r.get('cb') and r.get('pos') and r.get('time')]
    
    distance_data = {}
    for race in mode_races:
        cb = race['cb']
        if cb not in distance_data:
            distance_data[cb] = {'positions': [], 'times': []}
        distance_data[cb]['positions'].append(race['pos'])
        distance_data[cb]['times'].append(race['time'])
    
    results = []
    for cb, data in distance_data.items():
        positions = data['positions']
        times = data['times']
        
        if len(positions) < 20:
            continue
        
        wins = sum(1 for p in positions if p == 1)
        win_rate = wins / len(positions)
        avg_position = sum(positions) / len(positions)
        avg_time = sum(times) / len(times)
        sorted_times = sorted(times)
        time_range = sorted_times[-1] - sorted_times[0]
        consistency = 1 - (time_range / avg_time)
        
        win_rate_score = win_rate * 100
        position_score = (15 - avg_position) / 14 * 100
        consistency_score = consistency * 100
        
        vs_global_score = 50
        if cb in GLOBAL_AVERAGES:
            diff = (GLOBAL_AVERAGES[cb] - avg_time) / GLOBAL_AVERAGES[cb]
            vs_global_score = 50 + (diff * 100)
        
        weighted_score = (
            win_rate_score * 0.40 +
            position_score * 0.30 +
            consistency_score * 0.20 +
            vs_global_score * 0.10
        )
        
        percentile_rank = None
        vs_global_time = None
        if cb in GLOBAL_AVERAGES:
            percentile_rank = ((avg_time - GLOBAL_AVERAGES[cb]) / GLOBAL_AVERAGES[cb] * 100)
            vs_global_time = avg_time - GLOBAL_AVERAGES[cb]
        
        results.append({
            'Distance': f"{cb * 100}m",
            'CB': cb,
            'Races': len(positions),
            'Win Rate': f"{win_rate * 100:.1f}%",
            'Avg Position': f"{avg_position:.2f}",
            'Avg Time': f"{avg_time:.2f}s",
            'Consistency': f"{consistency * 100:.1f}%",
            'Weighted Score': weighted_score,
            'vs Global %': percentile_rank if percentile_rank is not None else None,
            'vs Global Time': vs_global_time,
        })
    
    return pd.DataFrame(results)

df = calculate_best_distance(races, mode)

if df.empty:
    st.warning(f"⚠️ Not enough data for {mode.upper()} mode. Minimum 20 races per distance required.")
    st.info("Try selecting a different mode or use a core with more race history.")
    st.stop()

# Method comparison
col1, col2 = st.columns(2)

# Method 1
with col1:
    st.subheader("🏆 Method 1: Weighted Performance")
    st.caption("Formula: Win Rate (40%) + Position (30%) + Consistency (20%) + vs Global (10%)")
    
    df_sorted = df.sort_values('Weighted Score', ascending=False)
    best = df_sorted.iloc[0]
    
    st.metric(
        "🥇 Best Distance",
        best['Distance'],
        delta=f"Score: {best['Weighted Score']:.1f}/100",
        delta_color="off"
    )
    
    st.markdown(f"""
    **Performance Breakdown:**
    - 🏁 **{best['Races']} total races**
    - 🏆 **{best['Win Rate']} win rate**
    - 📍 **{best['Avg Position']} avg position**
    - 🎯 **{best['Consistency']} consistency**
    """)

# Method 3
with col2:
    st.subheader("🌍 Method 3: vs Global Average")
    st.caption("Identifies where you're most dominant compared to the network")
    
    df_global = df[df['vs Global %'].notna()].sort_values('vs Global %', ascending=True)
    
    if not df_global.empty:
        best_global = df_global.iloc[0]
        
        is_faster = best_global['vs Global %'] < 0
        delta_color = "normal" if is_faster else "inverse"
        
        st.metric(
            "🥇 Best Distance",
            best_global['Distance'],
            delta=f"{best_global['vs Global %']:+.2f}% vs Network",
            delta_color=delta_color
        )
        
        st.markdown(f"""
        **Global Comparison:**
        - 🏁 **{best_global['Races']} total races**
        - ⚡ **{best_global['Avg Time']}** your avg time
        - 🌍 **{GLOBAL_AVERAGES[best_global['CB']]:.2f}s** global avg
        - {'🟢 **Faster than average!**' if is_faster else '🔴 **Slower than average**'}
        """)
    else:
        st.info("No global comparison data available for this mode")

st.divider()

# Full rankings table
st.subheader("📋 Complete Distance Rankings")

# Prepare display dataframe
display_df = df.sort_values('Weighted Score', ascending=False).copy()

# Format for display
display_df['Weighted Score'] = display_df['Weighted Score'].apply(lambda x: f"{x:.1f}")
display_df['vs Global %'] = display_df['vs Global %'].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A")

# Select columns to display
display_cols = ['Distance', 'Races', 'Win Rate', 'Avg Position', 'Avg Time', 'Consistency', 'Weighted Score', 'vs Global %']
display_df = display_df[display_cols]

# Style the dataframe
st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    height=400
)

st.divider()

# Recommendations
st.subheader("💡 Recommendations")

top_3 = df.sort_values('Weighted Score', ascending=False).head(3)

col1, col2, col3 = st.columns(3)

for idx, (_, row) in enumerate(top_3.iterrows()):
    with [col1, col2, col3][idx]:
        medal = ["🥇", "🥈", "🥉"][idx]
        st.markdown(f"### {medal} {row['Distance']}")
        st.markdown(f"**Score:** {row['Weighted Score']:.1f}/100")
        st.markdown(f"**Win Rate:** {row['Win Rate']}")
        st.markdown(f"**Races:** {row['Races']}")
        
        if pd.notna(row['vs Global %']):
            if row['vs Global %'] < 0:
                st.success(f"💪 {abs(row['vs Global %']):.1f}% faster than global avg")
            else:
                st.warning(f"⚠️ {row['vs Global %']:.1f}% slower than global avg")

st.info("🏁 Navigate to **Race History** to see detailed position distributions and timing charts!")
