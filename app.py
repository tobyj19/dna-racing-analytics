import streamlit as st

# DARK THEME CONFIGURATION
st.set_page_config(
    page_title="DNA Racing Analytics",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for improved design
st.markdown("""
<style>
    /* Hide sidebar on home page */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* Main container styling */
    .main {
        background-color: #0e1117;
    }
    
    /* Search bar styling */
    .search-container {
        max-width: 800px;
        margin: 0 auto 60px auto;
        padding: 20px;
    }
    
    /* Card styling */
    .tool-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 15px;
        padding: 30px 20px;
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
        height: 100%;
        min-height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .tool-card:hover {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
        border-color: rgba(102, 126, 234, 0.5);
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .tool-icon {
        font-size: 48px;
        margin-bottom: 15px;
    }
    
    .tool-title {
        font-size: 22px;
        font-weight: 600;
        color: #fafafa;
        margin-bottom: 10px;
    }
    
    .tool-description {
        font-size: 14px;
        color: rgba(250, 250, 250, 0.7);
        line-height: 1.5;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 60px 20px;
        margin-bottom: 40px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }
    
    .main-title {
        font-size: 56px;
        font-weight: 700;
        color: white;
        margin: 0;
        letter-spacing: -1px;
    }
    
    .main-subtitle {
        font-size: 18px;
        color: rgba(255, 255, 255, 0.9);
        margin-top: 15px;
        font-weight: 300;
    }
    
    /* Section headers */
    .section-header {
        font-size: 28px;
        font-weight: 600;
        color: #fafafa;
        margin: 40px 0 30px 0;
        text-align: center;
    }
    
    /* Coming soon badge */
    .coming-soon {
        background: rgba(102, 126, 234, 0.2);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 15px;
        padding: 30px 20px;
        text-align: center;
        min-height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .coming-soon-text {
        font-size: 20px;
        font-weight: 600;
        color: rgba(250, 250, 250, 0.5);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 40px 20px;
        margin-top: 60px;
        color: rgba(250, 250, 250, 0.5);
        border-top: 1px solid rgba(102, 126, 234, 0.1);
    }
    
    /* Hide default button styling but keep clickable */
    .stButton {
        margin-top: 10px;
    }
    
    .stButton button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
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

# Search Bar
st.markdown('<div class="search-container">', unsafe_allow_html=True)
search_query = st.text_input(
    "",
    placeholder="🔍 Search cores by name or HID...",
    label_visibility="collapsed",
    key="global_search"
)
st.caption("Search by name or HID number")
st.markdown('</div>', unsafe_allow_html=True)

if search_query:
    st.info(f"Searching for: {search_query}")
    st.markdown("*Search functionality coming soon - for now, use Core Analytics tool below*")
    st.divider()

# Tools Section
st.markdown('<p class="section-header">Tools & Features</p>', unsafe_allow_html=True)

# Row 1: Core Analysis Tools
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.markdown("""
    <div class="tool-card">
        <div class="tool-icon">📊</div>
        <div class="tool-title">Core Analytics</div>
        <div class="tool-description">Search and analyze individual core performance, stats, and race history</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Launch Tool", key="btn_analytics", use_container_width=True):
        st.switch_page("pages/1_Core_Analytics.py")

with col2:
    st.markdown("""
    <div class="tool-card">
        <div class="tool-icon">⚖️</div>
        <div class="tool-title">Core Comparison</div>
        <div class="tool-description">Compare multiple cores side-by-side across all metrics</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Launch Tool", key="btn_comparison", use_container_width=True):
        st.switch_page("pages/2_Core_Comparison.py")

with col3:
    st.markdown("""
    <div class="tool-card">
        <div class="tool-icon">🏁</div>
        <div class="tool-title">Race Finder</div>
        <div class="tool-description">Find upcoming races and optimal racing opportunities</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Launch Tool", key="btn_races", use_container_width=True):
        st.switch_page("pages/3_Race_Finder.py")

st.markdown("<br>", unsafe_allow_html=True)

# Row 2: Vault & Portfolio Tools
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.markdown("""
    <div class="tool-card">
        <div class="tool-icon">💼</div>
        <div class="tool-title">Vault Portfolio</div>
        <div class="tool-description">Analyze entire vaults with filters, stats, and performance tracking</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Launch Tool", key="btn_vault", use_container_width=True):
        st.switch_page("pages/4_Vault_Portfolio.py")

with col2:
    st.markdown("""
    <div class="tool-card">
        <div class="tool-icon">🧬</div>
        <div class="tool-title">Breeding Analyzer</div>
        <div class="tool-description">Find optimal breeding pairs with distance categorization</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Launch Tool", key="btn_breeding", use_container_width=True):
        st.switch_page("pages/5_Breeding_Analyzer.py")

with col3:
    st.markdown("""
    <div class="tool-card">
        <div class="tool-icon">⚡</div>
        <div class="tool-title">Speed Rankings</div>
        <div class="tool-description">Top 30 fastest cores per distance vs global averages</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Launch Tool", key="btn_speed", use_container_width=True):
        st.switch_page("pages/6_Speed_Rankings.py")

st.markdown("<br>", unsafe_allow_html=True)

# Row 3: Database & Future Tools
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.markdown("""
    <div class="tool-card">
        <div class="tool-icon">🗄️</div>
        <div class="tool-title">Power Database</div>
        <div class="tool-description">Search and filter power stats across all cores</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Launch Tool", key="btn_database", use_container_width=True):
        st.switch_page("pages/7_Power_Database.py")

with col2:
    st.markdown("""
    <div class="coming-soon">
        <div class="coming-soon-text">Coming Soon</div>
        <div class="tool-description" style="margin-top: 10px;">More analytics tools in development</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="coming-soon">
        <div class="coming-soon-text">Coming Soon</div>
        <div class="tool-description" style="margin-top: 10px;">More analytics tools in development</div>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer">
    <p style="font-size: 16px; margin-bottom: 10px;">DNA Racing Analytics Dashboard v2.0</p>
    <p style="font-size: 12px; opacity: 0.6;">Select a tool above to get started</p>
</div>
""", unsafe_allow_html=True)

# Info section
with st.expander("ℹ️ About DNA Racing Analytics"):
    st.markdown("""
    **DNA Racing Analytics** is a comprehensive suite of tools for analyzing cores, performance, and breeding strategies.
    
    **Features:**
    - **Core Analytics:** Deep dive into individual core performance
    - **Vault Management:** Analyze entire vault collections
    - **Breeding Tools:** Find optimal breeding pairs with genetic compatibility
    - **Speed Rankings:** Compare against global performance benchmarks
    - **Power Database:** Search across all cores for specific stats
    
    **Getting Started:**
    Use the search bar above or click any tool to begin your analysis!
    """)
