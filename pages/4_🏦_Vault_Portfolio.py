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
    
    # Tabs
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
        
        # Filters
        st.subheader("🔍 Filters")
        
        unique_elements = sorted(list(set([c.get('element', 'unknown') for c in cores if c.get('element')])))
        unique_types = sorted(list(set([c.get('type', 'unknown') for c in cores if c.get('type')])))
        unique_genders = sorted(list(set([c.get('gender', 'unknown') for c in cores if c.get('gender')])))
        
        with st.expander("🔍 Available filter values in this vault", expanded=False):
            st.write(f"**Elements:** {', '.join(unique_elements)}")
            st.write(f"**Types:** {', '.join(unique_types)}")
            st.write(f"**Genders:** {', '.join(unique_genders)}")
        
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
        
        # Apply filters
        filtered_cores = cores
        
        if element_filter:
            filtered_cores = [c for c in filtered_cores if c.get('element') in element_filter]
        
        if type_filter:
            filtered_cores = [c for c in filtered_cores if c.get('type') in type_filter]
        
        if gender_filter:
            filtered_cores = [c for c in filtered_cores if c.get('gender') in gender_filter]
        
        st.info(f"Showing {len(filtered_cores)} of {len(cores)} cores")
        
        st.divider()
        
        # Display mode selector
        st.subheader(f"🎯 Cores ({len(filtered_cores)})")
        
        display_col1, display_col2, display_col3 = st.columns([1, 2, 2])
        
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
            
            if display_mode == "Cards":
                load_data = st.checkbox("Load Power Stats")
            else:
                load_data = st.checkbox("Load Racing Stats")
        
        with display_col3:
            if display_mode == "Table":
                distance_filter = st.multiselect(
                    "Filter Distances",
                    options=list(range(9, 24)),
                    default=[],
                    format_func=lambda x: f"{x*100}m"
                )
        
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
                with st.spinner("Loading racing stats and race history..."):
                    hids = [c['hid'] for c in filtered_cores]
                    
                    # Load racing stats (fast - one bulk call)
                    stats_data = fetch_api("/cores/racing_stats_bulk", {"hids": hids}, timeout=180)
                    if stats_data:
                        st.session_state.stats_lookup = {s['hid']: s for s in stats_data}
                        st.success(f"✓ Loaded racing stats for {len(hids)} cores")
                    
                    # Load race history ONCE for star calculations and distance filtering
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
                            except Exception as e:
                                pass  # Continue loading others
                        
                        progress = min((i + batch_size) / len(hids), 1.0)
                        progress_bar.progress(progress)
                    
                    st.session_state.races_lookup = races_data
                    progress_bar.empty()
                    status_text.empty()
                    st.success(f"✓ Loaded race history for {len(races_data)}/{len(hids)} cores")
            
            if 'stats_lookup' in st.session_state and load_data:
                
                # Distance filter buttons
                st.markdown("**📏 Filter by Distance:**")
                
                button_cols = st.columns([1] + [1]*15)
                
                with button_cols[0]:
                    if st.button("All", use_container_width=True, type="primary" if not distance_filter else "secondary"):
                        distance_filter = []
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
                            distance_filter = [cb]
                            st.rerun()
                
                st.divider()
                
                # Show what's being displayed
                if distance_filter:
                    st.info(f"📊 Showing stats for {distance_filter[0]*100}m only")
                else:
                    st.info(f"📊 Showing career totals (all distances)")
                
                # Build table
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
                        if core_races:
                            distance_races = [r for r in core_races if r.get('cb') == cb]
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
    
    # ==================
    # TAB 2: BREEDING SUGGESTIONS
    # ==================
    with tab2:
        st.header("🧬 Breeding Suggestions")
        
        st.info(f"📊 Analyzing all {len(cores)} cores in vault (filters don't apply here)")
        
        # Fetch all needed data
        with st.spinner("Loading breeding and performance data..."):
            hids = [c['hid'] for c in cores]
            
            breeding_data = fetch_api("/cores/splicing_info_bulk", {"hids": hids})
            
            if 'power_lookup' not in st.session_state:
                power_data = fetch_api("/cores/power_bulk", {"hids": hids})
                if power_data:
                    st.session_state.power_lookup = {p['hid']: p for p in power_data}
            
            if 'stats_lookup' not in st.session_state:
                stats_data = fetch_api("/cores/racing_stats_bulk", {"hids": hids})
                if stats_data:
                    st.session_state.stats_lookup = {s['hid']: s for s in stats_data}
        
        if not breeding_data:
            st.error("Failed to load breeding data")
            st.stop()
        
        breeding_lookup = {b['splice_core']['hid']: b for b in breeding_data if b.get('splice_core')}
        power_lookup = st.session_state.get('power_lookup', {})
        stats_lookup = st.session_state.get('stats_lookup', {})
        
        # Build core info with categories
        available_cores = []
        categorization_debug = {
            'sprint': 0,
            'mid': 0,
            'marathon': 0,
            'unproven': 0,
            'total_checked': 0
        }
        
        for core in cores:
            breeding_info = breeding_lookup.get(core['hid'])
            if not breeding_info:
                continue
            
            splice_core = breeding_info.get('splice_core', {})
            life_splices = splice_core.get('life_splices_n', 0)
            max_life = splice_core.get('mxlife_splices_n', 999999999)
            
            if life_splices >= max_life:
                continue
            
            power = power_lookup.get(core['hid'], {})
            mode_data = power.get('power', {}).get('bike', {})
            
            stats = stats_lookup.get(core['hid'], {})
            categories = categorize_core_by_distance(stats, 'bike')
            
            categorization_debug['total_checked'] += 1
            if 'sprint' in categories:
                categorization_debug['sprint'] += 1
            if 'mid' in categories:
                categorization_debug['mid'] += 1
            if 'marathon' in categories:
                categorization_debug['marathon'] += 1
            if not categories:
                categorization_debug['unproven'] += 1
            
            core_info = {
                'hid': core['hid'],
                'name': core.get('name', 'Unnamed'),
                'element': core.get('element'),
                'type': core.get('type'),
                'gender': core.get('gender'),
                'categories': categories,
                'in_stud': splice_core.get('in_stud', False),
                'price_usd': splice_core.get('price_usd', 0),
                'power': mode_data.get('power', {}).get('fill', {}).get('per', 0),
                'variance': mode_data.get('variance', {}).get('fill', {}).get('per', 0),
                'adjodds': mode_data.get('adjodds', {}).get('fill', {}).get('per', 0),
            }
            available_cores.append(core_info)
        
        # Show debug info
        with st.expander("🔍 Distance Categorization Debug", expanded=True):
            st.write(f"**Total cores analyzed:** {categorization_debug['total_checked']}")
            st.write(f"**Sprint specialists:** {categorization_debug['sprint']} cores (>28% win rate at 900-1300m with 20+ races)")
            st.write(f"**Mid specialists:** {categorization_debug['mid']} cores (>28% win rate at 1400-1800m with 20+ races)")
            st.write(f"**Marathon specialists:** {categorization_debug['marathon']} cores (>28% win rate at 1900-2300m with 20+ races)")
            st.write(f"**Unproven/Unknown:** {categorization_debug['unproven']} cores (don't meet criteria)")
            
            if categorization_debug['unproven'] > categorization_debug['total_checked'] * 0.8:
                st.warning("⚠️ Most cores are unproven. This could mean: (1) Not enough races yet, (2) Win rates below 28%, or (3) Racing stats didn't load. Try loading racing stats in Vault Overview tab first.")
        
        males = [c for c in available_cores if c['gender'] == 'male']
        females = [c for c in available_cores if c['gender'] == 'female']
        
        # Helper function to calculate pairs
        def calculate_breeding_pairs(males, females, category_filter=None, gamble=False):
            pairs = []
            
            for male in males:
                for female in females:
                    # Category filtering
                    if not gamble and category_filter:
                        if category_filter not in male['categories'] or category_filter not in female['categories']:
                            continue
                    
                    # Calculate scores
                    power_score = (male['power'] + female['power']) / 2
                    var_score = (male['variance'] + female['variance']) / 2
                    adj_score = (male['adjodds'] + female['adjodds']) / 2
                    
                    element_bonus = 10 if male['element'] == female['element'] else 0
                    
                    if gamble:
                        # Gamble: Pure power breeding
                        total_score = (power_score * 0.5 + var_score * 0.3 + adj_score * 0.2 + element_bonus)
                    else:
                        # Category breeding: Distance compatibility
                        category_overlap = len(male['categories'] & female['categories'])
                        distance_bonus = category_overlap * 15
                        
                        total_score = (power_score * 0.3 + var_score * 0.2 + adj_score * 0.2 + 
                                      distance_bonus + element_bonus)
                    
                    pairs.append({
                        'male': male,
                        'female': female,
                        'score': total_score,
                        'expected_power': power_score,
                        'expected_var': var_score,
                        'expected_adj': adj_score,
                        'element_match': male['element'] == female['element']
                    })
            
            return sorted(pairs, key=lambda x: x['score'], reverse=True)[:10]
        
        # Create 4 breeding categories
        sprint_pairs = calculate_breeding_pairs(males, females, 'sprint')
        mid_pairs = calculate_breeding_pairs(males, females, 'mid')
        marathon_pairs = calculate_breeding_pairs(males, females, 'marathon')
        gamble_pairs = calculate_breeding_pairs(males, females, gamble=True)
        
        # Display tabs for each category
        cat_tabs = st.tabs(["🏃 Sprint (Top 10)", "🏃‍♂️ Mid-Distance (Top 10)", "🏃‍♀️ Marathon (Top 10)", "🎲 Gamble (Top 10)"])
        
        all_categories = [
            (cat_tabs[0], sprint_pairs, "Sprint", "🏃", "900m-1300m specialists"),
            (cat_tabs[1], mid_pairs, "Mid-Distance", "🏃‍♂️", "1400m-1800m specialists"),
            (cat_tabs[2], marathon_pairs, "Marathon", "🏃‍♀️", "1900m-2300m specialists"),
            (cat_tabs[3], gamble_pairs, "Gamble", "🎲", "⚠️ Pure power breeding - distance unpredictable")
        ]
        
        for tab, pairs, cat_name, icon, desc in all_categories:
            with tab:
                st.markdown(f"**{desc}**")
                
                if not pairs:
                    st.warning(f"No {cat_name} pairs found")
                    continue
                
                st.success(f"Found {len(pairs)} {cat_name} breeding pairs!")
                
                for idx, pair in enumerate(pairs, 1):
                    with st.expander(f"{icon} Pair #{idx} - Score: {pair['score']:.1f}/100", expanded=(idx==1)):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.markdown(f"**♂️ {pair['male']['name']}** (#{pair['male']['hid']})")
                            
                            if pair['male']['categories']:
                                cats = '/'.join([c.title() for c in pair['male']['categories']])
                                st.caption(f"🎯 {cats}")
                            else:
                                st.caption("🎯 Unproven")
                            
                            st.caption(f"{pair['male']['element'].title()} • {pair['male']['type'].title()}")
                            st.caption(f"PWR: {pair['male']['power']:.1f}% | VAR: {pair['male']['variance']:.1f}% | ADJ: {pair['male']['adjodds']:.1f}%")
                            
                            if pair['male']['in_stud']:
                                st.success(f"✅ In Stud - ${pair['male']['price_usd']:.2f}")
                            else:
                                st.warning("❌ Not in stud")
                        
                        with col2:
                            st.markdown(f"**♀️ {pair['female']['name']}** (#{pair['female']['hid']})")
                            
                            if pair['female']['categories']:
                                cats = '/'.join([c.title() for c in pair['female']['categories']])
                                st.caption(f"🎯 {cats}")
                            else:
                                st.caption("🎯 Unproven")
                            
                            st.caption(f"{pair['female']['element'].title()} • {pair['female']['type'].title()}")
                            st.caption(f"PWR: {pair['female']['power']:.1f}% | VAR: {pair['female']['variance']:.1f}% | ADJ: {pair['female']['adjodds']:.1f}%")
                            
                            if pair['female']['in_stud']:
                                st.success(f"✅ In Stud - ${pair['female']['price_usd']:.2f}")
                            else:
                                st.warning("❌ Not in stud")
                        
                        with col3:
                            st.metric("Exp. PWR", f"{pair['expected_power']:.1f}%")
                            st.metric("Exp. VAR", f"{pair['expected_var']:.1f}%")
                            st.metric("Exp. ADJ", f"{pair['expected_adj']:.1f}%")
                        
                        if pair['element_match']:
                            st.info("🎯 Same element - Higher offspring element match probability")

else:
    st.info("👆 Enter a vault address or name above to begin")
    
    with st.expander("💡 Example Vaults"):
        st.markdown("""
        **Try searching:**
        - wisdom-weaver
        - Your own vault address
        """)
