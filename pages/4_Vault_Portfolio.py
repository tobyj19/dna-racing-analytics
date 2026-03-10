import streamlit as st
import requests
import pandas as pd
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from collections import defaultdict

st.set_page_config(page_title="Vault Portfolio", page_icon="🏦", layout="wide")

API_BASE_URL = "https://api.dnaracing.run/fbike"

# Distance categories
SPRINT_RANGE = list(range(9, 14))      # 900m-1300m (CB 9-13)
MID_RANGE = list(range(14, 19))        # 1400m-1800m (CB 14-18)
MARATHON_RANGE = list(range(19, 24))   # 1900m-2300m (CB 19-23)

# Helper functions
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


def categorize_core_by_distance(stats_data: dict, mode: str) -> set:
    """Determine which distance categories a core excels in"""
    categories = set()
    mode_field = f"hstats_{mode}"  # Correct field name: hstats_bike, hstats_car, hstats_horse
    mode_stats = stats_data.get(mode_field, {})
    
    # Check each distance for >28% win rate
    for cb_str, cb_data in mode_stats.items():
        if cb_str == 'career':  # Skip career summary
            continue
            
        try:
            cb = int(cb_str)
            win_p = cb_data.get('win_p', 0)  # API returns decimal (0.28 = 28%)
            win_rate = win_p * 100  # Convert to percentage
            races = cb_data.get('races_n', 0)  # races_n not 'n'
            
            # Must have >28% win rate and at least 20 races
            if win_rate > 28 and races >= 20:
                if cb in SPRINT_RANGE:
                    categories.add('sprint')
                elif cb in MID_RANGE:
                    categories.add('mid')
                elif cb in MARATHON_RANGE:
                    categories.add('marathon')
        except:
            continue
    
    return categories


st.title("🏦 Vault Portfolio Dashboard")
st.markdown("Analyze your vault's collection and get breeding recommendations")

# Search section
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
    
    vault_address = vault_input.lower() if vault_input.startswith("0x") else vault_input
    vault_name = vault_input if not vault_input.startswith("0x") else None
    
    with st.spinner("Loading vault data..."):
        cores = fetch_api("/vault/bikes_inf", {"vault": vault_address})
    
    if not cores or len(cores) == 0:
        st.error("❌ No cores found for this vault")
        st.stop()
    
    trainer_cores = [c for c in cores if c.get('is_trainer', False)]
    regular_cores = [c for c in cores if not c.get('is_trainer', False)]
    
    st.success(f"✓ Found {len(cores)} total cores ({len(trainer_cores)} trainers, {len(regular_cores)} regular)")
    
    st.session_state.vault_cores = regular_cores
    st.session_state.vault_address = vault_address
    st.session_state.vault_name = vault_name
    
    st.divider()

