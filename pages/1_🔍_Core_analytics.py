import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from typing import Optional, Tuple, List, Dict
from datetime import datetime, timedelta

st.set_page_config(page_title="Core Analytics", page_icon="🔍", layout="wide")

# Global constants
GLOBAL_AVERAGES = {
    9: 50.3, 10: 56.9, 11: 63.8, 12: 70.5, 13: 76.8, 14: 82.8,
    15: 88.8, 16: 94.6, 17: 100.9, 18: 106.8, 19: 112.7, 20: 118.9,
    21: 124.4, 22: 130.7, 23: 137.6
}

API_BASE_URL = "https://api.dnaracing.run/fbike"

# Helper functions
def fetch_api(endpoint: str, data: dict) -> Optional[dict]:
    """Fetch data from DNA Racing API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        if result.get("status") == "success":
            return result.get("result")
        return None
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None


def fetch_core_data(hid: int) -> Tuple[Optional[dict], Optional[dict], Optional[dict], Optional[list]]:
    """Fetch all core data"""
    with st.spinner(f"Fetching data for Core #{hid}..."):
        mini = fetch_api("/cores/mini", {"hid": hid})
        power = fetch_api("/cores/power", {"hid": hid})
        stats = fetch_api("/cores/racing_stats", {"hid": hid})
        races = fetch_api("/i/hraces", {"hid": hid, "limit": 10000})
    
    return mini, power, stats, races


def calculate_pnl(races: List[dict], days: int = 30) -> dict:
    """Calculate P&L from race history"""
    if not races:
        return {'total_races': 0, 'fees_paid': 0, 'prizes_won': 0, 'net_profit': 0, 
                'roi': 0, 'wins': 0, 'win_rate': 0, 'podiums': 0, 'podium_rate': 0}
    
    cutoff = datetime.now() - timedelta(days=days)
    recent = []
    
    for r in races:
        try:
            race_date = datetime.fromisoformat(r.get('start_time', '').replace('Z', '+00:00'))
            if race_date > cutoff:
                recent.append(r)
        except:
            continue
    
    if not recent:
        return {'total_races': 0, 'fees_paid': 0, 'prizes_won': 0, 'net_profit': 0,
                'roi': 0, 'wins': 0, 'win_rate': 0, 'podiums': 0, 'podium_rate': 0}
    
    total_fees = sum(r.get('fee', 0) for r in recent)
    total_prizes = sum(r.get('prize_usd', 0) for r in recent)
    wins = sum(1 for r in recent if r.get('pos') == 1)
    podiums = sum(1 for r in recent if r.get('pos', 99) <= 3)
    
    return {
        'total_races': len(recent),
        'fees_paid': total_fees,
        'prizes_won': total_prizes,
        'net_profit': total_prizes - total_fees,
        'roi': ((total_prizes - total_fees) / total_fees * 100) if total_fees > 0 else 0,
        'wins': wins,
        'win_rate': (wins / len(recent) * 100) if recent else 0,
        'podiums': podiums,
        'podium_rate': (podiums / len(recent) * 100) if recent else 0
    }


# Main App
st.title("🔍 Core Analytics")
st.markdown("Complete analysis of any DNA Racing core")

# Search section
col1, col2 = st.columns([3, 1])

with col1:
    core_id = st.number_input(
        "Enter Core ID (HID)",
        min_value=1,
        value=st.session_state.get('current_core_id', 192),
        step=1,
        help="Enter the core's HID number"
    )

with col2:
    st.write("")
    st.write("")
    search_btn = st.button("🔍 Search Core", type="primary", use_container_width=True)

if search_btn:
    st.session_state.current_core_id = core_id
    
    mini, power, stats, races = fetch_core_data(core_id)
    
    if mini and power and races:
        st.session_state.mini = mini
        st.session_state.power = power
        st.session_state.stats = stats
        st.session_state.races = races
        st.success(f"✓ Successfully loaded Core #{core_id}")
    else:
        st.error("Failed to load core data. Please check the Core ID.")

# Display if data exists
if 'mini' in st.session_state and 'power' in st.session_state:
    mini = st.session_state.mini
    power = st.session_state.power
    stats = st.session_state.stats
    races = st.session_state.races
    
    st.divider()
    
    # ====================
    # SECTION 1: CORE DETAILS
    # ====================
    st.header(f"Core #{mini['hid']} - {mini.get('name', 'Unnamed')}")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("F.No", mini['fno'])
    with col2:
        st.metric("Element", mini['element'].title())
    with col3:
        st.metric("Type", mini['type'].title())
    with col4:
        st.metric("Gender", mini['gender'].title())
    with col5:
        st.metric("Color", mini['color'].replace('-', ' ').title())
    with col6:
        st.metric("Hex", f"#{mini['hex_code']}")
    
    # Power Stats
    st.subheader("⚡ Power Statistics")
    
    # Color gradient function
    def get_gradient_color(percentage):
        """Calculate color: blue (0%) → green (50%) → red (100%)"""
        if percentage <= 50:
            # Blue to Green (0-50%)
            ratio = percentage / 50
            r = 0
            g = int(255 * ratio)
            b = int(255 * (1 - ratio))
        else:
            # Green to Red (50-100%)
            ratio = (percentage - 50) / 50
            r = int(255 * ratio)
            g = int(255 * (1 - ratio))
            b = 0
        return f"#{r:02x}{g:02x}{b:02x}"
    
    mode_cols = st.columns(3)
    
    for idx, mode in enumerate(['bike', 'car', 'horse']):
        if mode not in power['power']:
            continue
        
        with mode_cols[idx]:
            st.markdown(f"### {mode.upper()}")
            mode_data = power['power'][mode]
            
            power_pct = mode_data['power']['fill']['per']
            power_color = get_gradient_color(power_pct)
            st.markdown(f"**Power:** {power_pct:.1f}%")
            st.markdown(f'<div style="background:{power_color};height:25px;border-radius:5px;"></div>', unsafe_allow_html=True)
            
            var_pct = mode_data['variance']['fill']['per']
            var_color = get_gradient_color(var_pct)
            st.markdown(f"**Variance:** {var_pct:.1f}%")
            st.markdown(f'<div style="background:{var_color};height:25px;border-radius:5px;"></div>', unsafe_allow_html=True)
            
            odds_pct = mode_data['adjodds']['fill']['per']
            odds_color = get_gradient_color(odds_pct)
            st.markdown(f"**Adj Odds:** {odds_pct:.1f}%")
            st.markdown(f'<div style="background:{odds_color};height:25px;border-radius:5px;"></div>', unsafe_allow_html=True)
    
    st.divider()
    
    # ====================
    # SECTION 2: P&L SUMMARY
    # ====================
    st.subheader("💰 Performance Summary (Last 30 Days)")
    
    pnl = calculate_pnl(races, days=30)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Net P&L", f"${pnl['net_profit']:.2f}", delta=f"{pnl['roi']:.1f}% ROI")
    with col2:
        st.metric("Total Races", pnl['total_races'])
    with col3:
        st.metric("Win Rate", f"{pnl['win_rate']:.1f}%", delta=f"{pnl['wins']} wins")
    with col4:
        st.metric("Podium Rate", f"{pnl['podium_rate']:.1f}%", delta=f"{pnl['podiums']} podiums")
    
    st.divider()
    
    # ====================
    # SECTION 3: PERFORMANCE ANALYSIS (TABBED)
    # ====================
    
    tab1, tab2, tab3 = st.tabs(["🏍️ Bike", "🏎️ Car", "🐎 Horse"])
    
    for tab, mode in zip([tab1, tab2, tab3], ['bike', 'car', 'horse']):
        with tab:
            st.subheader(f"📊 {mode.title()} Performance Analysis")
            
            # Filter races by mode
            mode_races = [r for r in races if r.get('rvmode') == mode and r.get('cb') and r.get('pos') and r.get('time')]
            
            if not mode_races:
                st.warning(f"No race data available for {mode.upper()} mode")
                continue
            
            # Calculate best distance
            distance_data = {}
            for race in mode_races:
                cb = int(race['cb'])  # Force to integer
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
                
                # Calculate weighted score
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
                if cb in GLOBAL_AVERAGES:
                    percentile_rank = ((avg_time - GLOBAL_AVERAGES[cb]) / GLOBAL_AVERAGES[cb] * 100)
                
                results.append({
                    'Distance': f"{cb * 100}m",
                    'CB': cb,
                    'Races': len(positions),
                    'Win Rate': f"{win_rate * 100:.1f}%",
                    'Avg Position': f"{avg_position:.2f}",
                    'Avg Time': f"{avg_time:.2f}s",
                    'Weighted Score': weighted_score,
                    'vs Global %': percentile_rank,
                })
            
            if not results:
                st.warning(f"Not enough race data for {mode.upper()} (need 20+ races per distance)")
                continue
            
            df = pd.DataFrame(results)
            df_sorted = df.sort_values('Weighted Score', ascending=False)
            
            # Best distance
            best = df_sorted.iloc[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("🥇 Best Distance", best['Distance'], 
                         delta=f"Score: {best['Weighted Score']:.1f}/100")
                st.markdown(f"""
                **Performance:**
                - 🏁 {best['Races']} races
                - 🏆 {best['Win Rate']} win rate
                - 📍 {best['Avg Position']} avg position
                """)
            
            with col2:
                if best['vs Global %'] is not None and pd.notna(best['vs Global %']):
                    is_faster = best['vs Global %'] < 0
                    st.metric("vs Global Average", 
                             f"{best['vs Global %']:+.2f}%",
                             delta="Faster" if is_faster else "Slower",
                             delta_color="normal" if is_faster else "inverse")
            
            # Full rankings
            st.markdown("**📋 All Distances:**")
            display_df = df_sorted.copy()
            display_df['Weighted Score'] = display_df['Weighted Score'].apply(lambda x: f"{x:.1f}")
            display_df['vs Global %'] = display_df['vs Global %'].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A")
            
            display_cols = ['Distance', 'Races', 'Win Rate', 'Avg Position', 'Avg Time', 'Weighted Score', 'vs Global %']
            st.dataframe(display_df[display_cols], use_container_width=True, hide_index=True, height=300)
            
            st.divider()
            
            # ====================
            # RACE HISTORY CHARTS (All distances)
            # ====================
            st.subheader("📈 Race History & Charts")
            
            # Sort distances
            sorted_chart_distances = sorted(distance_data.keys())
            
            if not sorted_chart_distances:
                st.info("No race data available")
                continue
            
            for dist_idx, distance in enumerate(sorted_chart_distances):
                positions = distance_data[distance]['positions']
                times = distance_data[distance]['times']
                
                # Calculate stats
                wins = sum(1 for p in positions if p == 1)
                win_pct = (wins / len(positions) * 100) if positions else 0
                
                # Get odds
                odds_races = [r for r in mode_races if r['cb'] == distance and r.get('odds')]
                avg_odds = sum(r['odds'] for r in odds_races) / len(odds_races) if odds_races else None
                
                # Title
                title = f"**{distance * 100}m** ({len(positions)} races)"
                if avg_odds:
                    title += f" • Avg Odds: {avg_odds:.2f}"
                st.markdown(f"### {title}")
                
                # Position Distribution
                position_counts = {i: 0 for i in range(1, 15)}
                for pos in positions:
                    if 1 <= pos <= 14:
                        position_counts[pos] += 1
                
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
                    height=250,
                    showlegend=False,
                    xaxis=dict(tickmode='linear', tick0=1, dtick=1)
                )
                
                st.plotly_chart(fig_pos, use_container_width=True, key=f"pos_{mode}_{dist_idx}")
                
                # Finish Times Distribution
                if times:
                    sorted_times = sorted(times)
                    fastest = sorted_times[0]
                    slowest = sorted_times[-1]
                    average = sum(times) / len(times)
                    global_avg = GLOBAL_AVERAGES.get(distance)
                    
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
                    
                    # Points - using circles with proper hover
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
                            marker=dict(
                                size=20,
                                color=color,
                                symbol='circle',
                                line=dict(width=2, color='white')
                            ),
                            name=label,
                            hovertext=f"{label}<br>{time:.2f}s",
                            hoverinfo='text'
                        ))
                    
                    fig_timing.update_layout(
                        title="Finish Times Distribution",
                        xaxis_title="Time (seconds)",
                        yaxis=dict(visible=False, range=[-0.2, 0.2]),
                        height=150,
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    
                    st.plotly_chart(fig_timing, use_container_width=True, key=f"timing_{mode}_{dist_idx}")
                
                st.divider()
    
    # ====================
    # SECTION 4: BREEDING & LINEAGE
    # ====================
    st.header("🧬 Breeding & Lineage")
    
    # Fetch splicing info
    with st.spinner("Loading breeding information..."):
        splicing_info = fetch_api("/cores/splicing_info", {"hid": mini['hid']})
    
    if splicing_info:
        splice_core = splicing_info.get('splice_core', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Core Information")
            
            core_type = splice_core.get('type', mini.get('type', 'Unknown'))
            st.metric("Type", core_type.title())
            
            # Parents
            parents = splicing_info.get('parents')
            if parents and any(parents):
                st.markdown("**Parents:**")
                for parent_id in parents:
                    if parent_id:
                        st.markdown(f"- Core #{parent_id}")
            else:
                st.info("🌟 Genesis Core (no parents)")
        
        with col2:
            st.subheader("🏆 Breeding Status")
            
            in_stud = splice_core.get('in_stud', False)
            
            if in_stud:
                st.success("✅ Available for Breeding")
                price_usd = splice_core.get('price_usd', 0)
                if price_usd > 0:
                    st.metric("Breeding Fee", f"${price_usd:.2f}")
                else:
                    st.info("Free breeding")
            else:
                st.warning("❌ Not Currently Available")
        
        # Breeding stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            life_splices = splice_core.get('life_splices_n', 0)
            st.metric("Total Offspring", life_splices)
        
        with col2:
            max_life = splice_core.get('mxlife_splices_n', 0)
            remaining = max_life - life_splices if max_life > 0 else "Unlimited"
            st.metric("Remaining Lifetime", remaining)
        
        with col3:
            cycle_splices = splice_core.get('cycle_splices_n', 0)
            st.metric("This Cycle", cycle_splices)
        
        with col4:
            max_cycle = splice_core.get('mxcycle_splices_n', 0)
            cycle_remaining = max_cycle - cycle_splices if max_cycle > 0 else 0
            st.metric("Cycle Remaining", cycle_remaining)
        
        # Offspring list
        life_splices_list = splice_core.get('life_splices', [])
        
        if life_splices_list:
            st.subheader(f"👶 Offspring ({len(life_splices_list)} cores)")
            
            # Fetch mini data and power data for all offspring
            with st.spinner("Loading offspring details..."):
                offspring_data = fetch_api("/cores/mini_bulk", {"hids": life_splices_list})
                offspring_power = fetch_api("/cores/power_bulk", {"hids": life_splices_list})
            
            if offspring_data and offspring_power:
                # Create power lookup
                power_lookup = {p['hid']: p for p in offspring_power}
                
                # Display in card grid - 4 per row
                cols_per_row = 4
                
                for i in range(0, len(offspring_data), cols_per_row):
                    cols = st.columns(cols_per_row)
                    row_offspring = offspring_data[i:i+cols_per_row]
                    
                    for col_idx, offspring in enumerate(row_offspring):
                        with cols[col_idx]:
                            # Get power data
                            power_data = power_lookup.get(offspring['hid'], {})
                            mode_power = power_data.get('power', {}).get('bike', {})
                            
                            power_pct = mode_power.get('power', {}).get('fill', {}).get('per', 0)
                            var_pct = mode_power.get('variance', {}).get('fill', {}).get('per', 0)
                            adj_pct = mode_power.get('adjodds', {}).get('fill', {}).get('per', 0)
                            
                            # Card with container border
                            with st.container(border=True):
                                # Name and ID
                                st.markdown(f"**{offspring.get('name', 'Unnamed')}**")
                                st.caption(f"#{offspring['hid']}")
                                
                                # Badges in columns
                                b1, b2, b3 = st.columns(3)
                                with b1:
                                    st.markdown(f'<span style="background:#667eea;color:white;padding:3px 6px;border-radius:4px;font-size:0.7em;display:inline-block;">{offspring.get("type", "?").upper()[:3]}</span>', unsafe_allow_html=True)
                                with b2:
                                    st.markdown(f'<span style="background:#764ba2;color:white;padding:3px 6px;border-radius:4px;font-size:0.7em;display:inline-block;">{offspring.get("element", "?").upper()[:3]}</span>', unsafe_allow_html=True)
                                with b3:
                                    st.markdown(f'<span style="background:#f59e0b;color:white;padding:3px 6px;border-radius:4px;font-size:0.7em;display:inline-block;">F{offspring.get("fno", "?")}</span>', unsafe_allow_html=True)
                                
                                st.write("")  # Spacer
                                
                                # Power stats with color-coded bars (Blue → Green → Red)
                                st.markdown("**Power Stats:**")
                                
                                def get_gradient_color(percentage):
                                    """Calculate color: blue (0%) → green (50%) → red (100%)"""
                                    if percentage <= 50:
                                        # Blue to Green (0-50%)
                                        ratio = percentage / 50
                                        r = 0
                                        g = int(255 * ratio)
                                        b = int(255 * (1 - ratio))
                                    else:
                                        # Green to Red (50-100%)
                                        ratio = (percentage - 50) / 50
                                        r = int(255 * ratio)
                                        g = int(255 * (1 - ratio))
                                        b = 0
                                    return f"#{r:02x}{g:02x}{b:02x}"
                                
                                # Power bar
                                st.caption("PWR")
                                power_color = get_gradient_color(power_pct)
                                st.markdown(f'<div style="background:{power_color};height:20px;border-radius:4px;text-align:center;line-height:20px;color:white;font-weight:bold;font-size:0.75em;">{power_pct:.1f}%</div>', unsafe_allow_html=True)
                                
                                # Variance bar
                                st.caption("VAR")
                                var_color = get_gradient_color(var_pct)
                                st.markdown(f'<div style="background:{var_color};height:20px;border-radius:4px;text-align:center;line-height:20px;color:white;font-weight:bold;font-size:0.75em;">{var_pct:.1f}%</div>', unsafe_allow_html=True)
                                
                                # Adj Odds bar
                                st.caption("ADJ")
                                adj_color = get_gradient_color(adj_pct)
                                st.markdown(f'<div style="background:{adj_color};height:20px;border-radius:4px;text-align:center;line-height:20px;color:white;font-weight:bold;font-size:0.75em;">{adj_pct:.1f}%</div>', unsafe_allow_html=True)
                                
                                st.write("")  # Spacer
                                
                                # Gender and color
                                st.caption(f"{offspring.get('gender', '?').title()} • {offspring.get('color', 'Unknown').replace('-', ' ').title()}")
                                
                                # Link button
                                core_url = f"https://fbike.dnaracing.run/core/{offspring['hid']}"
                                st.link_button("View on DNA Racing", core_url, use_container_width=True)
            else:
                # Fallback to simple button grid
                st.info("Could not load offspring details")
                cols_per_row = 10
                rows = [life_splices_list[i:i+cols_per_row] for i in range(0, len(life_splices_list), cols_per_row)]
                
                for row in rows:
                    cols = st.columns(cols_per_row)
                    for idx, offspring_id in enumerate(row):
                        with cols[idx]:
                            if st.button(f"#{offspring_id}", key=f"offspring_{offspring_id}"):
                                st.session_state.current_core_id = offspring_id
                                st.rerun()
    
    # Owner info at bottom
    st.divider()
    st.subheader("👤 Owner Information")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Vault Address", mini['vault'], disabled=True)
    with col2:
        st.text_input("Vault Name", mini.get('vault_name', 'Unknown'), disabled=True)

else:
    st.info("👆 Enter a Core ID above and click 'Search Core' to begin")
    
    with st.expander("💡 Example Cores"):
        st.markdown("""
        Try searching for these example cores:
        - **Core #192** - Well-rounded performer
        - **Core #10** - Linen (Genesis)
        - **Core #19503** - Iron
        """)
