import streamlit as st

# DARK THEME CONFIGURATION
st.set_page_config(
    page_title="DNA Racing Analytics",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dark theme
st.markdown("""
<style>
    /* Dark theme colors */
    :root {
        --background-color: #0e1117;
        --secondary-background-color: #1e2130;
        --text-color: #fafafa;
        --accent-color: #667eea;
    }
    
    /* Hide sidebar by default on home page */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* Navigation button styling */
    .nav-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 10px;
        padding: 30px;
        margin: 10px;
        color: white;
        font-size: 20px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: center;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .nav-button:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
    }
    
    .nav-button-description {
        font-size: 14px;
        font-weight: normal;
        opacity: 0.9;
        margin-top: 10px;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 40px 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin-bottom: 40px;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .main-title {
        font-size: 48px;
        font-weight: bold;
        color: white;
        margin: 0;
    }
    
    .main-subtitle {
        font-size: 18px;
        color: rgba(255, 255, 255, 0.9);
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1 class="main-title">DNA Racing Analytics</h1>
    <p class="main-subtitle">Comprehensive tools for analyzing cores, breeding, and performance</p>
</div>
""", unsafe_allow_html=True)

# Navigation Grid
st.markdown("## Tools & Features")

col1, col2, col3 = st.columns(3)

# Row 1: Core Analysis Tools
with col1:
    if st.button("Core Analytics", use_container_width=True, type="primary"):
        st.switch_page("pages/1_Core_Analytics.py")
    st.caption("Search and analyze individual core performance, stats, and race history")

with col2:
    if st.button("Core Comparison", use_container_width=True, type="primary"):
        st.switch_page("pages/2_Core_Comparison.py")
    st.caption("Compare multiple cores side-by-side across all metrics")

with col3:
    if st.button("Race Finder", use_container_width=True, type="primary"):
        st.switch_page("pages/3_Race_Finder.py")
    st.caption("Find upcoming races and optimal racing opportunities")

st.divider()

# Row 2: Vault & Portfolio Tools
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Vault Portfolio", use_container_width=True, type="primary"):
        st.switch_page("pages/4_Vault_Portfolio.py")
    st.caption("Analyze entire vaults with filters, stats, and performance tracking")

with col2:
    if st.button("Breeding Analyzer", use_container_width=True, type="primary"):
        st.switch_page("pages/5_Breeding_Analyzer.py")
    st.caption("Find optimal breeding pairs with distance categorization")

with col3:
    if st.button("Speed Rankings", use_container_width=True, type="primary"):
        st.switch_page("pages/6_Speed_Rankings.py")
    st.caption("Top 30 fastest cores per distance vs global averages")

st.divider()

# Row 3: Database Tools
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Power Database", use_container_width=True, type="primary"):
        st.switch_page("pages/7_Power_Database.py")
    st.caption("Search and filter power stats across all cores")

with col2:
    st.markdown("### Coming Soon")
    st.caption("More analytics tools in development")

with col3:
    st.markdown("### Coming Soon")
    st.caption("More analytics tools in development")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; opacity: 0.7; padding: 20px;">
    <p>DNA Racing Analytics Dashboard v1.0</p>
    <p style="font-size: 12px;">Select a tool above to get started</p>
</div>
""", unsafe_allow_html=True)

# Info section
with st.expander("About DNA Racing Analytics"):
    st.markdown("""
    **DNA Racing Analytics** is a comprehensive suite of tools for analyzing cores, performance, and breeding strategies.
    
    **Features:**
    - **Core Analytics:** Deep dive into individual core performance
    - **Vault Management:** Analyze entire vault collections
    - **Breeding Tools:** Find optimal breeding pairs with genetic compatibility
    - **Speed Rankings:** Compare against global performance benchmarks
    - **Power Database:** Search across all cores for specific stats
    
    **Getting Started:**
    Click any tool above to begin your analysis!
    """)
