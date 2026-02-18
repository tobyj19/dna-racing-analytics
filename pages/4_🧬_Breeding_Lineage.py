import streamlit as st

st.set_page_config(page_title="Breeding & Lineage", page_icon="🧬", layout="wide")

st.title("🧬 Breeding & Lineage")
st.markdown("Explore the core's breeding history, offspring, and family tree")

# Check if core data exists
if 'mini' not in st.session_state:
    st.warning("⚠️ No core data loaded. Please search for a core in the **Core Search** page first.")
    st.stop()

mini = st.session_state.mini
fetch_api = st.session_state.fetch_api

st.header(f"Lineage for Core #{mini['hid']} - {mini.get('name', 'Unnamed')}")

# Fetch splicing info
with st.spinner("Loading breeding information..."):
    splicing_info = fetch_api("/cores/splicing_info", {"hid": mini['hid']})

if not splicing_info:
    st.error("Failed to load breeding information")
    st.stop()

splice_core = splicing_info.get('splice_core', {})

st.divider()

# Core Type and Lineage
col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Core Information")
    
    core_type = splice_core.get('type', mini.get('type', 'Unknown'))
    st.metric("Type", core_type.title())
    
    # Parents
    parents = splicing_info.get('parents')
    if parents and any(parents):
        st.markdown("**Parents:**")
        for parent_id in parents:
            if parent_id:
                st.markdown(f"- Core #{parent_id}")
    else:
        st.info("🌟 Genesis Core (no parents)")
    
    # Grandparents
    grandparents = splicing_info.get('grand_parents')
    if grandparents and any(grandparents):
        st.markdown("**Grandparents:**")
        for gp_id in grandparents:
            if gp_id:
                st.markdown(f"- Core #{gp_id}")

with col2:
    st.subheader("🏆 Breeding Status")
    
    in_stud = splice_core.get('in_stud', False)
    
    if in_stud:
        st.success("✅ Available for Breeding")
        
        price_usd = splice_core.get('price_usd', 0)
        if price_usd > 0:
            st.metric("Breeding Fee", f"${price_usd:.2f}")
        else:
            st.info("Free breeding")
    else:
        st.warning("❌ Not Currently Available for Breeding")

st.divider()

# Breeding Statistics
st.subheader("📊 Breeding Statistics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    life_splices = splice_core.get('life_splices_n', 0)
    st.metric("Total Offspring", life_splices)

with col2:
    max_life = splice_core.get('mxlife_splices_n', 0)
    remaining = max_life - life_splices if max_life > 0 else "Unlimited"
    st.metric("Remaining Lifetime", remaining)

with col3:
    cycle_splices = splice_core.get('cycle_splices_n', 0)
    st.metric("This Cycle", cycle_splices)

with col4:
    max_cycle = splice_core.get('mxcycle_splices_n', 0)
    cycle_remaining = max_cycle - cycle_splices if max_cycle > 0 else 0
    st.metric("Cycle Remaining", cycle_remaining)

st.divider()

# Cycle Information
st.subheader("🔄 Breeding Cycle")

col1, col2 = st.columns(2)

with col1:
    cycle_dur = splice_core.get('cycle_dur', [])
    if cycle_dur and len(cycle_dur) == 2:
        st.metric("Cycle Duration", f"{cycle_dur[0]} {cycle_dur[1]}")
    else:
        st.info("Cycle duration not available")

with col2:
    cycle_resets = splice_core.get('cycle_resets')
    if cycle_resets:
        from datetime import datetime
        try:
            reset_date = datetime.fromisoformat(cycle_resets.replace('Z', '+00:00'))
            st.metric("Next Cycle Reset", reset_date.strftime("%Y-%m-%d %H:%M"))
        except:
            st.text(cycle_resets)

st.divider()

# Offspring List
st.subheader("👶 Offspring Produced")

life_splices_list = splice_core.get('life_splices', [])

if life_splices_list:
    st.markdown(f"**This core has produced {len(life_splices_list)} offspring:**")
    
    # Display in a nice grid
    cols_per_row = 8
    rows = [life_splices_list[i:i+cols_per_row] for i in range(0, len(life_splices_list), cols_per_row)]
    
    for row in rows:
        cols = st.columns(cols_per_row)
        for idx, offspring_id in enumerate(row):
            with cols[idx]:
                st.button(f"#{offspring_id}", key=f"offspring_{offspring_id}", use_container_width=True)
    
    st.caption("💡 Click on an offspring ID to view its details (feature coming soon)")
    
    # Download offspring list
    offspring_text = "\n".join([str(id) for id in life_splices_list])
    st.download_button(
        label="📥 Download Offspring List",
        data=offspring_text,
        file_name=f"core_{mini['hid']}_offspring.txt",
        mime="text/plain"
    )
else:
    st.info("🌱 This core has not yet produced any offspring")

st.divider()

# Additional breeding info
if 'off_chain_data' in splice_core:
    with st.expander("🔧 Additional Breeding Data"):
        st.json(splice_core['off_chain_data'])

st.info("🧬 Breeding availability and pricing can change. Check back regularly for updates!")
