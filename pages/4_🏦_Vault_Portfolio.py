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
        
        if not cores:
            st.warning("Load a vault first to see breeding suggestions")
            st.stop()
        
        # Fetch breeding info for all cores
        with st.spinner("Analyzing vault for breeding opportunities..."):
            hids = [c['hid'] for c in cores]
            breeding_data = fetch_api("/cores/splicing_info_bulk", {"hids": hids})
            power_data = fetch_api("/cores/power_bulk", {"hids": hids}) if 'power_lookup' not in st.session_state else None
        
        if not breeding_data:
            st.error("Failed to load breeding data")
            st.stop()
        
        # Create lookups
        breeding_lookup = {b['splice_core']['hid']: b for b in breeding_data if b.get('splice_core')}
        if power_data:
            st.session_state.power_lookup = {p['hid']: p for p in power_data}
        
        power_lookup = st.session_state.get('power_lookup', {})
        
        # ==================
        # OPTION A: SIMPLE PAIRING RECOMMENDATIONS
        # ==================
        st.subheader("🎯 Top Breeding Pairs")
        st.markdown("Best breeding pairs from your vault based on power stats and compatibility")
        
        # Calculate breeding pairs
        breeding_pairs = []
        available_for_breeding = []
        
        for core in cores:
            breeding_info = breeding_lookup.get(core['hid'])
            if not breeding_info:
                continue
            
            splice_core = breeding_info.get('splice_core', {})
            in_stud = splice_core.get('in_stud', False)
            
            # Check if can breed (has remaining breeds)
            life_splices = splice_core.get('life_splices_n', 0)
            max_life = splice_core.get('mxlife_splices_n', 999999999)
            can_breed = life_splices < max_life
            
            if can_breed:
                power = power_lookup.get(core['hid'], {})
                mode_data = power.get('power', {}).get('bike', {})
                
                core_info = {
                    'hid': core['hid'],
                    'name': core.get('name', 'Unnamed'),
                    'element': core.get('element'),
                    'type': core.get('type'),
                    'fno': core.get('fno'),
                    'gender': core.get('gender'),
                    'in_stud': in_stud,
                    'life_splices': life_splices,
                    'max_life': max_life,
                    'remaining': max_life - life_splices if max_life < 999999999 else "Unlimited",
                    'power': mode_data.get('power', {}).get('fill', {}).get('per', 0),
                    'variance': mode_data.get('variance', {}).get('fill', {}).get('per', 0),
                    'adjodds': mode_data.get('adjodds', {}).get('fill', {}).get('per', 0),
                    'price_usd': splice_core.get('price_usd', 0)
                }
                available_for_breeding.append(core_info)
        
        # Create breeding pairs (male + female)
        males = [c for c in available_for_breeding if c['gender'] == 'male']
        females = [c for c in available_for_breeding if c['gender'] == 'female']
        
        for male in males:
            for female in females:
                # Calculate compatibility score
                power_score = (male['power'] + female['power']) / 2
                var_score = (male['variance'] + female['variance']) / 2
                adj_score = (male['adjodds'] + female['adjodds']) / 2
                
                # Element bonus (same element = bonus)
                element_bonus = 10 if male['element'] == female['element'] else 0
                
                # Family bonus (different families preferred)
                family_bonus = 5 if male['fno'] != female['fno'] else -5
                
                total_score = (power_score * 0.4 + var_score * 0.3 + adj_score * 0.3 + 
                              element_bonus + family_bonus)
                
                breeding_pairs.append({
                    'male': male,
                    'female': female,
                    'score': total_score,
                    'expected_power': power_score,
                    'expected_var': var_score,
                    'expected_adj': adj_score,
                    'element_match': male['element'] == female['element']
                })
        
        # Sort by score
        breeding_pairs.sort(key=lambda x: x['score'], reverse=True)
        
        # Display top 5 pairs
        if breeding_pairs:
            st.success(f"Found {len(breeding_pairs)} possible breeding pairs!")
            
            for idx, pair in enumerate(breeding_pairs[:5], 1):
                with st.expander(f"🥇 Pair #{idx} - Score: {pair['score']:.1f}/100", expanded=(idx==1)):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.markdown(f"**♂️ Male: {pair['male']['name']}** (#{pair['male']['hid']})")
                        st.caption(f"{pair['male']['element'].title()} • {pair['male']['type'].title()} • F{pair['male']['fno']}")
                        st.caption(f"PWR: {pair['male']['power']:.1f}% | VAR: {pair['male']['variance']:.1f}% | ADJ: {pair['male']['adjodds']:.1f}%")
                        if pair['male']['in_stud']:
                            st.success(f"✅ In Stud - ${pair['male']['price_usd']:.2f}")
                        else:
                            st.warning("❌ Not in stud")
                    
                    with col2:
                        st.markdown(f"**♀️ Female: {pair['female']['name']}** (#{pair['female']['hid']})")
                        st.caption(f"{pair['female']['element'].title()} • {pair['female']['type'].title()} • F{pair['female']['fno']}")
                        st.caption(f"PWR: {pair['female']['power']:.1f}% | VAR: {pair['female']['variance']:.1f}% | ADJ: {pair['female']['adjodds']:.1f}%")
                        if pair['female']['in_stud']:
                            st.success(f"✅ In Stud - ${pair['female']['price_usd']:.2f}")
                        else:
                            st.warning("❌ Not in stud")
                    
                    with col3:
                        st.metric("Expected PWR", f"{pair['expected_power']:.1f}%")
                        st.metric("Expected VAR", f"{pair['expected_var']:.1f}%")
                        st.metric("Expected ADJ", f"{pair['expected_adj']:.1f}%")
                    
                    if pair['element_match']:
                        st.info("🎯 Same element - Higher chance of matching element offspring")
        else:
            st.warning("No breeding pairs found. You may need both male and female cores.")
        
        st.divider()
        
        # ==================
        # OPTION B: ADVANCED BREEDING ANALYTICS
        # ==================
        st.subheader("📊 Advanced Breeding Analytics")
        
        # Breeding availability
        with st.expander("🔍 Breeding Availability", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                in_stud_count = sum(1 for c in available_for_breeding if c['in_stud'])
                st.metric("Cores in Stud", f"{in_stud_count}/{len(available_for_breeding)}")
            
            with col2:
                males_count = len(males)
                st.metric("Males Available", males_count)
            
            with col3:
                females_count = len(females)
                st.metric("Females Available", females_count)
            
            st.markdown("**Cores Available for Breeding:**")
            
            for core in available_for_breeding[:10]:  # Show first 10
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.write(f"**{core['name']}** (#{core['hid']})")
                with col2:
                    st.write(f"{core['gender'].title()} • {core['element'].title()}")
                with col3:
                    st.write(f"Remaining: {core['remaining']}")
                with col4:
                    if core['in_stud']:
                        st.success(f"${core['price_usd']:.2f}")
                    else:
                        st.warning("Not listed")
            
            if len(available_for_breeding) > 10:
                st.caption(f"... and {len(available_for_breeding) - 10} more")
        
        # Filter by breeding goals
        with st.expander("🎯 Filter by Breeding Goals", expanded=False):
            st.markdown("**What are you trying to achieve?**")
            
            goal_col1, goal_col2 = st.columns(2)
            
            with goal_col1:
                target_element = st.selectbox(
                    "Target Element",
                    ["Any", "water", "fire", "earth", "air"]
                )
            
            with goal_col2:
                min_power = st.slider(
                    "Minimum Expected Power",
                    min_value=0,
                    max_value=100,
                    value=70
                )
            
            # Filter pairs
            filtered_pairs = breeding_pairs
            
            if target_element != "Any":
                filtered_pairs = [p for p in filtered_pairs if p['element_match'] and p['male']['element'] == target_element]
            
            filtered_pairs = [p for p in filtered_pairs if p['expected_power'] >= min_power]
            
            st.info(f"Found {len(filtered_pairs)} pairs matching your criteria")
            
            if filtered_pairs:
                for idx, pair in enumerate(filtered_pairs[:3], 1):
                    st.write(f"{idx}. {pair['male']['name']} × {pair['female']['name']} - Expected Power: {pair['expected_power']:.1f}%")
        
        st.divider()
        
        # ==================
        # OPTION C: FULL BREEDING SUITE
        # ==================
        st.subheader("💰 ROI & Profitability Analysis")
        
        with st.expander("💵 Breeding Cost Analysis", expanded=False):
            st.markdown("**Estimated breeding costs for top pairs:**")
            
            for idx, pair in enumerate(breeding_pairs[:5], 1):
                male_cost = pair['male']['price_usd'] if pair['male']['in_stud'] else 0
                female_cost = pair['female']['price_usd'] if pair['female']['in_stud'] else 0
                total_cost = male_cost + female_cost
                
                # Rough offspring value estimate (based on expected power)
                estimated_value = pair['expected_power'] * 10  # Simplified formula
                
                profit = estimated_value - total_cost
                roi = (profit / total_cost * 100) if total_cost > 0 else 0
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.write(f"**Pair #{idx}**")
                    st.caption(f"{pair['male']['name'][:15]} × {pair['female']['name'][:15]}")
                
                with col2:
                    st.metric("Breeding Cost", f"${total_cost:.2f}")
                
                with col3:
                    st.metric("Est. Offspring Value", f"${estimated_value:.2f}")
                
                with col4:
                    st.metric("Potential Profit", f"${profit:.2f}", delta=f"{roi:.0f}% ROI")
        
        with st.expander("📈 Breeding Strategy Planner", expanded=False):
            st.markdown("**Plan your breeding strategy:**")
            
            strategy = st.radio(
                "Choose your strategy:",
                [
                    "Maximize Power (breed strongest cores)",
                    "Element Focus (produce specific element)",
                    "Family Diversification (avoid inbreeding)",
                    "Budget Breeding (use free/cheap studs)"
                ]
            )
            
            if strategy == "Maximize Power (breed strongest cores)":
                st.info("Recommended: Top 3 pairs have 85%+ expected power")
                power_pairs = [p for p in breeding_pairs if p['expected_power'] >= 85][:3]
                for pair in power_pairs:
                    st.write(f"• {pair['male']['name']} × {pair['female']['name']} → {pair['expected_power']:.1f}% power")
            
            elif strategy == "Element Focus (produce specific element)":
                element_choice = st.selectbox("Target element:", ["water", "fire", "earth", "air"])
                element_pairs = [p for p in breeding_pairs if p['element_match'] and p['male']['element'] == element_choice][:3]
                st.info(f"Found {len(element_pairs)} pairs for {element_choice.title()}")
                for pair in element_pairs:
                    st.write(f"• {pair['male']['name']} × {pair['female']['name']} → {pair['expected_power']:.1f}% power")
            
            elif strategy == "Family Diversification (avoid inbreeding)":
                diverse_pairs = [p for p in breeding_pairs if p['male']['fno'] != p['female']['fno']][:3]
                st.info(f"Found {len(diverse_pairs)} pairs with different families")
                for pair in diverse_pairs:
                    st.write(f"• F{pair['male']['fno']} × F{pair['female']['fno']} → {pair['expected_power']:.1f}% power")
            
            else:  # Budget breeding
                free_pairs = [p for p in breeding_pairs if p['male']['price_usd'] == 0 or p['female']['price_usd'] == 0][:3]
                st.info(f"Found {len(free_pairs)} pairs with at least one free stud")
                for pair in free_pairs:
                    cost = pair['male']['price_usd'] + pair['female']['price_usd']
                    st.write(f"• {pair['male']['name']} × {pair['female']['name']} → ${cost:.2f} → {pair['expected_power']:.1f}% power")

else:
    st.info("👆 Enter a vault address or name above to begin")
    
    with st.expander("💡 Example Vaults to Try"):
        st.markdown("""
        Try searching for:
        - **wisdom-weaver** (example vault name)
        - **0xaf1320faa9a484a4702ec16ffec18260cc42c3c2** (example address)
        
        Or enter your own vault!
        """)
