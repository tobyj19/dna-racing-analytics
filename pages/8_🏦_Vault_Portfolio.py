import streamlit as st
import requests
import pandas as pd
from typing import Optional, List, Dict
from datetime import datetime, timedelta

st.set_page_config(page_title="Vault Portfolio", page_icon="🏦", layout="wide")

st.title("🏦 Vault Portfolio Analyzer")
st.markdown("Analyze any vault's complete core collection and performance")

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


def calculate_vault_pnl(all_races: List[dict], days: int = 30) -> dict:
    """Calculate combined P&L for all vault cores"""
    cutoff = datetime.now() - timedelta(days=days)
    recent_races = []
    
    for race in all_races:
        try:
            race_date = datetime.fromisoformat(race.get('start_time', '').replace('Z', '+00:00'))
            if race_date > cutoff:
                recent_races.append(race)
        except:
            continue
    
    if not recent_races:
        return {
            'total_races': 0, 'fees_paid': 0, 'prizes_won': 0,
            'net_profit': 0, 'roi': 0, 'wins': 0, 'podiums': 0
        }
    
    total_fees = sum(r.get('fee', 0) for r in recent_races)
    total_prizes = sum(r.get('prize_usd', 0) for r in recent_races)
    wins = sum(1 for r in recent_races if r.get('pos') == 1)
    podiums = sum(1 for r in recent_races if r.get('pos', 99) <= 3)
    
    return {
        'total_races': len(recent_races),
        'fees_paid': total_fees,
        'prizes_won': total_prizes,
        'net_profit': total_prizes - total_fees,
        'roi': ((total_prizes - total_fees) / total_fees * 100) if total_fees > 0 else 0,
        'wins': wins,
        'win_rate': (wins / len(recent_races) * 100) if recent_races else 0,
        'podiums': podiums,
        'podium_rate': (podiums / len(recent_races) * 100) if recent_races else 0
    }


# Sidebar: Vault Input
st.sidebar.header("🔍 Search Vault")

search_type = st.sidebar.radio(
    "Search by:",
    ["Vault Address", "Vault Name"],
    key="search_type"
)

if search_type == "Vault Address":
    vault_input = st.sidebar.text_input(
        "Enter Vault Address",
        placeholder="0xaf1320faa9a484a4702ec16ffec18260cc42c3c2",
        help="Full wallet address"
    )
else:
    vault_input = st.sidebar.text_input(
        "Enter Vault Name",
        placeholder="wisdom-weaver",
        help="Vault display name"
    )

analyze_btn = st.sidebar.button("🔍 Analyze Vault", type="primary", use_container_width=True)

st.sidebar.divider()

# Quick links
st.sidebar.subheader("💡 Quick Actions")
if st.sidebar.button("📊 View Sample Vault", use_container_width=True):
    st.session_state.sample_vault = True