# Display if vault is loaded
if 'vault_cores' in st.session_state:
    cores = st.session_state.vault_cores
    
    # ==================
    # VAULT OVERVIEW
    # ==================
    st.header("📊 Vault Overview")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Cores", len(cores))
    
    elements = {}
    for core in cores:
        elem = core.get('element', 'unknown')
        elements[elem] = elements.get(elem, 0) + 1
    
    with col2:
        most_common = max(elements, key=elements.get) if elements else "N/A"
        st.metric("Most Common Element", most_common.title())
    
    types = {}
    for core in cores:
        core_type = core.get('type', 'unknown')
        types[core_type] = types.get(core_type, 0) + 1
    
    with col3:
        genesis_count = types.get('genesis', 0)
        st.metric("Genesis Cores", genesis_count)
    
    with col4:
        spliced_count = len(cores) - genesis_count
        st.metric("Other Cores", spliced_count)
    
    st.divider()
    
    # ==================
    # FILTERS & DISPLAY OPTIONS
    # ==================
    st.subheader("🔍 Filters & Display Options")
    
    unique_elements = sorted(list(set([c.get('element', 'unknown') for c in cores if c.get('element')])))
    unique_types = sorted(list(set([c.get('type', 'unknown') for c in cores if c.get('type')])))
    unique_genders = sorted(list(set([c.get('gender', 'unknown') for c in cores if c.get('gender')])))
    
    with st.expander("🔍 Available filter values in this vault", expanded=False):
        st.write(f"**Elements:** {', '.join(unique_elements)}")
        st.write(f"**Types:** {', '.join(unique_types)}")
        st.write(f"**Genders:** {', '.join(unique_genders)}")
    
    # Row 1: Core filters
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        element_filter = st.multiselect(
            "Element",
            options=unique_elements,
            default=[]
        )
    
    with filter_col2:
        type_filter = st.multiselect(
            "Type",
            options=unique_types,
            default=[]
        )
    
    with filter_col3:
        gender_filter = st.multiselect(
            "Gender",
            options=unique_genders,
            default=[]
        )
    
    # Row 2: Display options
    display_col1, display_col2, display_col3 = st.columns(3)
    
    with display_col1:
        display_mode = st.radio(
            "Display Mode",
            ["Cards", "Table"],
            horizontal=True
        )
    
    with display_col2:
        mode_select = st.selectbox(
            "Mode",
            ["bike", "car", "horse"],
            index=0
        )
    
    with display_col3:
        if display_mode == "Cards":
            if st.button("⚡ Load Power Stats", use_container_width=True):
                st.session_state.load_power_data = True
        else:
            if st.button("📊 Load Racing Stats", use_container_width=True):
                st.session_state.load_racing_data = True
    
    # Check if data should be loaded
    if display_mode == "Cards":
        load_data = st.session_state.get('load_power_data', False)
    else:
        load_data = st.session_state.get('load_racing_data', False)
    
    # Apply core filters
    filtered_cores = cores
    
    if element_filter:
        filtered_cores = [c for c in filtered_cores if c.get('element') in element_filter]
    
    if type_filter:
        filtered_cores = [c for c in filtered_cores if c.get('type') in type_filter]
    
    if gender_filter:
        filtered_cores = [c for c in filtered_cores if c.get('gender') in gender_filter]
    
    st.info(f"Showing {len(filtered_cores)} of {len(cores)} cores")
    
    st.divider()
    
    # ==================
    # DISPLAY CORES
    # ==================
    st.subheader(f"🎯 Cores ({len(filtered_cores)})")
    
    # CARDS VIEW
    if display_mode == "Cards":
        if load_data and filtered_cores:
            with st.spinner("Loading power data..."):
                hids = [c['hid'] for c in filtered_cores]
                power_data = fetch_api("/cores/power_bulk", {"hids": hids})
                
                if power_data:
                    st.session_state.power_lookup = {p['hid']: p for p in power_data}
                    st.success(f"✓ Power data loaded for {mode_select.upper()}")
        
        if 'power_lookup' in st.session_state:
            st.session_state.selected_mode = mode_select
        
        cols_per_row = 4
        
        for i in range(0, len(filtered_cores), cols_per_row):
            cols = st.columns(cols_per_row)
            row_cores = filtered_cores[i:i+cols_per_row]
            
            for col_idx, core in enumerate(row_cores):
                with cols[col_idx]:
                    with st.container(border=True):
                        st.markdown(f"**{core.get('name', 'Unnamed')}**")
                        st.caption(f"#{core['hid']}")
                        
                        b1, b2, b3 = st.columns(3)
                        with b1:
                            st.markdown(f'<span style="background:#667eea;color:white;padding:2px 5px;border-radius:3px;font-size:0.7em;">{core.get("type", "?").upper()[:3]}</span>', unsafe_allow_html=True)
                        with b2:
                            st.markdown(f'<span style="background:#764ba2;color:white;padding:2px 5px;border-radius:3px;font-size:0.7em;">{core.get("element", "?").upper()[:3]}</span>', unsafe_allow_html=True)
                        with b3:
                            st.markdown(f'<span style="background:#f59e0b;color:white;padding:2px 5px;border-radius:3px;font-size:0.7em;">F{core.get("fno", "?")}</span>', unsafe_allow_html=True)
                        
                        if load_data and 'power_lookup' in st.session_state:
                            power = st.session_state.power_lookup.get(core['hid'])
                            current_mode = st.session_state.get('selected_mode', 'bike')
                            
                            if power:
                                mode_data = power.get('power', {}).get(current_mode, {})
                                pwr = mode_data.get('power', {}).get('fill', {}).get('per', 0)
                                var = mode_data.get('variance', {}).get('fill', {}).get('per', 0)
                                adj = mode_data.get('adjodds', {}).get('fill', {}).get('per', 0)
                                
                                st.write("")
                                st.caption(f"{current_mode.upper()}:")
                                
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
                        
                        core_url = f"https://fbike.dnaracing.run/core/{core['hid']}"
                        st.link_button("View", core_url, use_container_width=True)
    
    # TABLE VIEW
    else:
        if load_data and filtered_cores:
            hids = [c['hid'] for c in filtered_cores]
            
            # Load racing stats with retry
            stats_loaded = False
            for attempt in range(3):
                try:
                    with st.spinner(f"Loading racing stats (attempt {attempt + 1}/3)..."):
                        stats_data = fetch_api("/cores/racing_stats_bulk", {"hids": hids}, timeout=240)
                        if stats_data:
                            st.session_state.stats_lookup = {s['hid']: s for s in stats_data}
                            st.success(f"✓ Loaded racing stats for {len(hids)} cores")
                            stats_loaded = True
                            break
                except Exception as e:
                    if attempt < 2:
                        st.warning(f"Attempt {attempt + 1} failed, retrying...")
                    else:
                        st.error(f"Failed to load racing stats after 3 attempts: {str(e)}")
            
            if not stats_loaded:
                st.error("❌ Unable to load racing stats. Try with fewer cores or try again later.")
                st.stop()
            
            # Load race history in batches
            with st.spinner("Loading race history..."):
                batch_size = 25
                races_data = {}
                
                if len(hids) > 100:
                    st.warning(f"⚠️ Large vault ({len(hids)} cores) - Loading race history may take 2-5 minutes...")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i in range(0, len(hids), batch_size):
                    batch = hids[i:i+batch_size]
                    batch_num = (i // batch_size) + 1
                    total_batches = (len(hids) + batch_size - 1) // batch_size
                    
                    status_text.text(f"Loading race history: Batch {batch_num}/{total_batches} ({len(batch)} cores)...")
                    
                    for hid in batch:
                        try:
                            race_history = fetch_api("/i/hraces", {"hid": hid, "rvmode": mode_select, "limit": 500}, timeout=120)
                            if race_history:
                                races_data[hid] = race_history
                        except:
                            pass  # Continue with others
                    
                    progress = min((i + batch_size) / len(hids), 1.0)
                    progress_bar.progress(progress)
                
                st.session_state.races_lookup = races_data
                progress_bar.empty()
                status_text.empty()
                st.success(f"✓ Loaded race history for {len(races_data)}/{len(hids)} cores")
        
        if 'stats_lookup' in st.session_state and load_data:
            
            # Distance filter buttons
            st.markdown("**📏 Filter by Distance:**")
            
            # Initialize from session state
            if 'distance_filter' not in st.session_state:
                st.session_state.distance_filter = []
            
            distance_filter = st.session_state.distance_filter
            
            button_cols = st.columns([1] + [1]*15)
            
            with button_cols[0]:
                if st.button("All", use_container_width=True, type="primary" if not distance_filter else "secondary"):
                    st.session_state.distance_filter = []
                    st.rerun()
            
            for idx, cb in enumerate(range(9, 24), start=1):
                with button_cols[idx]:
                    is_selected = cb in distance_filter if distance_filter else False
                    if st.button(
                        f"{cb*100}m", 
                        use_container_width=True,
                        type="primary" if is_selected else "secondary",
                        key=f"dist_btn_{cb}"
                    ):
                        st.session_state.distance_filter = [cb]
                        st.rerun()
            
            st.divider()
            
            # Show what's being displayed
            if distance_filter:
                st.info(f"📊 Showing stats for {distance_filter[0]*100}m only")
            else:
                st.info(f"📊 Showing career totals (all distances)")
            
            st.divider()
            table_rows = []
            races_lookup = st.session_state.get('races_lookup', {})
            
            for core in filtered_cores:
                stats = st.session_state.stats_lookup.get(core['hid'], {})
                mode_field = f"hstats_{mode_select}"
                mode_stats = stats.get(mode_field, {})
                core_races = races_lookup.get(core['hid'], [])
                
                row = {
                    'HID': core['hid'],
                    'Name': core.get('name', 'Unnamed'),
                    'El': core.get('element', '?')[0].upper(),
                    'G': core.get('gender', '?')[0].upper(),
                    'Type': core.get('type', '?').title()
                }
                
                # CASE 1: Distance filter selected - show stats for that distance only
                if distance_filter:
                    cb = distance_filter[0]
                    
                    # Get stats for this distance
                    cb_stats = mode_stats.get(str(cb), {})
                    races_n = cb_stats.get('races_n', 0)
                    win_p = cb_stats.get('win_p', 0)
                    p2_n = cb_stats.get('p2_n', 0)
                    p3_n = cb_stats.get('p3_n', 0)
                    
                    # Calculate place % (wins + 2nd + 3rd)
                    wins = int(races_n * win_p) if races_n > 0 else 0
                    places = wins + p2_n + p3_n
                    place_pct = (places / races_n * 100) if races_n > 0 else 0
                    
                    row['Races'] = races_n
                    row['Wr%'] = f"{win_p * 100:.1f}%" if races_n > 0 else "-"
                    row['Place%'] = f"{place_pct:.1f}%" if races_n > 0 else "-"
                    
                    # Star % for this distance only
                    # IMPORTANT: Filter by 'class' field, not 'cb'
                    # class 10 = 1000m, class 11 = 1100m, etc.
                    if core_races:
                        # DEBUG: Show first race structure to understand fields
                        if core['hid'] == 588 and cb == 10:
                            st.write("DEBUG - First race structure:")
                            st.json(core_races[0] if core_races else {})
                            st.write(f"Looking for class={cb*100} in {len(core_races)} total races")
                        
                        # Try both 'class' and 'cb' fields to see which works
                        distance_races_by_class = [r for r in core_races if r.get('class') == cb * 100]
                        distance_races_by_cb = [r for r in core_races if r.get('cb') == cb]
                        
                        if core['hid'] == 588 and cb == 10:
                            st.write(f"Found by class={cb*100}: {len(distance_races_by_class)} races")
                            st.write(f"Found by cb={cb}: {len(distance_races_by_cb)} races")
                        
                        # Use whichever finds races
                        distance_races = distance_races_by_class if distance_races_by_class else distance_races_by_cb
                        
                        if distance_races:
                            total = len(distance_races)
                            blue = len([r for r in distance_races if r.get('star') in [2, 5]])
                            gold = len([r for r in distance_races if r.get('star') in [3, 5]])
                            
                            row['Blue star%'] = f"{(blue/total*100):.1f}%"
                            row['Gold star%'] = f"{(gold/total*100):.1f}%"
                        else:
                            row['Blue star%'] = "-"
                            row['Gold star%'] = "-"
                    else:
                        row['Blue star%'] = "-"
                        row['Gold star%'] = "-"
                
                # CASE 2: No filter - show career totals
                else:
                    career_stats = mode_stats.get('career', {})
                    races_n = career_stats.get('races_n', 0)
                    win_p = career_stats.get('win_p', 0)
                    p2_n = career_stats.get('p2_n', 0)
                    p3_n = career_stats.get('p3_n', 0)
                    
                    # Calculate place %
                    wins = int(races_n * win_p) if races_n > 0 else 0
                    places = wins + p2_n + p3_n
                    place_pct = (places / races_n * 100) if races_n > 0 else 0
                    
                    row['Races'] = races_n
                    row['Wr%'] = f"{win_p * 100:.1f}%" if races_n > 0 else "-"
                    row['Place%'] = f"{place_pct:.1f}%" if races_n > 0 else "-"
                    
                    # Star % for all races
                    if core_races:
                        total = len(core_races)
                        blue = len([r for r in core_races if r.get('star') in [2, 5]])
                        gold = len([r for r in core_races if r.get('star') in [3, 5]])
                        
                        row['Blue star%'] = f"{(blue/total*100):.1f}%"
                        row['Gold star%'] = f"{(gold/total*100):.1f}%"
                    else:
                        row['Blue star%'] = "-"
                        row['Gold star%'] = "-"
                
                table_rows.append(row)
            
            df = pd.DataFrame(table_rows)
            
            # Display table
            st.dataframe(
                df, 
                use_container_width=True, 
                height=600, 
                hide_index=True,
                column_config={
                    "Races": st.column_config.NumberColumn("Races", help="Total races"),
                    "Wr%": st.column_config.TextColumn("Wr%", help="Win rate percentage"),
                    "Place%": st.column_config.TextColumn("Place%", help="1st, 2nd, or 3rd place percentage"),
                    "Blue star%": st.column_config.TextColumn("⭐ Blue%", help="Blue star percentage (includes doubles)"),
                    "Gold star%": st.column_config.TextColumn("⭐ Gold%", help="Gold star percentage (includes doubles)")
                }
            )
            
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                csv,
                f"vault_{mode_select}_{'filtered' if distance_filter else 'career'}.csv",
                "text/csv"
            )
        else:
            st.info("👆 Check 'Load Racing Stats' to see table")
    

else:
    st.info("👆 Enter a vault address or name above to begin")
    
    with st.expander("💡 Example Vaults"):
        st.markdown("""
        **Try searching:**
        - wisdom-weaver
        - Your own vault address
        """)
