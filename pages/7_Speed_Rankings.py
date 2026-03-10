import streamlit as st
import requests
import pandas as pd
from typing import Optional, Dict, List
from collections import defaultdict

st.set_page_config(page_title="Speed Rankings", page_icon="🧬", layout="wide")

API_BASE_URL = "https://api.dnaracing.run/fbike"

# Global average times per distance (in seconds)
GLOBAL_AVERAGES = {
    9: 50.3, 10: 56.9, 11: 63.8, 12: 70.5, 13: 76.8, 14: 82.8,
    15: 88.8, 16: 94.6, 17: 100.9, 18: 106.8, 19: 112.7, 20: 118.9,
    21: 124.4, 22: 130.7, 23: 137.6
}

def fetch_api(endpoint: str, data: dict, timeout: int = 60) -> Optional[dict]:
    """Fetch data from DNA Racing API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=timeout
        )
        response.raise_for_status()
        result = response.json()
        if result.get("status") == "success":
            return result.get("result")
        return None
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None


st.title("Speed Rankings")
st.markdown("Find the fastest cores at each distance compared to global averages")

# Input section
st.subheader("Analyze Cores")

input_method = st.radio(
    "How would you like to input cores?",
    ["Enter Core IDs Manually", "Load from Vault"],
    horizontal=True
)

cores_to_analyze = []

if input_method == "Enter Core IDs Manually":
    core_ids_input = st.text_area(
        "Enter Core IDs (comma-separated or one per line)",
        placeholder="588, 599, 192\nor\n588\n599\n192",
        height=100
    )
    
    if st.button("🔍 Analyze Cores", type="primary"):
        if core_ids_input:
            # Parse input
            ids_str = core_ids_input.replace('\n', ',').replace(' ', '')
            hids = [int(x.strip()) for x in ids_str.split(',') if x.strip().isdigit()]
            
            if hids:
                with st.spinner(f"Loading data for {len(hids)} cores..."):
                    cores_to_analyze = hids
                    st.session_state.cores_to_analyze = hids
            else:
                st.error("No valid core IDs found")

else:  # Load from Vault
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_type = st.radio(
            "Search by:",
            ["Vault Address", "Vault Name"],
            horizontal=True
        )
        
        if search_type == "Vault Address":
            vault_input = st.text_input(
                "Enter Vault Address",
                placeholder="0xaf1320faa9a484a4702ec16ffec18260cc42c3c2"
            )
        else:
            vault_input = st.text_input(
                "Enter Vault Name",
                placeholder="wisdom-weaver"
            )
    
    with col2:
        st.write("")
        st.write("")
        if st.button("🔍 Load Vault", type="primary"):
            if vault_input:
                vault_address = vault_input.lower() if vault_input.startswith("0x") else vault_input
                
                with st.spinner("Loading vault..."):
                    vault_cores = fetch_api("/vault/bikes_inf", {"vault": vault_address})
                
                if vault_cores:
                    regular_cores = [c for c in vault_cores if not c.get('is_trainer', False)]
                    cores_to_analyze = [c['hid'] for c in regular_cores]
                    st.session_state.cores_to_analyze = cores_to_analyze
                    st.success(f"✓ Loaded {len(cores_to_analyze)} cores from vault")
                else:
                    st.error("Failed to load vault")

st.divider()

# Analysis section
if 'cores_to_analyze' in st.session_state and st.session_state.cores_to_analyze:
    hids = st.session_state.cores_to_analyze
    
    st.info(f"📊 Analyzing {len(hids)} cores for speed rankings...")
    
    # Mode selector
    mode = st.selectbox("Select Mode", ["bike", "car", "horse"], index=0)
    
    # Minimum races filter
    min_races = st.slider("Minimum Races Required", 5, 50, 20, 5)
    
    if st.button("⚡ Calculate Speed Rankings", type="primary"):
        
        with st.spinner("Fetching race history for all cores..."):
            # Fetch race history in batches
            batch_size = 25
            all_race_data = {}
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i in range(0, len(hids), batch_size):
                batch = hids[i:i+batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(hids) + batch_size - 1) // batch_size
                
                status_text.text(f"Loading race history: Batch {batch_num}/{total_batches} ({len(batch)} cores)...")
                
                for hid in batch:
                    try:
                        race_history = fetch_api("/i/hraces", {"hid": hid, "rvmode": mode, "limit": 500}, timeout=120)
                        if race_history:
                            all_race_data[hid] = race_history
                    except:
                        pass
                
                progress = min((i + batch_size) / len(hids), 1.0)
                progress_bar.progress(progress)
            
            progress_bar.empty()
            status_text.empty()
        
        st.success(f"✓ Loaded race history for {len(all_race_data)}/{len(hids)} cores")
        
        # Calculate average times per distance for each core
        with st.spinner("Calculating speed rankings..."):
            # Structure: {distance: [(hid, avg_time, races_count, % faster), ...]}
            rankings_by_distance = defaultdict(list)
            
            for hid, races in all_race_data.items():
                # Group races by distance (class field)
                distance_times = defaultdict(list)
                
                for race in races:
                    distance_class = race.get('class')
                    finish_time = race.get('time')
                    
                    if distance_class and finish_time:
                        # Convert class to CB (1000 -> 10, 1100 -> 11, etc.)
                        cb = distance_class // 100
                        if cb in GLOBAL_AVERAGES:
                            distance_times[cb].append(finish_time)
                
                # Calculate averages for each distance
                for cb, times in distance_times.items():
                    if len(times) >= min_races:
                        avg_time = sum(times) / len(times)
                        global_avg = GLOBAL_AVERAGES[cb]
                        
                        # Calculate % faster than global average
                        # Negative % = slower, Positive % = faster
                        pct_faster = ((global_avg - avg_time) / global_avg) * 100
                        
                        rankings_by_distance[cb].append({
                            'hid': hid,
                            'avg_time': avg_time,
                            'races': len(times),
                            'pct_faster': pct_faster,
                            'global_avg': global_avg
                        })
            
            # Sort each distance by % faster (descending) and take top 30
            for cb in rankings_by_distance:
                rankings_by_distance[cb] = sorted(
                    rankings_by_distance[cb], 
                    key=lambda x: x['pct_faster'], 
                    reverse=True
                )[:30]
        
        st.success("✓ Speed rankings calculated!")
        
        st.divider()
        
        # Display results
        st.header("Speed Rankings by Distance")
        
        # Create tabs for each distance
        distance_tabs = st.tabs([f"{cb*100}m" for cb in sorted(rankings_by_distance.keys())])
        
        for tab_idx, cb in enumerate(sorted(rankings_by_distance.keys())):
            with distance_tabs[tab_idx]:
                rankings = rankings_by_distance[cb]
                
                if not rankings:
                    st.warning(f"No cores found with {min_races}+ races at {cb*100}m")
                    continue
                
                st.markdown(f"**Top {len(rankings)} Fastest Cores at {cb*100}m**")
                st.caption(f"Global Average: {GLOBAL_AVERAGES[cb]:.2f}s | Minimum {min_races} races required")
                
                # Build table
                table_data = []
                for idx, core_data in enumerate(rankings, 1):
                    # Determine medal emoji
                    if idx == 1:
                        medal = "🥇"
                    elif idx == 2:
                        medal = "🥈"
                    elif idx == 3:
                        medal = "🥉"
                    else:
                        medal = f"#{idx}"
                    
                    # Calculate time difference
                    time_diff = core_data['global_avg'] - core_data['avg_time']
                    
                    table_data.append({
                        'Rank': medal,
                        'Core ID': core_data['hid'],
                        'Avg Time': f"{core_data['avg_time']:.2f}s",
                        'Global Avg': f"{core_data['global_avg']:.2f}s",
                        'Difference': f"{time_diff:+.2f}s",
                        '% Faster': f"{core_data['pct_faster']:.2f}%",
                        'Races': core_data['races']
                    })
                
                df = pd.DataFrame(table_data)
                
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Rank": st.column_config.TextColumn("Rank", width="small"),
                        "Core ID": st.column_config.NumberColumn("Core ID", format="%d"),
                        "Avg Time": st.column_config.TextColumn("Avg Time"),
                        "Global Avg": st.column_config.TextColumn("Global Avg"),
                        "Difference": st.column_config.TextColumn("Diff", help="Negative = slower, Positive = faster"),
                        "% Faster": st.column_config.TextColumn("% Faster", help="Percentage faster than global average"),
                        "Races": st.column_config.NumberColumn("Races", format="%d")
                    }
                )
                
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    f"📥 Download {cb*100}m Rankings",
                    csv,
                    f"speed_rankings_{cb*100}m_{mode}.csv",
                    "text/csv",
                    key=f"download_{cb}"
                )
                
                # Show top 3 with highlights
                if len(rankings) >= 3:
                    st.markdown("**🏆 Podium:**")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "🥇 1st Place",
                            f"Core #{rankings[0]['hid']}",
                            f"{rankings[0]['avg_time']:.2f}s ({rankings[0]['pct_faster']:+.2f}%)"
                        )
                    
                    with col2:
                        st.metric(
                            "🥈 2nd Place",
                            f"Core #{rankings[1]['hid']}",
                            f"{rankings[1]['avg_time']:.2f}s ({rankings[1]['pct_faster']:+.2f}%)"
                        )
                    
                    with col3:
                        st.metric(
                            "🥉 3rd Place",
                            f"Core #{rankings[2]['hid']}",
                            f"{rankings[2]['avg_time']:.2f}s ({rankings[2]['pct_faster']:+.2f}%)"
                        )

else:
    st.info("👆 Enter core IDs or load a vault to analyze speed rankings")
    
    with st.expander("💡 How It Works"):
        st.markdown("""
        **Speed Rankings** compares each core's average finish time against global averages.
        
        **What It Shows:**
        - Top 30 fastest cores at each distance (900m - 2300m)
        - Average finish time per core
        - % faster/slower than global average
        - Minimum races requirement (default: 20)
        
        **How to Use:**
        1. Enter specific core IDs or load entire vault
        2. Select mode (bike/car/horse)
        3. Set minimum races required
        4. Click "Calculate Speed Rankings"
        5. View rankings for each distance
        
        **Understanding Results:**
        - **Positive %** = Faster than global average ✅
        - **Negative %** = Slower than global average ❌
        - **Green numbers** = Better than average
        - **Red numbers** = Worse than average
        
        **Use Cases:**
        - Find fastest cores in your vault
        - Compare core performance across distances
        - Identify speed specialists
        - Benchmark against global averages
        """)
