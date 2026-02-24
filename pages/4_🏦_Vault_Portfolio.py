import streamlit as st
import requests
import pandas as pd
from typing import Optional, List, Dict
from datetime import datetime, timedelta

st.set_page_config(page_title="Vault Portfolio", page_icon="🏦", layout="wide")

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


st.title("🏦 Vault Portfolio Dashboard")
st.markdown("Analyze your vault's complete collection and get breeding recommendations")

# ==================
# SEARCH SECTION
# ==================
st.subheader("🔍 Search Vault")

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
    search_btn = st.button("🔍 Search Vault", type="primary", use_container_width=True)

if search_btn and vault_input:
    
    # Determine vault address
    vault_address = vault_input.lower() if vault_input.startswith("0x") else vault_input
    vault_name = vault_input if not vault_input.startswith("0x") else None
    
    # Fetch vault cores
    with st.spinner("Loading vault data..."):
        cores = fetch_api("/vault/bikes_inf", {"vault": vault_address})
    
    if not cores or len(cores) == 0:
        st.error("❌ No cores found for this vault")
        st.stop()
    
    # Separate trainers and regular cores
    trainer_cores = [c for c in cores if c.get('is_trainer', False)]
    regular_cores = [c for c in cores if not c.get('is_trainer', False)]
    
    st.success(f"✓ Found {len(cores)} total cores ({len(trainer_cores)} trainers, {len(regular_cores)} regular)")
    
    # Store in session state
    st.session_state.vault_cores = regular_cores
    st.session_state.vault_address = vault_address
    st.session_state.vault_name = vault_name
    
    st.divider()

