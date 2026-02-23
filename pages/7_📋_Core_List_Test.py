import streamlit as st
import requests
from typing import Optional

st.set_page_config(page_title="Core List Test", page_icon="📋", layout="wide")

st.title("📋 Active Cores List - Test Page")
st.markdown("Fetches all cores from open races and shows their power stats")

API_BASE_URL = "https://api.dnaracing.run/fbike"

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

# Mode selection
mode = st.selectbox("Select Mode", ["bike", "car", "horse"])

if st.button("🔍 Fetch Active Cores", type="primary"):
    
    with st.spinner("Fetching open races..."):
        open_races = fetch_api("/races/open_races", {"rvmode": [mode]})
    
    if not open_races:
        st.error("Failed to fetch open races")
        st.stop()
    
    st.success(f"✓ Found {len(open_races)} open races")
    
    # Extract all unique core IDs
    all_core_ids = set()
    for race in open_races:
        all_core_ids.update(race.get('hids', []))
    
    all_core_ids = sorted(list(all_core_ids))
    
    st.info(f"📊 Found {len(all_core_ids)} unique cores in open races")
    
    # Fetch power data for all cores
    with st.spinner(f"Fetching power data for {len(all_core_ids)} cores..."):
        power_data = fetch_api("/cores/power_bulk", {"hids": all_core_ids})
        mini_data = fetch_api("/cores/mini_bulk", {"hids": all_core_ids})
    
    if not power_data:
        st.error("Failed to fetch power data")
        st.stop()
    
    st.success("✓ Power data loaded")
    
    # Create lookup for mini data
    mini_lookup = {}
    if mini_data:
        for mini in mini_data:
            mini_lookup[mini['hid']] = mini
    
    # Extract power stats
    core_list = []
    for core in power_data:
        hid = core['hid']
        mode_data = core.get('power', {}).get(mode, {})
        
        if not mode_data:
            continue
        
        power_pct = mode_data.get('power', {}).get('fill', {}).get('per', 0)
        variance_pct = mode_data.get('variance', {}).get('fill', {}).get('per', 0)
        adjodds_pct = mode_data.get('adjodds', {}).get('fill', {}).get('per', 0)
        
        mini = mini_lookup.get(hid, {})
        name = mini.get('name', 'Unknown')
        element = mini.get('element', 'Unknown')
        core_type = mini.get('type', 'Unknown')
        
        core_list.append({
            'HID': hid,
            'Name': name,
            'Power': power_pct,
            'Variance': variance_pct,
            'Adj Odds': adjodds_pct,
            'Element': element,
            'Type': core_type
        })
    
    # Sort by power (highest first)
    core_list.sort(key=lambda x: x['Power'], reverse=True)
    
    st.divider()
    
    # Display top 30
    st.subheader(f"🔥 Top 30 Highest Power {mode.upper()} Cores")
    
    for idx, core in enumerate(core_list[:30], 1):
        medal = ""
        if idx == 1:
            medal = "🥇"
        elif idx == 2:
            medal = "🥈"
        elif idx == 3:
            medal = "🥉"
        
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2])
            
            with col1:
                st.markdown(f"**{medal} #{idx}**")
            
            with col2:
                st.markdown(f"**Core #{core['HID']}** - {core['Name']}")
            
            with col3:
                st.metric("Power", f"{core['Power']:.1f}%")
            
            with col4:
                st.metric("Variance", f"{core['Variance']:.1f}%")
            
            with col5:
                st.metric("Adj Odds", f"{core['Adj Odds']:.1f}%")
            
            st.caption(f"Element: {core['Element']} • Type: {core['Type']}")
            
            if idx < 30:
                st.divider()
    
    st.divider()
    
    # Full list as downloadable text
    st.subheader(f"📋 Complete List ({len(core_list)} cores)")
    
    # Create text output
    text_output = f"# {mode.upper()} CORES - Power Rankings\n"
    text_output += f"# Total: {len(core_list)} cores\n"
    text_output += f"# Sorted by Power (highest first)\n\n"
    text_output += f"{'Rank':<6} {'HID':<8} {'Name':<30} {'Power':<8} {'Variance':<10} {'Adj Odds':<10} {'Element':<10} {'Type':<10}\n"
    text_output += "=" * 120 + "\n"
    
    for idx, core in enumerate(core_list, 1):
        text_output += f"{idx:<6} #{core['HID']:<7} {core['Name'][:28]:<30} {core['Power']:.1f}%{'':<4} {core['Variance']:.1f}%{'':<6} {core['Adj Odds']:.1f}%{'':<6} {core['Element']:<10} {core['Type']:<10}\n"
    
    # Download button
    st.download_button(
        label=f"📥 Download Full List ({len(core_list)} cores)",
        data=text_output,
        file_name=f"{mode}_power_rankings.txt",
        mime="text/plain"
    )
    
    # Show in expander
    with st.expander(f"👁️ View All {len(core_list)} Cores"):
        st.text(text_output)

else:
    st.info("👆 Click 'Fetch Active Cores' to load the list")
    
    with st.expander("ℹ️ What does this do?"):
        st.markdown("""
        This test page will:
        1. Fetch all open races for the selected mode
        2. Extract all unique core IDs from those races
        3. Fetch power stats for all cores (using bulk API)
        4. Sort by Power percentage (highest first)
        5. Display top 30 with full details
        6. Provide downloadable complete list
        
        This is a test to verify the data before integrating into the main Power Rankings page.
        """)
