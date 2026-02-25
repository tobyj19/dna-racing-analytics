import streamlit as st
import requests
from collections import defaultdict

st.set_page_config(page_title="Star Value Finder", page_icon="⭐", layout="wide")

st.title("⭐ Star Value Finder")
st.markdown("Find example races with different star values to understand the star system")

API_BASE_URL = "https://api.dnaracing.run/fbike"

# Input
core_id = st.number_input("Enter Core ID to analyze", min_value=1, value=588, step=1)
mode = st.selectbox("Mode", ["bike", "car", "horse"])

if st.button("🔍 Analyze Star Values", type="primary"):
    
    with st.spinner(f"Fetching race history for core #{core_id}..."):
        try:
            response = requests.post(
                f"{API_BASE_URL}/i/hraces",
                json={"hid": core_id, "rvmode": mode, "limit": 500},  # Get lots of races
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            data = response.json()
            
            if data.get('status') != 'success':
                st.error("Failed to fetch race data")
                st.stop()
            
            races = data.get('result', [])
            
            if not races:
                st.warning("No races found for this core")
                st.stop()
            
            st.success(f"✓ Loaded {len(races)} races")
            
            # Group races by star value
            star_groups = defaultdict(list)
            
            for race in races:
                star_value = race.get('star', 'unknown')
                star_groups[star_value].append(race)
            
            # Display summary
            st.subheader("📊 Star Value Distribution")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            for idx, (star_val, race_list) in enumerate(sorted(star_groups.items())):
                with [col1, col2, col3, col4, col5][idx % 5]:
                    st.metric(f"Star {star_val}", len(race_list))
            
            st.divider()
            
            # Show example race for each star value
            st.subheader("🎯 Example Races for Each Star Value")
            
            for star_val in sorted(star_groups.keys()):
                with st.expander(f"⭐ Star Value: {star_val} ({len(star_groups[star_val])} races)", expanded=True):
                    
                    # Show first race as example
                    example_race = star_groups[star_val][0]
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("**Race Details:**")
                        st.write(f"**Race ID:** {example_race.get('rid', 'N/A')}")
                        st.write(f"**Race Name:** {example_race.get('race_name', 'N/A')}")
                        st.write(f"**Distance:** {example_race.get('cb', 'N/A')*100}m (CB {example_race.get('cb', 'N/A')})")
                        st.write(f"**Class:** {example_race.get('class', 'N/A')}")
                    
                    with col2:
                        st.markdown("**Performance:**")
                        st.write(f"**Position:** {example_race.get('pos', 'N/A')}/{example_race.get('rgate', 'N/A')}")
                        st.write(f"**Time:** {example_race.get('time', 'N/A')}s")
                        st.write(f"**Gate:** {example_race.get('gate', 'N/A')}")
                        st.write(f"**Star:** ⭐ **{example_race.get('star', 'N/A')}**")
                    
                    with col3:
                        st.markdown("**Prize Info:**")
                        st.write(f"**Prize USD:** ${example_race.get('prize_usd', 0):.2f}")
                        st.write(f"**Pay Token:** {example_race.get('paytoken', 'N/A')}")
                        st.write(f"**Fee:** {example_race.get('fee', 0)}")
                    
                    # Show full JSON
                    with st.expander("📄 View Full Race JSON"):
                        st.json(example_race)
            
            st.divider()
            
            # Show all unique star values found
            st.subheader("✨ Summary")
            st.write(f"**Total races analyzed:** {len(races)}")
            st.write(f"**Unique star values found:** {sorted(star_groups.keys())}")
            
            # Percentage breakdown
            st.markdown("**Star Value Breakdown:**")
            for star_val in sorted(star_groups.keys()):
                count = len(star_groups[star_val])
                percentage = (count / len(races)) * 100
                st.write(f"- Star {star_val}: {count} races ({percentage:.1f}%)")
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.exception(e)

else:
    st.info("👆 Enter a core ID and click 'Analyze Star Values' to find example races")
    
    with st.expander("💡 What This Tool Does"):
        st.markdown("""
        This tool fetches race history for a core and groups races by their `star` value.
        
        **It will show:**
        - How many races have each star value (0, 1, 3, 5, etc.)
        - Example race data for each star value
        - Distribution breakdown
        
        **Use this to determine:**
        - What star values exist (0, 1, 3, 5?)
        - What each star value means
        - How to calculate ⭐% for blue/gold stars
        """)
