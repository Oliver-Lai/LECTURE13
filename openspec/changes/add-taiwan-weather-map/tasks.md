# Implementation Tasks: Add Taiwan Weather Temperature Map

## Overview
This document outlines the ordered implementation tasks for building the Taiwan weather temperature map application using Streamlit. Tasks are organized to deliver incremental, testable progress with clear validation criteria.

## Prerequisites
- [ ] Python 3.9+ installed
- [ ] pip package manager available
- [ ] Modern web browser (Chrome, Firefox, Safari, or Edge)
- [ ] Internet connection for accessing CWA OpenData and map tiles
- [ ] GitHub account (for Streamlit Cloud deployment)

---

## Phase 1: Project Setup and Core Modules

### Task 1.1: Initialize Project Structure
**Estimated Time**: 15 minutes

**Actions**:
- Create directory structure:
  ```
  project/
  ├── app.py
  ├── requirements.txt
  ├── .gitignore
  ├── .streamlit/
  │   └── config.toml
  ├── src/
  │   ├── __init__.py
  │   ├── scraper.py
  │   ├── storage.py
  │   └── visualization.py
  ├── data/
  └── tests/
  ```
- Create `.gitignore` with entries for:
  - `__pycache__/`
  - `*.pyc`
  - `.env`
  - `data/*.db`
  - `venv/` or `.venv/`
  - `.streamlit/secrets.toml`
- Create `requirements.txt` with dependencies:
  ```
  streamlit>=1.28.0
  folium>=0.14.0
  streamlit-folium>=0.15.0
  requests>=2.31.0
  beautifulsoup4>=4.12.0
  lxml>=4.9.0
  pandas>=2.0.0
  ```

**Validation**:
- [x] All directories exist
- [x] `.gitignore` includes necessary patterns
- [x] `requirements.txt` contains all required packages

**Dependencies**: None

**Status**: ✅ COMPLETED

---

### Task 1.2: Set Up Python Virtual Environment
**Estimated Time**: 10 minutes

**Actions**:
- Create virtual environment: `python -m venv venv`
- Activate virtual environment
- Install dependencies: `pip install -r requirements.txt`
- Verify installations: `pip list`

**Validation**:
- [x] Virtual environment created successfully
- [x] All packages installed without errors
- [x] `pip list` shows streamlit, folium, streamlit-folium

**Dependencies**: Task 1.1

**Test Command**: `streamlit --version`

**Status**: ✅ COMPLETED

---

### Task 1.3: Create Streamlit Configuration
**Estimated Time**: 10 minutes

**Actions**:
- Create `.streamlit/config.toml`:
  ```toml
  [theme]
  primaryColor = "#FF6B6B"
  backgroundColor = "#FFFFFF"
  secondaryBackgroundColor = "#F0F2F6"
  textColor = "#262730"

  [server]
  headless = true
  port = 8501
  ```
- Create `.streamlit/secrets.toml.example`:
  ```toml
  # CWA API key (if required in future)
  # CWA_API_KEY = "your-api-key"
  ```

**Validation**:
- [x] Configuration files created
- [x] Theme settings are valid

**Dependencies**: Task 1.1

**Status**: ✅ COMPLETED

---

### Task 1.4: Implement Weather Scraper Module
**Estimated Time**: 2-3 hours

**Actions**:
- Create `src/scraper.py`
- Implement `fetch_weather_data()` function:
  - Make HTTP GET request to CWA OpenData URL
  - Set timeout (10 seconds)
  - Implement retry logic with exponential backoff (3 attempts)
  - Handle network errors and timeouts
- Implement `parse_weather_response(response)` function:
  - Inspect actual CWA response format (XML or JSON)
  - Parse the response structure
  - Extract location name, latitude, longitude, temperature, forecast time
  - Handle missing or invalid data
- Add logging for all operations
- Return list of dictionaries with structured data

**Validation**:
- [x] Scraper successfully fetches data from CWA
- [x] Data is parsed correctly (verify with print statements)
- [x] Missing data is handled without crashes
- [x] Retries work on network failures
- [x] Returns expected data structure (list of dicts)

**Dependencies**: Task 1.2

**Status**: ✅ COMPLETED

**Test Command**: 
```python
from src.scraper import fetch_weather_data
data = fetch_weather_data()
print(f"Retrieved {len(data)} locations")
print(data[0] if data else "No data")
```

---

### Task 1.5: Implement SQLite Storage Module
**Estimated Time**: 1.5-2 hours

**Actions**:
- Create `src/storage.py`
- Implement `WeatherDatabase` class:
  ```python
  class WeatherDatabase:
      def __init__(self, db_path: str = "data/weather.db")
      def _init_db(self)  # Create tables and indexes
      def save_weather_data(self, data: list[dict]) -> int
      def get_latest_data(self) -> list[dict]
      def get_data_by_location(self, location: str) -> list[dict]
      def cleanup_old_data(self, days: int = 30) -> int
      def close(self)
  ```
- Create database schema with UNIQUE constraint on (location_name, forecast_time)
- Handle upsert logic for duplicate records (INSERT OR REPLACE)
- Implement error handling with logging

