import streamlit as st
import requests
import pandas as pd
from typing import Optional, List, Dict
import time

st.set_page_config(page_title="Power Database", page_icon="🗄️", layout="wide")

API_BASE_URL = "https://api.dnaracing.run/fbike"

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
        return None


def get_gradient_color(percentage):
    """Calculate color: blue (0%) → green (50%) → red (100%)"""
    if percentage <= 50:
        ratio = percentage / 50
        r = 0
        g = int(255 * ratio)
        b = int(255 * (1 - ratio))
    else:
        ratio = (percentage - 50) / 50
        r = int(255 * ratio)
        g = int(255 * (1 - ratio))
        b = 0
    return f"#{r:02x}{g:02x}{b:02x}"


st.title("🗄️ Power Database")
st.markdown("Search and filter core power statistics across all modes")

# Input method selector
input_method = st.radio(
    "Data Source:",
    ["Scan Core ID Range", "Load from Vault", "Enter Specific IDs"],
    horizontal=True
)

cores_to_scan = []

if input_method == "Scan Core ID Range":
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        start_id = st.number_input("Start Core ID", min_value=1, value=1, step=1)
    
    with col2:
        end_id = st.number_input("End Core ID", min_value=1, value=1000, step=1)
    
    with col3:
        st.write("")
        st.write("")
        if st.button("🔍 Scan Range", type="primary", use_container_width=True):
            if end_id >= start_id:
                cores_to_scan = list(range(start_id, end_id + 1))
                st.session_state.cores_to_scan = cores_to_scan
                st.info(f"Will scan {len(cores_to_scan)} core IDs")
            else:
                st.error("End ID must be greater than Start ID")

elif input_method == "Load from Vault":
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_type = st.radio("Search by:", ["Vault Address", "Vault Name"], horizontal=True)
        
        if search_type == "Vault Address":
            vault_input = st.text_input("Enter Vault Address", placeholder="0xaf1320...")
        else:
            vault_input = st.text_input("Enter Vault Name", placeholder="wisdom-weaver")
    
    with col2:
        st.write("")
        st.write("")
        if st.button("🔍 Load Vault", type="primary", use_container_width=True):
            if vault_input:
                vault_address = vault_input.lower() if vault_input.startswith("0x") else vault_input
                
                with st.spinner("Loading vault..."):
                    vault_cores = fetch_api("/vault/bikes_inf", {"vault": vault_address})
                
                if vault_cores:
                    regular_cores = [c for c in vault_cores if not c.get('is_trainer', False)]
                    cores_to_scan = [c['hid'] for c in regular_cores]
                    st.session_state.cores_to_scan = cores_to_scan
                    st.success(f"✓ Loaded {len(cores_to_scan)} cores from vault")
                else:
                    st.error("Failed to load vault")

else:  # Enter Specific IDs
    core_ids_input = st.text_area(
        "Enter Core IDs (comma-separated or one per line)",
        placeholder="588, 599, 192\nor\n588\n599\n192",
        height=100
    )
    
    if st.button("🔍 Load Cores", type="primary"):
        if core_ids_input:
            ids_str = core_ids_input.replace('\n', ',').replace(' ', '')
            cores_to_scan = [int(x.strip()) for x in ids_str.split(',') if x.strip().isdigit()]
            
            if cores_to_scan:
                st.session_state.cores_to_scan = cores_to_scan
                st.success(f"✓ Will load {len(cores_to_scan)} cores")
            else:
                st.error("No valid core IDs found")

st.divider()

