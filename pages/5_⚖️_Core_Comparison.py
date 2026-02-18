import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Core Comparison", page_icon="⚖️", layout="wide")

st.title("⚖️ Core Comparison")
st.markdown("Compare up to 3 cores side-by-side to find the best performer")

fetch_core_data = st.session_state.fetch_core_data
GLOBAL_AVERAGES = st.session_state.GLOBAL_AVERAGES

# Input section
st.subheader("Select Cores to Compare")

col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

with col1:
    core_1 = st.number_input("Core 1 ID", min_value=1, value=192, step=1, key="compare_1")

with col2:
    core_2 = st.number_input("Core 2 ID", min_value=1, value=10, step=1, key="compare_2")

with col3:
    core_3 = st.number_input("Core 3 ID (optional)", min_value=0, value=0, step=1, key="compare_3")

with col4:
    st.write("")
    st.write("")
    compare_btn = st.button("⚖️ Compare", type="primary", use_container_width=True)

if not compare_btn and 'comparison_data' not in st.session_state:
    st.info("👆 Enter 2-3 Core IDs above and click 'Compare' to begin")
    
    with st.expander("💡 Comparison Features"):
        st.markdown("""
        This tool will compare:
        - ✅ Power statistics across all modes
        - ✅ Total race counts
        - ✅ Win rates by mode
        - ✅ Average positions
        - ✅ Best performing distances
        - ✅ Performance vs global averages
        """)
    st.stop()

if compare_btn:
    cores_to_fetch = [core_1, core_2]
    if core_3 > 0:
        cores_to_fetch.append(core_3)
    
    comparison_data = []
    
    with st.spinner("Fetching data for all cores..."):
        for core_id in cores_to_fetch:
            mini, power, stats, races = fetch_core_data(core_id)
            
            if mini and power and races:
                comparison_data.append({
                    'id': core_id,
                    'mini': mini,
                    'power': power,
                    'stats': stats,
                    'races': races
                })
            else:
                st.error(f"Failed to load Core #{core_id}")
    
    if len(comparison_data) < 2:
        st.error("Need at least 2 valid cores to compare")
        st.stop()
    
    st.session_state.comparison_data = comparison_data

# Display comparison
if 'comparison_data' in st.session_state:
    comparison_data = st.session_state.comparison_data
    
    st.success(f"✓ Comparing {len(comparison_data)} cores")
    st.divider()
    
    # Basic Info Comparison
    st.subheader("📋 Basic Information")
    
    cols = st.columns(len(comparison_data))
    
    for idx, data in enumerate(comparison_data):
        mini = data['mini']
        with cols[idx]:
            st.markdown(f"### Core #{mini['hid']}")
            st.markdown(f"**Name:** {mini.get('name', 'Unnamed')}")
            st.markdown(f"**Type:** {mini['type'].title()}")
            st.markdown(f"**Element:** {mini['element'].title()}")
            st.markdown(f"**Gender:** {mini['gender'].title()}")
            st.markdown(f"**Color:** {mini['color'].replace('-', ' ').title()}")
    
    st.divider()
    
    # Power Statistics Comparison
    st.subheader("⚡ Power Statistics Comparison")
    
    mode_tabs = st.tabs(["🏍️ Bike", "🏎️ Car", "🐎 Horse"])
    
    for mode_idx, mode in enumerate(['bike', 'car', 'horse']):
        with mode_tabs[mode_idx]:
            # Create comparison chart
            metrics = ['power', 'variance', 'adjodds']
            metric_names = ['Power', 'Variance', 'Adj Odds']
            
            fig = go.Figure()
            
            for data in comparison_data:
                mini = data['mini']
                power = data['power']
                
                if mode in power['power']:
                    mode_data = power['power'][mode]
                    values = [
                        mode_data['power']['fill']['per'],
                        mode_data['variance']['fill']['per'],
                        mode_data['adjodds']['fill']['per']
                    ]
                    
                    fig.add_trace(go.Bar(
                        name=f"Core #{mini['hid']}",
                        x=metric_names,
                        y=values,
                        text=[f"{v:.1f}%" for v in values],
                        textposition='auto',
                    ))
            
            fig.update_layout(
                title=f"{mode.upper()} Power Comparison",
                yaxis_title="Percentage",
                barmode='group',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Race Statistics
    st.subheader("🏁 Race Statistics")
    
    race_stats = []
    for data in comparison_data:
        mini = data['mini']
        races = data['races']
        
        mode_counts = {}
        for race in races:
            mode = race.get('rvmode', 'unknown')
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        race_stats.append({
            'Core ID': f"#{mini['hid']}",
            'Name': mini.get('name', 'Unnamed'),
            'Total Races': len(races),
            'Bike': mode_counts.get('bike', 0),
            'Car': mode_counts.get('car', 0),
            'Horse': mode_counts.get('horse', 0)
        })
    
    df_races = pd.DataFrame(race_stats)
    st.dataframe(df_races, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Performance Comparison (Best Distance Analysis)
    st.subheader("🎯 Best Distance Comparison")
    
    mode_select = st.selectbox("Select Mode for Comparison", ["bike", "car", "horse"], key="comp_mode")
    
    def calc_best_for_core(races_list, selected_mode):
        """Calculate best distance for a single core"""
        mode_races = [r for r in races_list if r.get('rvmode') == selected_mode and r.get('cb') and r.get('pos') and r.get('time')]
        
        distance_data = {}
        for race in mode_races:
            cb = race['cb']
            if cb not in distance_data:
                distance_data[cb] = {'positions': [], 'times': []}
            distance_data[cb]['positions'].append(race['pos'])
            distance_data[cb]['times'].append(race['time'])
        
        best_distance = None
        best_score = 0
        
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
            
            if weighted_score > best_score:
                best_score = weighted_score
                best_distance = {
                    'distance': cb * 100,
                    'score': weighted_score,
                    'win_rate': win_rate * 100,
                    'avg_pos': avg_position,
                    'races': len(positions)
                }
        
        return best_distance
    
    cols = st.columns(len(comparison_data))
    
    for idx, data in enumerate(comparison_data):
        mini = data['mini']
        races = data['races']
        
        with cols[idx]:
            st.markdown(f"### Core #{mini['hid']}")
            
            best = calc_best_for_core(races, mode_select)
            
            if best:
                st.metric("🥇 Best Distance", f"{best['distance']}m")
                st.metric("Score", f"{best['score']:.1f}/100")
                st.metric("Win Rate", f"{best['win_rate']:.1f}%")
                st.metric("Avg Position", f"{best['avg_pos']:.2f}")
                st.caption(f"Based on {best['races']} races")
            else:
                st.warning(f"Not enough data for {mode_select.upper()}")
    
    st.divider()
    
    # Winner determination
    st.subheader("🏆 Comparison Summary")
    
    st.info("💡 **Tip:** The core with the highest weighted score at its best distance is typically the best overall performer for that mode.")
    
    # Reset button
    if st.button("🔄 Compare Different Cores"):
        del st.session_state.comparison_data
        st.rerun()
