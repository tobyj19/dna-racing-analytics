#!/usr/bin/env python3
"""
DNA Racing Core Analytics - Multi-Page Streamlit App

Main entry point for the DNA Racing analytics application.

Installation:
    pip install streamlit requests pandas plotly

Usage:
    streamlit run app.py

Structure:
    app.py (this file)
    pages/
        1_🔍_Core_Search.py
        2_📊_Performance_Analysis.py
        3_🏁_Race_History.py
        4_🧬_Breeding_Lineage.py
        5_⚖️_Core_Comparison.py
"""

import streamlit as st
import requests
from typing import Dict, List, Optional, Tuple

# Page config
st.set_page_config(
    page_title="DNA Racing Analytics",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "DNA Racing Core Analytics - Comprehensive performance analysis tool"
    }
)

# Global constants
GLOBAL_AVERAGES = {
    9: 50.3, 10: 56.9, 11: 63.8, 12: 70.5, 13: 76.8, 14: 82.8,
    15: 88.8, 16: 94.6, 17: 100.9, 18: 106.8, 19: 112.7, 20: 118.9,
    21: 124.4, 22: 130.7, 23: 137.6
}

API_BASE_URL = "https://api.dnaracing.run/fbike"

# Shared utility functions
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


# Store in session state for sharing across pages
if 'GLOBAL_AVERAGES' not in st.session_state:
    st.session_state.GLOBAL_AVERAGES = GLOBAL_AVERAGES

if 'fetch_api' not in st.session_state:
    st.session_state.fetch_api = fetch_api

if 'fetch_core_data' not in st.session_state:
    st.session_state.fetch_core_data = fetch_core_data


# Home page
st.title("🏁 DNA Racing Core Analytics")
st.markdown("### Multi-Page Analytics Platform")

st.markdown("""
Welcome to the DNA Racing Core Analytics platform! Use the sidebar to navigate between different analysis tools.

#### 📚 Available Pages:

**1. 🔍 Core Search & Overview**
- Search for cores by ID
- View basic information and power statistics
- See quick performance summary

**2. 📊 Performance Analysis**
- Best distance recommendations (2 analysis methods)
- Weighted performance scoring
- Global comparison rankings

**3. 🏁 Race History & Charts**
- Position distribution by distance
- Finish time analysis with global averages
- Interactive race data visualizations

**4. 🧬 Breeding & Lineage**
- View offspring produced by the core
- Check breeding availability and pricing
- See parent/grandparent lineage

**5. ⚖️ Core Comparison**
- Compare up to 3 cores side-by-side
- Performance metrics comparison
- Find the best core for your needs

---

### 🚀 Getting Started

1. Click **🔍 Core Search** in the sidebar
2. Enter a Core ID (e.g., 192)
3. Explore the data across different pages

### 📊 Features

- ✅ Real-time data from DNA Racing API
- ✅ Interactive charts with Plotly
- ✅ Global performance benchmarks
- ✅ 20+ races minimum for statistical accuracy
- ✅ Multi-core comparison tools

### ℹ️ Tips

- Use the sidebar to navigate between pages
- Data is cached during your session
- Minimum 20 races required for distance analysis
- Global averages help identify competitive advantages
""")

st.divider()

# Quick stats
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Distances",
        "15",
        help="From 900m to 2300m"
    )

with col2:
    st.metric(
        "Analysis Methods",
        "2",
        help="Weighted Score + Global Comparison"
    )

with col3:
    st.metric(
        "Racing Modes",
        "3",
        help="Bike, Car, Horse"
    )

with col4:
    st.metric(
        "Min Races",
        "20",
        help="For statistical accuracy"
    )

st.divider()

st.info("👈 **Get started by selecting a page from the sidebar!**")