# Display if vault is loaded
if 'vault_cores' in st.session_state:
    cores = st.session_state.vault_cores
    
    # ==================
    # TABS: OVERVIEW vs BREEDING
    # ==================
    tab1, tab2 = st.tabs(["📊 Vault Overview", "🧬 Breeding Suggestions"])
    
    # ==================
    # TAB 1: VAULT OVERVIEW
    # ==================
    with tab1:
        st.header("📊 Vault Overview")
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Cores", len(cores))
        
        # Element breakdown
        elements = {}
        for core in cores:
            elem = core.get('element', 'unknown')
            elements[elem] = elements.get(elem, 0) + 1
        
        with col2:
            most_common = max(elements, key=elements.get) if elements else "N/A"
            st.metric("Most Common Element", most_common.title())
        
        # Type breakdown
        types = {}
        for core in cores:
            core_type = core.get('type', 'unknown')
            types[core_type] = types.get(core_type, 0) + 1
        
        with col3:
            genesis_count = types.get('genesis', 0)
            st.metric("Genesis Cores", genesis_count)
        
        with col4:
            spliced_count = len(cores) - genesis_count
            st.metric("Spliced Cores", spliced_count)
        
        st.divider()
        
        # ==================
        # FILTERS
        # ==================
        st.subheader("🔍 Filters")
        
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
        
        with filter_col1:
            element_filter = st.multiselect(
                "Element",
                options=['water', 'fire', 'earth', 'air'],
                default=[]
            )
        
        with filter_col2:
            type_filter = st.multiselect(
                "Type",
                options=['genesis', 'spliced'],
                default=[]
            )
        
        with filter_col3:
            gender_filter = st.multiselect(
                "Gender",
                options=['male', 'female'],
                default=[]
            )
        
        with filter_col4:
            fno_filter = st.multiselect(
                "Family (F.No)",
                options=sorted(list(set([c.get('fno', 0) for c in cores]))),
                default=[]
            )
        
        # Apply filters
        filtered_cores = cores
        
        if element_filter:
            filtered_cores = [c for c in filtered_cores if c.get('element') in element_filter]
        
        if type_filter:
            filtered_cores = [c for c in filtered_cores if c.get('type') in type_filter]
        
        if gender_filter:
            filtered_cores = [c for c in filtered_cores if c.get('gender') in gender_filter]
        
        if fno_filter:
            filtered_cores = [c for c in filtered_cores if c.get('fno') in fno_filter]
        
        st.info(f"Showing {len(filtered_cores)} of {len(cores)} cores")
        
        st.divider()
        
        # ==================
        # CORE GRID DISPLAY
        # ==================
        st.subheader(f"🎯 Cores ({len(filtered_cores)})")
        
        # Mode selector and power data loader
        col1, col2 = st.columns([1, 3])
        
        with col1:
            mode_select = st.selectbox(
                "Mode for Power Stats",
                ["bike", "car", "horse"],
                index=0
            )
        
        with col2:
            load_power = st.checkbox("Load Power Stats (may take 30-60s for large vaults)")
        
        if load_power and filtered_cores:
            with st.spinner("Loading power data..."):
                hids = [c['hid'] for c in filtered_cores]
                power_data = fetch_api("/cores/power_bulk", {"hids": hids})
                
                if power_data:
                    power_lookup = {p['hid']: p for p in power_data}
                    st.session_state.power_lookup = power_lookup
                    st.session_state.selected_mode = mode_select
                    st.success(f"✓ Power data loaded for {mode_select.upper()}")
        
        # Update mode if changed
        if 'power_lookup' in st.session_state:
            st.session_state.selected_mode = mode_select
        
        # Display cores in grid (4 per row)
        cols_per_row = 4
        
        for i in range(0, len(filtered_cores), cols_per_row):
            cols = st.columns(cols_per_row)
            row_cores = filtered_cores[i:i+cols_per_row]
            
            for col_idx, core in enumerate(row_cores):
                with cols[col_idx]:
                    with st.container(border=True):
                        # Name and ID
                        st.markdown(f"**{core.get('name', 'Unnamed')}**")
                        st.caption(f"#{core['hid']}")
                        
                        # Badges
                        b1, b2, b3 = st.columns(3)
                        with b1:
                            st.markdown(f'<span style="background:#667eea;color:white;padding:2px 5px;border-radius:3px;font-size:0.7em;">{core.get("type", "?").upper()[:3]}</span>', unsafe_allow_html=True)
                        with b2:
                            st.markdown(f'<span style="background:#764ba2;color:white;padding:2px 5px;border-radius:3px;font-size:0.7em;">{core.get("element", "?").upper()[:3]}</span>', unsafe_allow_html=True)
                        with b3:
                            st.markdown(f'<span style="background:#f59e0b;color:white;padding:2px 5px;border-radius:3px;font-size:0.7em;">F{core.get("fno", "?")}</span>', unsafe_allow_html=True)
                        
                        # Power stats if loaded
                        if load_power and 'power_lookup' in st.session_state:
                            power = st.session_state.power_lookup.get(core['hid'])
                            current_mode = st.session_state.get('selected_mode', 'bike')
                            
                            if power:
                                mode_data = power.get('power', {}).get(current_mode, {})
                                pwr = mode_data.get('power', {}).get('fill', {}).get('per', 0)
                                var = mode_data.get('variance', {}).get('fill', {}).get('per', 0)
                                adj = mode_data.get('adjodds', {}).get('fill', {}).get('per', 0)
                                
                                st.write("")
                                st.caption(f"{current_mode.upper()} Stats:")
                                
                                st.caption("PWR")
                                pwr_color = get_gradient_color(pwr)
                                st.markdown(f'<div style="background:{pwr_color};height:18px;border-radius:3px;text-align:center;line-height:18px;color:white;font-weight:bold;font-size:0.7em;">{pwr:.1f}%</div>', unsafe_allow_html=True)
                                
                                st.caption("VAR")
                                var_color = get_gradient_color(var)
                                st.markdown(f'<div style="background:{var_color};height:18px;border-radius:3px;text-align:center;line-height:18px;color:white;font-weight:bold;font-size:0.7em;">{var:.1f}%</div>', unsafe_allow_html=True)
                                
                                st.caption("ADJ")
                                adj_color = get_gradient_color(adj)
                                st.markdown(f'<div style="background:{adj_color};height:18px;border-radius:3px;text-align:center;line-height:18px;color:white;font-weight:bold;font-size:0.7em;">{adj:.1f}%</div>', unsafe_allow_html=True)
                        
                        st.write("")
                        st.caption(f"{core.get('gender', '?').title()} • {core.get('color', 'Unknown').replace('-', ' ').title()}")
                        
                        # Link button
                        core_url = f"https://fbike.dnaracing.run/core/{core['hid']}"
                        st.link_button("View", core_url, use_container_width=True)
    
    # ==================
    # TAB 2: BREEDING SUGGESTIONS
    # ==================
    with tab2:
        st.header("🧬 Breeding Suggestions")
        st.info("🚧 Coming soon! This will analyze your vault and suggest optimal breeding pairs.")
        
        st.markdown("""
        **Planned Features:**
        - Analyze all cores in vault for breeding compatibility
        - Suggest optimal breeding pairs based on:
          - Power stats
          - Element combinations
          - Family numbers
          - Performance data
        - Calculate expected offspring stats
        - Show breeding profitability
        - Filter by breeding goals (maximize power, specific element, etc.)
        """)

else:
    st.info("👆 Enter a vault address or name above to begin")
    
    with st.expander("💡 Example Vaults to Try"):
        st.markdown("""
        Try searching for:
        - **wisdom-weaver** (example vault name)
        - **0xaf1320faa9a484a4702ec16ffec18260cc42c3c2** (example address)
        
        Or enter your own vault!
        """)
