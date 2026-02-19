import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from typing import Optional, List, Dict
from datetime import datetime, timedelta

st.set_page_config(page_title="Race Finder", page_icon="🏁", layout="wide")

st.title("🏁 Race Finder")
st.markdown("Find the best races for your cores with smart ROI analysis")

# Global averages and API config
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


def calculate_pnl(races: List[dict], days: int = 30) -> dict:
    """Calculate P&L from race history"""
    if not races:
        return {
            'total_races': 0, 'fees_paid': 0, 'prizes_won': 0,
            'net_profit': 0, 'roi': 0, 'wins': 0, 'win_rate': 0,
            'podiums': 0, 'podium_rate': 0
        }
    
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
        return {
            'total_races': 0, 'fees_paid': 0, 'prizes_won': 0,
            'net_profit': 0, 'roi': 0, 'wins': 0, 'win_rate': 0,
            'podiums': 0, 'podium_rate': 0
        }
    
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


def get_core_performance(races: List[dict], distance: int, mode: str) -> dict:
    """Get performance stats for a specific distance and mode"""
    relevant_races = [r for r in races if r.get('cb') == distance and r.get('rvmode') == mode]
    
    if not relevant_races:
        return {'races': 0, 'win_rate': 0, 'avg_position': 0, 'podium_rate': 0}
    
    wins = sum(1 for r in relevant_races if r.get('pos') == 1)
    podiums = sum(1 for r in relevant_races if r.get('pos', 99) <= 3)
    avg_pos = sum(r.get('pos', 14) for r in relevant_races) / len(relevant_races)
    
    return {
        'races': len(relevant_races),
        'win_rate': (wins / len(relevant_races) * 100) if relevant_races else 0,
        'avg_position': avg_pos,
        'podium_rate': (podiums / len(relevant_races) * 100) if relevant_races else 0
    }


def check_eligibility(core_stats: dict, mini: dict, entry_filter: dict) -> tuple:
    """Check if core meets entry requirements"""
    if not entry_filter:
        return True, ""
    
    reasons = []
    
    # Check element
    if entry_filter.get('element') and mini.get('element') not in entry_filter['element']:
        reasons.append(f"Element: {mini.get('element')} not allowed")
    
    # Check type
    if entry_filter.get('type') and mini.get('type') not in entry_filter['type']:
        reasons.append(f"Type: {mini.get('type')} not allowed")
    
    # Check gender
    if entry_filter.get('gender') and mini.get('gender') not in entry_filter['gender']:
        reasons.append(f"Gender: {mini.get('gender')} not allowed")
    
    # Check race count
    total_races = core_stats.get('career', {}).get('races_n', 0)
    if entry_filter.get('races_n_mi') and total_races < entry_filter['races_n_mi']:
        reasons.append(f"Too few races: {total_races} < {entry_filter['races_n_mi']}")
    if entry_filter.get('races_n_mx') and total_races > entry_filter['races_n_mx']:
        reasons.append(f"Too many races: {total_races} > {entry_filter['races_n_mx']}")
    
    # Check win rate
    win_rate = core_stats.get('career', {}).get('win_p', 0) * 100
    if entry_filter.get('win_p_mi') and win_rate < entry_filter['win_p_mi']:
        reasons.append(f"Win rate too low: {win_rate:.1f}% < {entry_filter['win_p_mi']}%")
    if entry_filter.get('win_p_mx') and win_rate > entry_filter['win_p_mx']:
        reasons.append(f"Win rate too high: {win_rate:.1f}% > {entry_filter['win_p_mx']}%")
    
    eligible = len(reasons) == 0
    reason_text = "; ".join(reasons) if reasons else ""
    
    return eligible, reason_text


def calculate_race_score(race: dict, core_perf: dict, core_best_distance: int, competition_strength: float = 50) -> float:
    """Calculate recommendation score for a race"""
    if core_perf['races'] == 0:
        return 0
    
    # Distance match (35%) - reduced to make room for competition
    distance = race.get('cb', 0)
    if distance == core_best_distance:
        distance_score = 100
    else:
        distance_score = 50
    
    # Competition strength (30%) - NEW: based on actual competitor analysis
    competition_score = competition_strength
    
    # Win rate (20%)
    win_rate_score = core_perf['win_rate']
    
    # ROI potential (15%) - prize/fee ratio
    prize = race.get('prizeusd', 0)
    fee = race.get('feeusd', 0)
    if fee == 0 and prize > 0:
        roi_score = 100
    elif fee > 0:
        ratio = prize / fee
        roi_score = min(ratio * 5, 100)  # Cap at 100
    else:
        roi_score = 0
    
    total_score = (
        distance_score * 0.35 +
        competition_score * 0.30 +
        win_rate_score * 0.20 +
        roi_score * 0.15
    )
    
    return total_score