# Main content
if analyze_btn or st.session_state.get('sample_vault'):
    
    if st.session_state.get('sample_vault'):
        vault_input = "wisdom-weaver"  # Sample vault
        st.session_state.sample_vault = False
    
    if not vault_input:
        st.error("Please enter a vault address or name")
        st.stop()
    
    # Determine if input is address or name
    if vault_input.startswith("0x"):
        vault_address = vault_input.lower()
        vault_name = None
    else:
        vault_name = vault_input
        vault_address = vault_input  # API will handle name lookup
    
    st.header(f"🏦 Analyzing: {vault_name or vault_address}")
    
    # Fetch vault cores
    with st.spinner("Fetching vault cores..."):
        cores = fetch_api("/vault/bikes_inf", {"vault": vault_address})
    
    if not cores or len(cores) == 0:
        st.error("❌ No cores found for this vault. Please check the address/name.")
        st.stop()
    
    # Separate trainers and regular cores
    trainer_cores = [c for c in cores if c.get('is_trainer', False)]
    regular_cores = [c for c in cores if not c.get('is_trainer', False)]
    
    st.success(f"✓ Found {len(cores)} total cores ({len(trainer_cores)} trainers, {len(regular_cores)} regular)")
    
    # Store in session state
    if 'vault_analysis' not in st.session_state:
        st.session_state.vault_analysis = {}
    
    st.session_state.vault_analysis['cores'] = cores
    st.session_state.vault_analysis['vault_address'] = vault_address
    st.session_state.vault_analysis['vault_name'] = vault_name
    
    st.divider()
    
    # Quick Overview
    st.subheader("📊 Quick Overview")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Cores", len(cores))
    
    with col2:
        st.metric("Regular Cores", len(regular_cores))
    
    with col3:
        st.metric("Trainer Cores", len(trainer_cores))
    
    # Element distribution
    elements = {}
    for core in regular_cores:
        elem = core.get('element', 'unknown')
        elements[elem] = elements.get(elem, 0) + 1
    
    with col4:
        most_common_element = max(elements, key=elements.get) if elements else "N/A"
        st.metric("Most Common Element", most_common_element.title())
    
    # Type distribution
    types = {}
    for core in regular_cores:
        core_type = core.get('type', 'unknown')
        types[core_type] = types.get(core_type, 0) + 1
    
    with col5:
        genesis_count = types.get('genesis', 0)
        st.metric("Genesis Cores", genesis_count)
    
    st.divider()
    
    # Detailed Analysis Toggle
    analyze_performance = st.checkbox("📈 Load Full Performance Analysis (may take 30-60 seconds)", value=False)
    
    if analyze_performance:
        
        with st.spinner("Fetching detailed performance data for all cores..."):
            # Fetch data for all regular cores (skip trainers for performance)
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            all_races = []
            all_power = []
            all_stats = []
            
            total = len(regular_cores)
            
            for idx, core in enumerate(regular_cores):
                hid = core['hid']
                
                status_text.text(f"Loading Core #{hid} ({idx+1}/{total})...")
                
                # Fetch race history
                races = fetch_api("/i/hraces", {"hid": hid, "limit": 1000})
                if races:
                    all_races.extend(races)
                
                # Fetch power stats
                power = fetch_api("/cores/power", {"hid": hid})
                if power:
                    all_power.append({'hid': hid, 'power': power})
                
                # Fetch racing stats
                stats = fetch_api("/cores/racing_stats", {"hid": hid})
                if stats:
                    all_stats.append({'hid': hid, 'stats': stats})
                
                progress_bar.progress((idx + 1) / total)
            
            progress_bar.empty()
            status_text.empty()
            
            st.success("✓ Performance data loaded!")
        
        st.divider()
        
        # P&L Analysis
        st.subheader("💰 Performance Summary (Last 30 Days)")
        
        pnl = calculate_vault_pnl(all_races, days=30)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Net P&L",
                f"${pnl['net_profit']:.2f}",
                delta=f"{pnl['roi']:.1f}% ROI"
            )
        
        with col2:
            st.metric("Total Races", pnl['total_races'])
        
        with col3:
            st.metric("Win Rate", f"{pnl['win_rate']:.1f}%", 
                     delta=f"{pnl['wins']} wins")
        
        with col4:
            st.metric("Podium Rate", f"{pnl['podium_rate']:.1f}%",
                     delta=f"{pnl['podiums']} podiums")
        
        # Financial breakdown
        with st.expander("💵 Financial Breakdown"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Entry Fees Paid", f"${pnl['fees_paid']:.2f}")
            with col2:
                st.metric("Prize Money Won", f"${pnl['prizes_won']:.2f}")
        
        st.divider()
        
        # Power Analysis
        st.subheader("⚡ Power Distribution")
        
        # Extract power stats by mode
        power_by_mode = {'bike': [], 'car': [], 'horse': []}
        
        for entry in all_power:
            power_data = entry['power'].get('power', {})
            for mode in ['bike', 'car', 'horse']:
                mode_data = power_data.get(mode, {})
                if mode_data:
                    power_pct = mode_data.get('power', {}).get('fill', {}).get('per', 0)
                    variance_pct = mode_data.get('variance', {}).get('fill', {}).get('per', 0)
                    adjodds_pct = mode_data.get('adjodds', {}).get('fill', {}).get('per', 0)
                    
                    power_by_mode[mode].append({
                        'hid': entry['hid'],
                        'power': power_pct,
                        'variance': variance_pct,
                        'adjodds': adjodds_pct
                    })
        
        # Show averages
        tab1, tab2, tab3 = st.tabs(["🏍️ Bike", "🏎️ Car", "🐎 Horse"])
        
        for tab, mode in zip([tab1, tab2, tab3], ['bike', 'car', 'horse']):
            with tab:
                mode_power = power_by_mode[mode]
                
                if mode_power:
                    avg_power = sum(c['power'] for c in mode_power) / len(mode_power)
                    avg_variance = sum(c['variance'] for c in mode_power) / len(mode_power)
                    avg_adjodds = sum(c['adjodds'] for c in mode_power) / len(mode_power)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Avg Power", f"{avg_power:.1f}%")
                    with col2:
                        st.metric("Avg Variance", f"{avg_variance:.1f}%")
                    with col3:
                        st.metric("Avg Adj Odds", f"{avg_adjodds:.1f}%")
                    
                    # Top 5 performers
                    st.markdown("**🏆 Top 5 by Power:**")
                    top_5 = sorted(mode_power, key=lambda x: x['power'], reverse=True)[:5]
                    
                    for idx, core in enumerate(top_5, 1):
                        st.write(f"{idx}. Core #{core['hid']} - {core['power']:.1f}% power, {core['adjodds']:.1f}% adj odds")
                else:
                    st.info(f"No {mode} power data available")
        
        st.divider()
        
        # Top Performers
        st.subheader("🏆 Top Performing Cores")
        
        # Calculate win rates per core
        core_performance = {}
        for race in all_races:
            hid = race.get('hid')
            if hid not in core_performance:
                core_performance[hid] = {'races': 0, 'wins': 0, 'podiums': 0}
            
            core_performance[hid]['races'] += 1
            if race.get('pos') == 1:
                core_performance[hid]['wins'] += 1
            if race.get('pos', 99) <= 3:
                core_performance[hid]['podiums'] += 1
        
        # Calculate rates
        for hid in core_performance:
            races = core_performance[hid]['races']
            if races > 0:
                core_performance[hid]['win_rate'] = (core_performance[hid]['wins'] / races) * 100
                core_performance[hid]['podium_rate'] = (core_performance[hid]['podiums'] / races) * 100
        
        # Filter cores with at least 10 races
        active_performers = {k: v for k, v in core_performance.items() if v['races'] >= 10}
        
        if active_performers:
            # Sort by win rate
            sorted_performers = sorted(active_performers.items(), key=lambda x: x[1]['win_rate'], reverse=True)
            
            st.markdown("**Top 10 by Win Rate (min 10 races):**")
            
            for idx, (hid, perf) in enumerate(sorted_performers[:10], 1):
                core_info = next((c for c in regular_cores if c['hid'] == hid), None)
                core_name = core_info['name'] if core_info else f"Core #{hid}"
                
                col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
                
                with col1:
                    st.write(f"**{idx}. {core_name}**")
                with col2:
                    st.write(f"Win Rate: {perf['win_rate']:.1f}%")
                with col3:
                    st.write(f"Races: {perf['races']}")
                with col4:
                    st.write(f"Wins: {perf['wins']}")
        
        st.divider()
        
        # Bottom Performers / Idle Cores
        st.subheader("⚠️ Underperforming & Idle Cores")
        
        # Find cores with 0 races
        raced_hids = set(race['hid'] for race in all_races)
        idle_cores = [c for c in regular_cores if c['hid'] not in raced_hids]
        
        if idle_cores:
            st.warning(f"**{len(idle_cores)} cores have never raced:**")
            idle_hids = ", ".join([f"#{c['hid']}" for c in idle_cores[:10]])
            st.write(idle_hids)
            if len(idle_cores) > 10:
                st.caption(f"... and {len(idle_cores) - 10} more")
        
        # Low performers (< 10% win rate with 20+ races)
        low_performers = {k: v for k, v in core_performance.items() 
                         if v['races'] >= 20 and v['win_rate'] < 10}
        
        if low_performers:
            st.warning(f"**{len(low_performers)} cores with <10% win rate (20+ races):**")
            for hid, perf in list(low_performers.items())[:5]:
                st.write(f"Core #{hid}: {perf['win_rate']:.1f}% win rate ({perf['races']} races)")
    
    else:
        st.info("👆 Check the box above to load full performance analysis")
    
    st.divider()
    
    # Core List
    st.subheader("📋 All Cores in Vault")
    
    # Create dataframe
    core_list = []
    for core in regular_cores:
        core_list.append({
            'HID': core['hid'],
            'Name': core.get('name', 'Unknown'),
            'Type': core.get('type', 'Unknown').title(),
            'Element': core.get('element', 'Unknown').title(),
            'Gender': core.get('gender', 'Unknown').title(),
            'F.No': core.get('fno', 'N/A')
        })
    
    df = pd.DataFrame(core_list)
    
    st.dataframe(df, use_container_width=True, hide_index=True, height=400)
    
    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Core List (CSV)",
        data=csv,
        file_name=f"vault_{vault_name or vault_address}_cores.csv",
        mime="text/csv"
    )

else:
    # Landing page
    st.info("👈 Enter a vault address or name in the sidebar to begin analysis")
    
    with st.expander("💡 How to use Vault Portfolio Analyzer"):
        st.markdown("""
        **What you can do:**
        
        1. **Search ANY vault** - Enter address (0x...) or vault name
        2. **View core collection** - See all cores owned by the vault
        3. **Performance analysis** - Combined P&L, win rates, power stats
        4. **Top performers** - Identify your best cores
        5. **Find issues** - Spot idle cores and underperformers
        
        **Example vault names to try:**
        - `wisdom-weaver`
        - `ATQ Motorsports`
        - Or enter your own vault address
        
        **Note:** Full performance analysis loads data for ALL cores and may take 30-60 seconds for vaults with many cores.
        """)
