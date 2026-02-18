# 🏁 DNA Racing Core Analytics - Multi-Page Streamlit App

Comprehensive performance analysis tool for DNA Racing cores with 5 dedicated pages.

## 📁 Project Structure

```
streamlit-multipage/
├── app.py                          # Main entry point & home page
├── requirements.txt                # Python dependencies
├── README.md                       # This file
└── pages/
    ├── 1_🔍_Core_Search.py        # Core search & basic info
    ├── 2_📊_Performance_Analysis.py # Best distance analysis
    ├── 3_🏁_Race_History.py        # Charts & visualizations
    ├── 4_🧬_Breeding_Lineage.py    # Breeding info & offspring
    └── 5_⚖️_Core_Comparison.py    # Compare multiple cores
```

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Install Dependencies

```bash
cd streamlit-multipage
pip install -r requirements.txt
```

Or install manually:
```bash
pip install streamlit requests pandas plotly
```

## 💻 Usage

### Run Locally

```bash
streamlit run app.py
```

The app will automatically open in your browser at `http://localhost:8501`

### Stop the App

Press `Ctrl + C` in the terminal

## 📚 Page Overview

### Page 1: 🔍 Core Search & Overview
- Search cores by ID
- View basic information (Element, Type, Gender, Color)
- Power statistics for all modes (Bike, Car, Horse)
- Quick race summary
- Owner information

### Page 2: 📊 Performance Analysis
- **Method 1:** Weighted Performance Score (Win Rate 40% + Position 30% + Consistency 20% + vs Global 10%)
- **Method 3:** vs Global Average (identifies competitive advantages)
- Complete distance rankings table
- Top 3 recommended distances
- Requires minimum 20 races per distance

### Page 3: 🏁 Race History & Charts
- Interactive position distribution charts (1st-14th place)
- Finish time analysis with global averages
- Timeline visualization (Fastest, Average, Global Avg, Slowest)
- Average odds per distance
- Organized by racing mode

### Page 4: 🧬 Breeding & Lineage
- Core type and lineage (parents, grandparents)
- Breeding availability and pricing
- Breeding statistics (lifetime, cycle limits)
- Complete offspring list
- Cycle reset information
- Download offspring data

### Page 5: ⚖️ Core Comparison
- Compare 2-3 cores side-by-side
- Power statistics comparison charts
- Race count breakdown
- Best distance comparison
- Performance scoring

## ✨ Features

- ✅ **Real-time API data** from DNA Racing
- ✅ **Interactive Plotly charts** (hover, zoom, pan)
- ✅ **Session state management** (data persists between pages)
- ✅ **Responsive design** (works on mobile/tablet/desktop)
- ✅ **Global performance benchmarks**
- ✅ **Statistical accuracy** (20+ race minimum)
- ✅ **Multi-core comparison**
- ✅ **Breeding analytics**

## 🌐 Deploy to Cloud (Optional)

### Streamlit Cloud (Free)

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Deploy!

### Other Options
- Heroku
- AWS
- Google Cloud
- DigitalOcean

## 🛠️ Configuration

### API Settings
Edit `app.py` to change API configuration:
```python
API_BASE_URL = "https://api.dnaracing.run/fbike"
```

### Global Averages
Update `GLOBAL_AVERAGES` dictionary in `app.py` if new distances are added.

## 📊 Data Requirements

- **Minimum races:** 20 per distance for analysis inclusion
- **Cache:** Session-based (data refreshes when app restarts)
- **API timeout:** 30 seconds per request

## 🐛 Troubleshooting

### Port Already in Use
```bash
streamlit run app.py --server.port 8502
```

### Clear Cache
```bash
streamlit cache clear
```

### Module Not Found
```bash
pip install --upgrade -r requirements.txt
```

## 📝 Notes

- Data is fetched in real-time from the DNA Racing API
- Session state preserves data across pages during your browser session
- Tracking prevention must be disabled for API calls
- Charts are interactive - hover for details, click to zoom

## 🤝 Support

For issues or questions:
1. Check this README
2. Verify all dependencies are installed
3. Ensure Python version is 3.8+
4. Check API connectivity

## 📜 License

This tool is for personal use with DNA Racing data.

---

**Happy Racing! 🏁**