**Validation**:
- [x] Database file is created at `data/weather.db`
- [x] Tables and indexes are created correctly
- [x] Data is saved successfully
- [x] Duplicate records are updated (not duplicated)
- [x] Query functions return correct data format

**Dependencies**: Task 1.2

**Status**: ✅ COMPLETED

**Test Command**: 
```python
from src.storage import WeatherDatabase
from src.scraper import fetch_weather_data

db = WeatherDatabase("data/weather.db")
data = fetch_weather_data()
saved = db.save_weather_data(data)
print(f"Saved {saved} records")
latest = db.get_latest_data()
print(f"Retrieved {len(latest)} records")
db.close()
```

---

### Task 1.6: Implement Visualization Helper Module
**Estimated Time**: 1 hour

**Actions**:
- Create `src/visualization.py`
- Implement `get_temperature_color(temperature: float) -> str`:
  - Return hex color based on temperature ranges:
    - < 10°C → #0000FF (Blue)
    - 10-15°C → #00FFFF (Cyan)
    - 15-20°C → #00FF00 (Green)
    - 20-25°C → #FFFF00 (Yellow)
    - 25-30°C → #FFA500 (Orange)
    - > 30°C → #FF0000 (Red)
- Implement `create_folium_map(data: list[dict]) -> folium.Map`:
  - Initialize map centered on Taiwan [23.5, 121.0], zoom 7
  - Add CircleMarker for each location with color
  - Add popup with location name and temperature
  - Return the folium Map object
- Implement `get_legend_html() -> str`:
  - Return HTML for temperature color legend

**Validation**:
- [x] Color mapping works for all temperature ranges
- [x] Map is created with correct center and zoom
- [x] Markers are positioned correctly
- [x] Popups display correct information

**Dependencies**: Task 1.2

**Status**: ✅ COMPLETED

**Test Command**:
```python
from src.visualization import get_temperature_color, create_folium_map

print(get_temperature_color(5))   # Should be #0000FF
print(get_temperature_color(25))  # Should be #FFFF00
print(get_temperature_color(35))  # Should be #FF0000
```

---

## Phase 2: Streamlit Application

### Task 2.1: Create Basic Streamlit App
**Estimated Time**: 30 minutes

**Actions**:
- Create `app.py` with basic structure:
  ```python
  import streamlit as st
  
  st.set_page_config(
      page_title="Taiwan Weather Map",
      page_icon="🌡️",
      layout="wide"
  )
  
  st.title("🌡️ Taiwan Weather Temperature Map")
  ```
- Add sidebar placeholder
- Add main content area placeholder

**Validation**:
- [x] App runs without errors: `streamlit run app.py`
- [x] Title appears correctly
- [x] Page config is applied (wide layout)

**Dependencies**: Task 1.3

**Test Command**: `streamlit run app.py`

**Status**: ✅ COMPLETED

---

### Task 2.2: Integrate Data Fetching with Session State
**Estimated Time**: 45 minutes

**Actions**:
- Import scraper and storage modules
- Use `st.session_state` for caching:
  ```python
  if 'weather_data' not in st.session_state:
      st.session_state.weather_data = None
      st.session_state.last_update = None
  ```
- Implement data loading function with caching logic
- Add refresh button to sidebar
- Display last update timestamp

**Validation**:
- [x] Data loads on first run
- [x] Session state persists across reruns
- [x] Refresh button triggers new data fetch
- [x] Last update time is displayed

**Dependencies**: Task 2.1, Task 1.4, Task 1.5

**Status**: ✅ COMPLETED

---

### Task 2.3: Integrate Folium Map Display
**Estimated Time**: 1 hour

**Actions**:
- Import visualization module and streamlit_folium
- Create map when data is available:
  ```python
  from streamlit_folium import st_folium
  from src.visualization import create_folium_map
  
  if st.session_state.weather_data:
      m = create_folium_map(st.session_state.weather_data)
      st_folium(m, width=800, height=600)
  ```
- Handle empty data state with message
- Add loading spinner during map creation

**Validation**:
- [x] Map displays correctly with markers
- [x] Markers have correct colors
- [x] Clicking markers shows popup
- [x] Empty data shows appropriate message

**Dependencies**: Task 2.2, Task 1.6

**Status**: ✅ COMPLETED

---

### Task 2.4: Add Statistics Sidebar
**Estimated Time**: 30 minutes

**Actions**:
- Calculate statistics from weather data:
  - Number of locations
  - Average temperature
  - Highest temperature (with location)
  - Lowest temperature (with location)
- Display in sidebar using `st.metric`:
  ```python
  st.sidebar.header("📊 Statistics")
  st.sidebar.metric("Locations", len(data))
  st.sidebar.metric("Average Temp", f"{avg_temp:.1f}°C")
  st.sidebar.metric("Highest", f"{max_temp:.1f}°C", location)
  st.sidebar.metric("Lowest", f"{min_temp:.1f}°C", location)
  ```

**Validation**:
- [x] All statistics display correctly
- [x] Values are accurate
- [x] Formatting is clear and readable

**Dependencies**: Task 2.3