def analyze_competition(race: dict, your_core_id: int, your_adjodds: float, mode: str) -> dict:
    """Analyze race competition using power stats"""
    competitor_hids = race.get('hids', [])
    
    if not competitor_hids or len(competitor_hids) == 0:
        return {
            'strength_score': 100,  # Empty race = great!
            'competitors': [],
            'your_rank': 1,
            'stronger_count': 0,
            'weaker_count': 0
        }
    
    # Fetch power stats for all competitors
    competitors_data = fetch_api("/cores/power_bulk", {"hids": competitor_hids})
    
    if not competitors_data:
        # Fallback if API fails
        return {
            'strength_score': 50,
            'competitors': [],
            'your_rank': None,
            'stronger_count': 0,
            'weaker_count': 0
        }
    
    # Extract adjodds for each competitor
    competitor_stats = []
    for comp in competitors_data:
        if comp['hid'] == your_core_id:
            continue  # Skip your own core
        
        mode_data = comp.get('power', {}).get(mode, {})
        if not mode_data:
            continue
        
        adjodds = mode_data.get('adjodds', {}).get('fill', {}).get('per', 0)
        power = mode_data.get('power', {}).get('fill', {}).get('per', 0)
        variance = mode_data.get('variance', {}).get('fill', {}).get('per', 0)
        
        competitor_stats.append({
            'hid': comp['hid'],
            'adjodds': adjodds,
            'power': power,
            'variance': variance
        })
    
    # Sort by adjodds (descending)
    competitor_stats.sort(key=lambda x: x['adjodds'], reverse=True)
    
    # Calculate your rank
    stronger_count = sum(1 for c in competitor_stats if c['adjodds'] > your_adjodds)
    weaker_count = len(competitor_stats) - stronger_count
    your_rank = stronger_count + 1
    
    # Calculate competition strength score
    if stronger_count == 0:
        strength_score = 100  # No one stronger!
    elif stronger_count == 1:
        strength_score = 85   # One stronger
    elif stronger_count == 2:
        strength_score = 70   # Two stronger
    elif stronger_count == 3:
        strength_score = 55   # Three stronger
    else:
        strength_score = 30   # Many stronger - tough field
    
    return {
        'strength_score': strength_score,
        'competitors': competitor_stats[:5],  # Top 5 only
        'your_rank': your_rank,
        'stronger_count': stronger_count,
        'weaker_count': weaker_count,
        'total_entries': len(competitor_stats) + 1  # +1 for your core
    }


# Initialize session state for core selection
if 'selected_cores' not in st.session_state:
    st.session_state.selected_cores = []

if 'core_data_cache' not in st.session_state:
    st.session_state.core_data_cache = {}

# Sidebar: Core Selection
st.sidebar.header("🎯 Core Selection")

# Add core input
new_core_id = st.sidebar.number_input(
    "Add Core by ID",
    min_value=1,
    step=1,
    key="new_core_input"
)

if st.sidebar.button("➕ Add Core", use_container_width=True):
    if new_core_id not in st.session_state.selected_cores:
        if len(st.session_state.selected_cores) < 10:
            st.session_state.selected_cores.append(new_core_id)
            st.sidebar.success(f"Added Core #{new_core_id}")
        else:
            st.sidebar.error("Maximum 10 cores allowed")
    else:
        st.sidebar.warning("Core already added")

# Display selected cores
if st.session_state.selected_cores:
    st.sidebar.subheader("Selected Cores:")
    for core_id in st.session_state.selected_cores:
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            st.write(f"Core #{core_id}")
        with col2:
            if st.button("❌", key=f"remove_{core_id}"):
                st.session_state.selected_cores.remove(core_id)
                if core_id in st.session_state.core_data_cache:
                    del st.session_state.core_data_cache[core_id]
                st.rerun()

st.sidebar.divider()

# Mode selection
mode = st.sidebar.selectbox(
    "Racing Mode",
    ["bike", "car", "horse"],
    key="race_mode"
)

