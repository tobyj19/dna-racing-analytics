import streamlit as st
import requests
from typing import Optional, Tuple

st.set_page_config(page_title="Core Search", page_icon="🔍", layout="wide")

st.title("🔍 Core Search & Overview")
st.markdown("Search for a DNA Racing core and view its basic information")

# API Configuration
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

def fetch_core_data(hid: int) -> Tuple[Optional[dict], Optional[dict], Optional[dict], Optional[list]]:
    """Fetch all core data"""
    with st.spinner(f"Fetching data for Core #{hid}..."):
        mini = fetch_api("/cores/mini", {"hid": hid})
        power = fetch_api("/cores/power", {"hid": hid})
        stats = fetch_api("/cores/racing_stats", {"hid": hid})
        races = fetch_api("/i/hraces", {"hid": hid, "limit": 10000})
    
    return mini, power, stats, races

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
    races = st.session_state.races
    
    st.divider()
    
    # Core header
    st.header(f"Core #{mini['hid']} - {mini.get('name', 'Unnamed')}")
    
    # Basic info cards
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
        st.metric("Hex Code", f"#{mini['hex_code']}")
    
    st.divider()
    
    # Power statistics
    st.subheader("⚡ Power Statistics")
    
    mode_cols = st.columns(3)
    
    for idx, mode in enumerate(['bike', 'car', 'horse']):
        if mode not in power['power']:
            continue
        
        with mode_cols[idx]:
            st.markdown(f"### {mode.upper()}")
            mode_data = power['power'][mode]
            
            # Power
            power_pct = mode_data['power']['fill']['per']
            st.markdown(f"**Power:** {power_pct:.1f}%")
            st.progress(power_pct / 100)
            
            # Variance
            var_pct = mode_data['variance']['fill']['per']
            st.markdown(f"**Variance:** {var_pct:.1f}%")
            st.progress(var_pct / 100)
            
            # Adj Odds
            odds_pct = mode_data['adjodds']['fill']['per']
            st.markdown(f"**Adj Odds:** {odds_pct:.1f}%")
            st.progress(odds_pct / 100)
    
    st.divider()
    
    # Quick race summary
    st.subheader("📈 Quick Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Races", len(races))
    
    mode_counts = {}
    for race in races:
        mode = race.get('rvmode', 'unknown')
        mode_counts[mode] = mode_counts.get(mode, 0) + 1
    
    for idx, (mode, count) in enumerate(mode_counts.items(), 1):
        if idx == 1:
            col2.metric(f"{mode.upper()} Races", count)
        elif idx == 2:
            col3.metric(f"{mode.upper()} Races", count)
        elif idx == 3:
            col4.metric(f"{mode.upper()} Races", count)
    
    st.divider()
    
    # Owner info
    st.subheader("👤 Owner Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Vault Address", mini['vault'], disabled=True)
    with col2:
        st.text_input("Vault Name", mini.get('vault_name', 'Unknown'), disabled=True)
    
    st.info("📊 Navigate to **Performance Analysis** to see detailed statistics and recommendations!")

else:
    st.info("👆 Enter a Core ID above and click 'Search Core' to begin")
    
    # Example
    with st.expander("💡 Example Cores"):
        st.markdown("""
        Try searching for these example cores:
        - **Core #192** - Well-rounded performer
        - **Core #10** - Linen (Genesis)
        - **Core #11** - Grinning Gears (Genesis)
        """)