**Status**: ✅ COMPLETED

---

### Task 2.5: Add Temperature Legend to Sidebar
**Estimated Time**: 20 minutes

**Actions**:
- Add legend section to sidebar
- Use colored boxes with temperature ranges:
  ```python
  st.sidebar.header("🎨 Legend")
  st.sidebar.markdown("""
  - 🔵 < 10°C
  - 🔷 10-15°C
  - 🟢 15-20°C
  - 🟡 20-25°C
  - 🟠 25-30°C
  - 🔴 > 30°C
  """)
  ```
- Or use HTML with colored divs

**Validation**:
- [x] Legend displays in sidebar
- [x] All color ranges are shown
- [x] Colors match marker colors on map

**Dependencies**: Task 2.4

**Status**: ✅ COMPLETED

---

### Task 2.6: Add Error Handling and Loading States
**Estimated Time**: 30 minutes

**Actions**:
- Wrap data fetching in try-except
- Display user-friendly error messages using `st.error()`
- Add loading spinner using `st.spinner()`:
  ```python
  with st.spinner("Loading weather data..."):
      data = fetch_weather_data()
  ```
- Add retry button on error

**Validation**:
- [x] Loading spinner appears during data fetch
- [x] Errors display friendly messages
- [x] Retry button works correctly

**Dependencies**: Task 2.5

**Status**: ✅ COMPLETED

---

## Phase 3: Deployment Preparation

### Task 3.1: Prepare GitHub Repository
**Estimated Time**: 15 minutes

**Actions**:
- Initialize git repository: `git init`
- Add all files: `git add .`
- Create initial commit: `git commit -m "Initial commit: Taiwan Weather Map"`
- Create GitHub repository
- Push to GitHub: `git push -u origin main`

**Validation**:
- [ ] Repository is created on GitHub
- [ ] All files are pushed
- [ ] .gitignore is working (no venv or secrets)

**Dependencies**: Phase 2 complete

---

### Task 3.2: Test Local Deployment
**Estimated Time**: 15 minutes

**Actions**:
- Run app in fresh environment:
  ```bash
  deactivate  # Exit current venv
  rm -rf venv
  python -m venv venv
  source venv/bin/activate  # or venv\Scripts\activate on Windows
  pip install -r requirements.txt
  streamlit run app.py
  ```
- Verify all features work

**Validation**:
- [ ] App starts from fresh install
- [ ] All dependencies install correctly
- [ ] Map loads and displays data

**Dependencies**: Task 3.1

---

### Task 3.3: Deploy to Streamlit Cloud
**Estimated Time**: 20 minutes

**Actions**:
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select repository, branch, and `app.py`
5. Click "Deploy"
6. Wait for deployment to complete
7. Test the deployed app

**Validation**:
- [ ] App deploys without errors
- [ ] App is accessible via public URL
- [ ] Data loads correctly in cloud
- [ ] Map displays properly

**Dependencies**: Task 3.2

---

### Task 3.4: Create README Documentation
**Estimated Time**: 30 minutes

**Actions**:
- Create `README.md` with:
  - Project title and description
  - Screenshot of the application
  - Features list
  - Installation instructions
  - Local development guide
  - Deployment instructions
  - Technology stack
  - License

**Validation**:
- [ ] README is complete and accurate
- [ ] Instructions are clear
- [ ] Links work correctly

**Dependencies**: Task 3.3

---

## Phase 4: Testing and Refinement

### Task 4.1: Unit Testing
**Estimated Time**: 1.5 hours

**Actions**:
- Create `tests/test_scraper.py`
  - Test `fetch_weather_data()` with mocked responses
  - Test retry logic
  - Test error handling
- Create `tests/test_storage.py`
  - Test database initialization
  - Test save and query operations
  - Test duplicate handling
- Create `tests/test_visualization.py`
  - Test color mapping for all ranges
- Run tests with pytest

**Validation**:
- [ ] All tests pass
- [ ] Edge cases are covered

**Dependencies**: Phase 2 complete

**Test Command**: `pytest tests/`

---

### Task 4.2: Manual Testing Checklist
**Estimated Time**: 1 hour

**Actions**:
- Test on deployed Streamlit Cloud:
  - [ ] Page loads correctly
  - [ ] Map displays Taiwan
  - [ ] Temperature markers are visible
  - [ ] Marker colors are correct
  - [ ] Clicking markers shows popup
  - [ ] Statistics in sidebar are accurate
  - [ ] Refresh button works
  - [ ] Legend is visible
- Test on different devices:
  - [ ] Desktop browser
  - [ ] Mobile browser (responsive)
- Test error scenarios:
  - [ ] App handles CWA unavailable

**Dependencies**: Task 3.3

---

## Summary

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1: Project Setup | 6 tasks | 6-8 hours |
| Phase 2: Streamlit App | 6 tasks | 3-4 hours |
| Phase 3: Deployment | 4 tasks | 1.5 hours |
| Phase 4: Testing | 2 tasks | 2.5 hours |
| **Total** | **18 tasks** | **13-16 hours** |

## Quick Start Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run locally
streamlit run app.py

# Run tests
pytest tests/
```