# Filters
st.sidebar.subheader("🔍 Filters")
show_ineligible = st.sidebar.checkbox("Show ineligible races", value=False)
min_prize = st.sidebar.number_input("Min Prize ($)", min_value=0, value=0, step=10)
max_fee = st.sidebar.number_input("Max Entry Fee ($)", min_value=0, value=1000, step=10)

st.sidebar.divider()

# Search button
search_btn = st.sidebar.button("🔍 Find Races", type="primary", use_container_width=True)

# Main content
if not st.session_state.selected_cores:
    st.info("👈 Add cores in the sidebar to begin")
    
    with st.expander("💡 How to use Race Finder"):
        st.markdown("""
        **Step 1:** Add up to 10 cores using the sidebar
        
        **Step 2:** Select your racing mode (Bike/Car/Horse)
        
        **Step 3:** Click "Find Races" to see recommendations
        
        **Features:**
        - 🎯 Smart race recommendations based on your core's performance
        - 💰 ROI calculations and expected returns
        - ✅ Entry requirement validation
        - 📊 Performance tracking (P&L, win rates)
        - ⚡ Direct links to enter races
        """)
    
    st.stop()

# Fetch data when search is clicked
if search_btn or 'open_races' in st.session_state:
    
    # Fetch core data for all selected cores
    with st.spinner("Loading core data..."):
        for core_id in st.session_state.selected_cores:
            if core_id not in st.session_state.core_data_cache:
                mini = fetch_api("/cores/mini", {"hid": core_id})
                stats = fetch_api("/cores/racing_stats", {"hid": core_id})
                races = fetch_api("/i/hraces", {"hid": core_id, "limit": 10000})
                
                if mini and stats and races:
                    st.session_state.core_data_cache[core_id] = {
                        'mini': mini,
                        'stats': stats,
                        'races': races
                    }
    
    # Fetch open races
    if search_btn or 'open_races' not in st.session_state:
        with st.spinner("Fetching open races..."):
            open_races_data = fetch_api("/races/open_races", {"rvmode": [mode]})
            
            if open_races_data:
                st.session_state.open_races = open_races_data
                st.success(f"✓ Found {len(open_races_data)} open {mode} races")
            else:
                st.error("Failed to fetch open races")
                st.stop()
    
    open_races = st.session_state.open_races
    
    # Display P&L Summary for selected cores
    st.header("📊 Performance Overview (Last 30 Days)")
    
    cols = st.columns(len(st.session_state.selected_cores))
    
    for idx, core_id in enumerate(st.session_state.selected_cores):
        if core_id in st.session_state.core_data_cache:
            with cols[idx]:
                core_data = st.session_state.core_data_cache[core_id]
                mini = core_data['mini']
                races = core_data['races']
                
                pnl = calculate_pnl(races, days=30)
                
                st.markdown(f"### Core #{core_id}")
                st.caption(mini.get('name', 'Unnamed'))
                
                st.metric(
                    "Net P&L",
                    f"${pnl['net_profit']:.2f}",
                    delta=f"{pnl['roi']:.1f}% ROI"
                )
                
                st.metric("Win Rate", f"{pnl['win_rate']:.1f}%")
                st.caption(f"{pnl['total_races']} races")
    
    st.divider()
    
    # Recommendations
    st.header("🏆 Top Race Recommendations")
    
    # Calculate scores for all cores and races
    recommendations = []
    
    for core_id in st.session_state.selected_cores:
        if core_id not in st.session_state.core_data_cache:
            continue
        
        core_data = st.session_state.core_data_cache[core_id]
        mini = core_data['mini']
        stats = core_data['stats']
        races = core_data['races']
        
        # Get core's best distance
        mode_stats = stats.get(f'hstats_{mode}', {})
        best_distance = None
        best_win_rate = 0
        
        for cb in range(9, 24):
            cb_stats = mode_stats.get(str(cb), {})
            if cb_stats.get('races_n', 0) >= 20:
                win_p = cb_stats.get('win_p', 0)
                if win_p > best_win_rate:
                    best_win_rate = win_p
                    best_distance = cb
        
        # Score each race
        for race in open_races:
            distance = race.get('cb')
            
            # Get performance at this distance
            core_perf = get_core_performance(races, distance, mode)
            
            if core_perf['races'] < 5:  # Skip if too few races
                continue
            
            # Check eligibility
            entry_filter = race.get('r_form', {}).get('entry_filt', {})
            eligible, reason = check_eligibility(mode_stats, mini, entry_filter)
            
            # Apply filters
            if race.get('prizeusd', 0) < min_prize:
                continue
            if race.get('feeusd', 1000000) > max_fee:
                continue
            
            if not eligible and not show_ineligible:
                continue
            
            # Get your core's adjodds for competition analysis
            your_power = core_data['stats'].get(f'hstats_{mode}', {})
            # We need to get adjodds from power endpoint - let's fetch it
            your_core_power = fetch_api("/cores/power", {"hid": core_id})
            your_adjodds = 0
            if your_core_power:
                mode_data = your_core_power.get('power', {}).get(mode, {})
                your_adjodds = mode_data.get('adjodds', {}).get('fill', {}).get('per', 0)
            
            # Analyze competition
            comp_analysis = analyze_competition(race, core_id, your_adjodds, mode)
            
            # Calculate score with competition strength
            score = calculate_race_score(race, core_perf, best_distance, comp_analysis['strength_score'])
            
            # Calculate expected ROI
            prize = race.get('prizeusd', 0)
            fee = race.get('feeusd', 0)
            horses_in = race.get('hs_in', 0)
            
            # Avoid division by zero
            if horses_in > 0:
                expected_win = prize * (core_perf['win_rate'] / 100) * (1 / horses_in)
                expected_roi = expected_win - fee
            else:
                expected_roi = 0
            
            recommendations.append({
                'core_id': core_id,
                'core_name': mini.get('name', 'Unnamed'),
                'race': race,
                'score': score,
                'eligible': eligible,
                'ineligible_reason': reason,
                'core_perf': core_perf,
                'expected_roi': expected_roi,
                'is_best_distance': distance == best_distance,
                'competition': comp_analysis,
                'your_adjodds': your_adjodds
            })
    
    # Sort by score
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    
    # Show top 5 recommendations
    st.subheader("🥇 Top 5 Recommended Races")
    
    top_5 = [r for r in recommendations if r['eligible']][:5]
    
    if not top_5:
        st.warning("No eligible races found matching your criteria")
    else:
        for rec in top_5:
            race = rec['race']
            core_perf = rec['core_perf']
            
            # Recommendation badge
            if rec['score'] >= 80:
                badge = "🥇 HIGHLY RECOMMENDED"
                color = "green"
            elif rec['score'] >= 60:
                badge = "🥈 RECOMMENDED"
                color = "blue"
            else:
                badge = "🥉 CONSIDER"
                color = "orange"
            
            with st.container():
                st.markdown(f"### {badge}")
                
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.markdown(f"**{race.get('cb', 0) * 100}m** • {race.get('race_name', 'Unnamed')}")
                    st.caption(f"Core #{rec['core_id']} - {rec['core_name']}")
                    
                    filled = race.get('hs_in', 0)
                    total = race.get('rgate', 0)
                    st.progress(filled / total if total > 0 else 0, text=f"{filled}/{total} filled")
                
                with col2:
                    fee_display = "FREE" if race.get('feeusd', 0) == 0 else f"${race.get('feeusd', 0):.2f}"
                    st.metric("Entry Fee", fee_display)
                    st.metric("Prize Pool", f"${race.get('prizeusd', 0):.2f}")
                
                with col3:
                    st.metric("Your Win Rate", f"{core_perf['win_rate']:.1f}%")
                    st.metric("Expected ROI", f"${rec['expected_roi']:.2f}")
                
                # Why recommended
                reasons = []
                if rec['is_best_distance']:
                    reasons.append("✅ Your BEST distance")
                if rec['competition']['strength_score'] >= 85:
                    reasons.append("✅ Weak competition")
                elif rec['competition']['strength_score'] >= 70:
                    reasons.append("⚠️ Moderate competition")
                else:
                    reasons.append("🔴 Strong competition")
                if race.get('feeusd', 0) == 0:
                    reasons.append("✅ Free entry")
                if rec['expected_roi'] > 0:
                    reasons.append("✅ Positive ROI")
                
                if reasons:
                    st.info("**Why:** " + " • ".join(reasons))
                
                # Competition Analysis (Clean & Simple)
                comp = rec['competition']
                
                if comp['competitors']:
                    with st.expander(f"👥 Field Analysis ({comp['total_entries']} entries)", expanded=False):
                        
                        # Your position in field
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            rank_color = "🟢" if comp['your_rank'] <= 3 else "🟡" if comp['your_rank'] <= 6 else "🔴"
                            st.metric("Your Projected Rank", f"{rank_color} #{comp['your_rank']}")
                        
                        with col2:
                            st.metric("Cores Faster", comp['stronger_count'], 
                                     delta="Tough field" if comp['stronger_count'] > 2 else None,
                                     delta_color="inverse")
                        
                        with col3:
                            st.metric("Cores Slower", comp['weaker_count'],
                                     delta="Good position" if comp['weaker_count'] > comp['stronger_count'] else None,
                                     delta_color="normal")
                        
                        st.divider()
                        
                        # Top competitors comparison
                        st.markdown("**Top Competitors:**")
                        
                        # Create comparison dataframe
                        comp_data = []
                        
                        # Add competitors
                        for idx, competitor in enumerate(comp['competitors']):
                            if idx >= 3:  # Show top 3 competitors only
                                break
                            comp_data.append({
                                'Rank': f"#{idx + 1}",
                                'Core': f"#{competitor['hid']}",
                                'Power': f"{competitor['power']:.1f}%",
                                'Variance': f"{competitor['variance']:.1f}%",
                                'Adj Odds': f"{competitor['adjodds']:.1f}%"
                            })
                        
                        # Get your core's full power stats
                        your_core_power = st.session_state.core_data_cache[rec['core_id']].get('power_full')
                        if not your_core_power:
                            # Fetch if not cached
                            your_core_power = fetch_api("/cores/power", {"hid": rec['core_id']})
                            st.session_state.core_data_cache[rec['core_id']]['power_full'] = your_core_power
                        
                        your_power_pct = "-"
                        your_variance_pct = "-"
                        if your_core_power:
                            mode_data = your_core_power.get('power', {}).get(mode, {})
                            your_power_pct = f"{mode_data.get('power', {}).get('fill', {}).get('per', 0):.1f}%"
                            your_variance_pct = f"{mode_data.get('variance', {}).get('fill', {}).get('per', 0):.1f}%"
                        
                        # Add your core in the right position
                        comp_data.append({
                            'Rank': f"#{comp['your_rank']} ⭐",
                            'Core': f"#{rec['core_id']} (YOU)",
                            'Power': your_power_pct,
                            'Variance': your_variance_pct,
                            'Adj Odds': f"{rec['your_adjodds']:.1f}%"
                        })
                        
                        # Show as clean table
                        df_comp = pd.DataFrame(comp_data)
                        st.dataframe(df_comp, hide_index=True, use_container_width=True)
                        
                        # Strategic insight
                        if comp['your_rank'] == 1:
                            st.success("💪 **You're the favorite!** Highest chance to win.")
                        elif comp['your_rank'] <= 3:
                            st.info("🎯 **Strong position.** Podium finish very likely.")
                        elif comp['your_rank'] <= 6:
                            st.warning("⚠️ **Mid-pack.** Possible podium with good performance.")
                        else:
                            st.error("🔴 **Tough field.** Consider finding a weaker race.")
                
                race_url = f"https://dnaracing.run/race/{race.get('rid')}"
                st.link_button("⚡ Enter This Race", race_url, use_container_width=True)
                
                st.divider()
    
    # All races table
    st.header("📋 All Available Races")
    
    if recommendations:
        # Convert to dataframe
        table_data = []
        for rec in recommendations:
            race = rec['race']
            core_perf = rec['core_perf']
            
            table_data.append({
                'Core': f"#{rec['core_id']}",
                'Distance': f"{race.get('cb', 0) * 100}m",
                'Race': race.get('race_name', 'Unnamed'),
                'Fee': f"${race.get('feeusd', 0):.2f}" if race.get('feeusd', 0) > 0 else "FREE",
                'Prize': f"${race.get('prizeusd', 0):.2f}",
                'Filled': f"{race.get('hs_in', 0)}/{race.get('rgate', 0)}",
                'Win Rate': f"{core_perf['win_rate']:.1f}%",
                'Expected ROI': f"${rec['expected_roi']:.2f}",
                'Score': f"{rec['score']:.0f}",
                'Eligible': "✅" if rec['eligible'] else "❌",
                'RID': race.get('rid')
            })
        
        df = pd.DataFrame(table_data)
        
        # Display with selection
        st.dataframe(
            df.drop('RID', axis=1),
            use_container_width=True,
            hide_index=True,
            height=600
        )

else:
    st.info("Click 'Find Races' in the sidebar to begin")