# Process and display data
if 'cores_to_scan' in st.session_state and st.session_state.cores_to_scan:
    hids = st.session_state.cores_to_scan
    
    if st.button("⚡ Load Power Data", type="primary", use_container_width=True):
        
        st.info(f"📊 Loading power data for {len(hids)} cores...")
        
        with st.spinner("Fetching core information and power stats..."):
            # Batch processing
            batch_size = 100
            all_core_info = []
            all_power_data = {}
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i in range(0, len(hids), batch_size):
                batch = hids[i:i+batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(hids) + batch_size - 1) // batch_size
                
                status_text.text(f"Loading batch {batch_num}/{total_batches} ({len(batch)} cores)...")
                
                # Fetch basic info
                core_info = fetch_api("/cores/mini_bulk", {"hids": batch}, timeout=120)
                if core_info:
                    all_core_info.extend(core_info)
                
                # Fetch power data
                power_data = fetch_api("/cores/power_bulk", {"hids": batch}, timeout=120)
                if power_data:
                    for p in power_data:
                        all_power_data[p['hid']] = p
                
                progress = min((i + batch_size) / len(hids), 1.0)
                progress_bar.progress(progress)
                
                # Small delay to avoid rate limiting
                time.sleep(0.2)
            
            progress_bar.empty()
            status_text.empty()
        
        st.success(f"✓ Loaded data for {len(all_core_info)} cores")
        
        # Store in session state
        st.session_state.core_database = all_core_info
        st.session_state.power_database = all_power_data
        
        st.rerun()

