import streamlit as st
import requests
from typing import Optional, Dict, List
from collections import defaultdict

st.set_page_config(page_title="Breeding Analyzer", page_icon="🧬", layout="wide")

API_BASE_URL = "https://api.dnaracing.run/fbike"

# Distance categories
SPRINT_RANGE = list(range(9, 14))      # 900m-1300m (CB 9-13)
MID_RANGE = list(range(14, 19))        # 1400m-1800m (CB 14-18)
MARATHON_RANGE = list(range(19, 24))   # 1900m-2300m (CB 19-23)

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


def categorize_core_by_distance(stats_data: dict, mode: str) -> set:
    """Determine which distance categories a core excels in"""
    categories = set()
    mode_field = f"hstats_{mode}"
    mode_stats = stats_data.get(mode_field, {})
    
    for cb_str, cb_data in mode_stats.items():
        if cb_str == 'career':
            continue
            
        try:
            cb = int(cb_str)
            win_p = cb_data.get('win_p', 0)
            win_rate = win_p * 100
            races = cb_data.get('races_n', 0)
            
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


st.title("🧬 Breeding Analyzer")
st.markdown("Analyze your vault's cores and discover optimal breeding pairs")

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
    search_btn = st.button("🔍 Analyze Vault", type="primary", use_container_width=True)

if search_btn and vault_input:
    
    vault_address = vault_input.lower() if vault_input.startswith("0x") else vault_input
    
    with st.spinner("Loading vault data..."):
        cores = fetch_api("/vault/bikes_inf", {"vault": vault_address})
    
    if not cores or len(cores) == 0:
        st.error("❌ No cores found for this vault")
        st.stop()
    
    regular_cores = [c for c in cores if not c.get('is_trainer', False)]
    
    st.success(f"✓ Found {len(regular_cores)} breedable cores in vault")
    st.session_state.vault_cores = regular_cores
    st.divider()

# Display if vault is loaded
if 'vault_cores' in st.session_state:
    cores = st.session_state.vault_cores
    
    st.info(f"📊 Analyzing {len(cores)} cores for breeding opportunities...")
    
    # Fetch all needed data
    with st.spinner("Loading breeding and performance data..."):
        hids = [c['hid'] for c in cores]
        
        breeding_data = fetch_api("/cores/splicing_info_bulk", {"hids": hids}, timeout=120)
        power_data = fetch_api("/cores/power_bulk", {"hids": hids}, timeout=120)
        stats_data = fetch_api("/cores/racing_stats_bulk", {"hids": hids}, timeout=180)
    
    if not breeding_data:
        st.error("Failed to load breeding data")
        st.stop()
    
    breeding_lookup = {b['splice_core']['hid']: b for b in breeding_data if b.get('splice_core')}
    power_lookup = {p['hid']: p for p in power_data} if power_data else {}
    stats_lookup = {s['hid']: s for s in stats_data} if stats_data else {}
    
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
            'father_hid': None  # Will be extracted from parents field
        }
        
        # Extract father HID from parents field if it exists
        parents = breeding_info.get('parents')
        if parents:
            # Parents structure might be [male_hid, female_hid] or {"male": hid, "female": hid}
            # We need to identify which is the father (stud/male parent)
            if isinstance(parents, list) and len(parents) >= 2:
                # Assuming parents[0] is male/father
                core_info['father_hid'] = parents[0]
            elif isinstance(parents, dict):
                core_info['father_hid'] = parents.get('male') or parents.get('father')
        
        available_cores.append(core_info)
    
    # Show categorization debug
    with st.expander("🔍 Distance Categorization Analysis", expanded=True):
        st.write(f"**Total cores analyzed:** {categorization_debug['total_checked']}")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🏃 Sprint", categorization_debug['sprint'], help=">28% win rate at 900-1300m with 20+ races")
        with col2:
            st.metric("🏃‍♂️ Mid-Distance", categorization_debug['mid'], help=">28% win rate at 1400-1800m with 20+ races")
        with col3:
            st.metric("🏃‍♀️ Marathon", categorization_debug['marathon'], help=">28% win rate at 1900-2300m with 20+ races")
        with col4:
            st.metric("❓ Unproven", categorization_debug['unproven'], help="Don't meet criteria")
        
        if categorization_debug['unproven'] > categorization_debug['total_checked'] * 0.8:
            st.warning("⚠️ Most cores are unproven. This could mean: (1) Not enough races, (2) Win rates below 28%, or (3) Racing stats didn't load properly.")
    
    males = [c for c in available_cores if c['gender'] == 'male']
    females = [c for c in available_cores if c['gender'] == 'female']
    
    st.divider()
    
    # Helper function to calculate breeding pairs with half-sibling tracking
    excluded_half_siblings = {'sprint': 0, 'mid': 0, 'marathon': 0, 'gamble': 0}
    
    def calculate_breeding_pairs(males, females, category_filter=None, gamble=False):
        pairs = []
        category_key = category_filter if category_filter else 'gamble'
        
        for male in males:
            for female in females:
                # BREEDING RESTRICTION: Skip half-siblings (same father/stud)
                male_father = male.get('father_hid')
                female_father = female.get('father_hid')
                
                # If both have fathers and they're the same, they're half-siblings - SKIP
                if male_father and female_father and male_father == female_father:
                    excluded_half_siblings[category_key] += 1
                    continue
                
                # Category filtering
                if not gamble and category_filter:
                    if category_filter not in male['categories'] or category_filter not in female['categories']:
                        continue
                
                power_score = (male['power'] + female['power']) / 2
                var_score = (male['variance'] + female['variance']) / 2
                adj_score = (male['adjodds'] + female['adjodds']) / 2
                
                element_bonus = 10 if male['element'] == female['element'] else 0
                
                if gamble:
                    total_score = (power_score * 0.5 + var_score * 0.3 + adj_score * 0.2 + element_bonus)
                else:
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
            
            # Show exclusion info
            category_key = cat_name.lower() if cat_name != "Gamble" else "gamble"
            excluded_count = excluded_half_siblings.get(category_key, 0)
            if excluded_count > 0:
                st.caption(f"ℹ️ Excluded {excluded_count} pairs (half-siblings - same father)")
            
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
    st.info("👆 Enter a vault address or name above to analyze breeding opportunities")
    
    with st.expander("💡 What This Tool Does"):
        st.markdown("""
        **Breeding Analyzer** helps you find optimal breeding pairs from your vault.
        
        **Four Categories:**
        - **🏃 Sprint:** Cores that excel at 900-1300m
        - **🏃‍♂️ Mid-Distance:** Cores that excel at 1400-1800m  
        - **🏃‍♀️ Marathon:** Cores that excel at 1900-2300m
        - **🎲 Gamble:** Pure power breeding (ignores distance)
        
        **How It Works:**
        1. Analyzes all cores in your vault
        2. Categorizes by racing performance (>28% win rate, 20+ races)
        3. Finds best male + female combinations
        4. Scores based on power, compatibility, and distance match
        5. Shows top 10 pairs per category
        
        **Great For:**
        - Planning breeding strategy
        - Finding complementary pairs
        - Maximizing offspring potential
        - Identifying which cores to put in stud
        """)