# Display database if loaded
if 'core_database' in st.session_state and 'power_database' in st.session_state:
    cores = st.session_state.core_database
    power_data = st.session_state.power_database
    
    st.header("🗄️ Power Database")
    st.caption(f"Showing {len(cores)} cores")
    
    # Filters
    st.subheader("🔍 Filters")
    
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
    
    with filter_col1:
        elements = sorted(list(set([c.get('element', 'unknown') for c in cores])))
        element_filter = st.multiselect("Element", elements, default=[])
    
    with filter_col2:
        types = sorted(list(set([c.get('type', 'unknown') for c in cores])))
        type_filter = st.multiselect("Type", types, default=[])
    
    with filter_col3:
        genders = sorted(list(set([c.get('gender', 'unknown') for c in cores])))
        gender_filter = st.multiselect("Gender", genders, default=[])
    
    with filter_col4:
        mode_display = st.selectbox("Display Mode Stats", ["All Modes", "Bike Only", "Car Only", "Horse Only"])
    
    # Power range filters
    st.markdown("**Power Range Filters:**")
    power_col1, power_col2, power_col3 = st.columns(3)
    
    with power_col1:
        pwr_min = st.slider("Min Bike PWR %", 0, 100, 0)
    
    with power_col2:
        var_min = st.slider("Min Bike VAR %", 0, 100, 0)
    
    with power_col3:
        adj_min = st.slider("Min Bike ADJ %", 0, 100, 0)
    
    st.divider()
    
    # Build table
    table_rows = []
    
    for core in cores:
        # Apply basic filters
        if element_filter and core.get('element') not in element_filter:
            continue
        if type_filter and core.get('type') not in type_filter:
            continue
        if gender_filter and core.get('gender') not in gender_filter:
            continue
        
        power = power_data.get(core['hid'], {})
        power_stats = power.get('power', {})
        
        # Get bike stats for filtering
        bike_stats = power_stats.get('bike', {})
        bike_pwr = bike_stats.get('power', {}).get('fill', {}).get('per', 0)
        bike_var = bike_stats.get('variance', {}).get('fill', {}).get('per', 0)
        bike_adj = bike_stats.get('adjodds', {}).get('fill', {}).get('per', 0)
        
        # Apply power filters
        if bike_pwr < pwr_min or bike_var < var_min or bike_adj < adj_min:
            continue
        
        row = {
            'HID': core['hid'],
            'Name': core.get('name', 'Unnamed'),
            'Element': core.get('element', '?'),
            'Type': core.get('type', '?'),
            'Gender': core.get('gender', '?'),
        }
        
        # Add stats based on display mode
        if mode_display in ["All Modes", "Bike Only"]:
            row['🚲 PWR'] = f"{bike_pwr:.1f}%"
            row['🚲 VAR'] = f"{bike_var:.1f}%"
            row['🚲 ADJ'] = f"{bike_adj:.1f}%"
        
        if mode_display in ["All Modes", "Car Only"]:
            car_stats = power_stats.get('car', {})
            car_pwr = car_stats.get('power', {}).get('fill', {}).get('per', 0)
            car_var = car_stats.get('variance', {}).get('fill', {}).get('per', 0)
            car_adj = car_stats.get('adjodds', {}).get('fill', {}).get('per', 0)
            
            row['🚗 PWR'] = f"{car_pwr:.1f}%"
            row['🚗 VAR'] = f"{car_var:.1f}%"
            row['🚗 ADJ'] = f"{car_adj:.1f}%"
        
        if mode_display in ["All Modes", "Horse Only"]:
            horse_stats = power_stats.get('horse', {})
            horse_pwr = horse_stats.get('power', {}).get('fill', {}).get('per', 0)
            horse_var = horse_stats.get('variance', {}).get('fill', {}).get('per', 0)
            horse_adj = horse_stats.get('adjodds', {}).get('fill', {}).get('per', 0)
            
            row['🐴 PWR'] = f"{horse_pwr:.1f}%"
            row['🐴 VAR'] = f"{horse_var:.1f}%"
            row['🐴 ADJ'] = f"{horse_adj:.1f}%"
        
        table_rows.append(row)
    
    st.info(f"📊 Showing {len(table_rows)} cores (after filters)")
    
    if table_rows:
        df = pd.DataFrame(table_rows)
        
        # Display table
        st.dataframe(
            df,
            use_container_width=True,
            height=600,
            hide_index=True
        )
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download Database as CSV",
            csv,
            f"power_database_{len(table_rows)}_cores.csv",
            "text/csv"
        )
        
        # Quick stats
        st.divider()
        st.subheader("📈 Quick Stats")
        
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        with stat_col1:
            st.metric("Total Cores", len(table_rows))
        
        with stat_col2:
            bike_pwrs = [float(r['🚲 PWR'].rstrip('%')) for r in table_rows if '🚲 PWR' in r]
            avg_pwr = sum(bike_pwrs) / len(bike_pwrs) if bike_pwrs else 0
            st.metric("Avg Bike PWR", f"{avg_pwr:.1f}%")
        
        with stat_col3:
            bike_vars = [float(r['🚲 VAR'].rstrip('%')) for r in table_rows if '🚲 VAR' in r]
            avg_var = sum(bike_vars) / len(bike_vars) if bike_vars else 0
            st.metric("Avg Bike VAR", f"{avg_var:.1f}%")
        
        with stat_col4:
            bike_adjs = [float(r['🚲 ADJ'].rstrip('%')) for r in table_rows if '🚲 ADJ' in r]
            avg_adj = sum(bike_adjs) / len(bike_adjs) if bike_adjs else 0
            st.metric("Avg Bike ADJ", f"{avg_adj:.1f}%")
    else:
        st.warning("No cores match the current filters")

else:
    st.info("👆 Select a data source and load cores to begin")
    
    with st.expander("💡 How to Use"):
        st.markdown("""
        **Power Database** lets you search and analyze core power statistics.
        
        **Data Sources:**
        - **Scan Core ID Range:** Check cores from ID X to ID Y (e.g., 1-1000)
        - **Load from Vault:** Import all cores from a specific vault
        - **Enter Specific IDs:** Paste a list of core IDs to analyze
        
        **Features:**
        - View PWR, VAR, and ADJ odds for Bike/Car/Horse
        - Filter by element, type, gender
        - Filter by minimum power thresholds
        - Sort by any column (click header)
        - Export to CSV
        
        **Tips:**
        - Start with smaller ranges (100-500 cores) to test
        - Use filters to find high-performers
        - Download results for offline analysis
        - Scanning large ranges (5000+) may take several minutes
        
        **Example Searches:**
        - "Show all genesis cores with Bike PWR > 80%"
        - "Find fire element cores with high variance"
        - "Compare power stats across my vault"
        """)
