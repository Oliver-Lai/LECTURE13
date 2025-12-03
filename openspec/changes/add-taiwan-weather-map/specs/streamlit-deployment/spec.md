# Specification: Streamlit Deployment

## Overview
A Streamlit-based web application that replaces the Flask + Leaflet.js architecture with a unified Python application. This enables simple deployment to Streamlit Cloud for public access without managing separate frontend and backend components.

## ADDED Requirements

### Requirement: The system MUST provide a Streamlit application entry point

The system SHALL create a main Streamlit application file that serves as the entry point for the web application.

#### Scenario: Launch Streamlit application locally
**Given** the user has installed all dependencies  
**When** the user runs `streamlit run app.py`  
**Then** the Streamlit server should start on port 8501 (default)  
**And** the browser should automatically open to the application  
**And** the application should display the Taiwan weather map interface

#### Scenario: Application structure
**Given** the Streamlit application is created  
**When** the application initializes  
**Then** the main file should be named `app.py` in the project root  
**And** it should import and use the scraper, storage, and visualization modules  
**And** it should handle session state for caching

---

### Requirement: The system MUST render an interactive map using Folium

The system SHALL use Folium library integrated with Streamlit to display the temperature map.

#### Scenario: Display Taiwan-centered map
**Given** the Streamlit application loads  
**When** the map component renders  
**Then** a Folium map should be displayed centered at [23.5, 121.0]  
**And** the initial zoom level should be 7  
**And** OpenStreetMap tiles should be used as the base layer

#### Scenario: Render temperature markers on map
**Given** weather data is available  
**When** the map renders  
**Then** each location should display a CircleMarker  
**And** the marker color should reflect temperature (using the defined color scale)  
**And** clicking a marker should show a popup with location name and temperature

#### Scenario: Display temperature legend
**Given** the map is rendered  
**When** the user views the page  
**Then** a legend should be visible showing temperature color ranges  
**And** the legend should use Streamlit sidebar or an overlay

---

### Requirement: The system MUST support manual data refresh

The system SHALL provide a button for users to manually refresh weather data.

#### Scenario: Refresh button in UI
**Given** the application is running  
**When** the user views the interface  
**Then** a "Refresh Data" button should be visible  
**And** the button should be styled clearly

#### Scenario: Trigger data refresh
**Given** the user clicks the refresh button  
**When** the action is processed  
**Then** the system should fetch new data from CWA OpenData  
**And** update the SQLite database with new records  
**And** re-render the map with fresh data  
**And** display the last update timestamp

---

### Requirement: The system MUST display data statistics

The system SHALL show summary statistics about the current weather data.

#### Scenario: Show temperature statistics
**Given** weather data is loaded  
**When** the page renders  
**Then** the application should display:
- Number of locations with data
- Average temperature across Taiwan
- Highest and lowest temperatures with location names
- Last data update timestamp

#### Scenario: Display in sidebar
**Given** statistics are calculated  
**When** rendering the UI  
**Then** statistics should appear in the Streamlit sidebar  
**And** be clearly formatted with appropriate units

---

### Requirement: The system MUST be deployable to Streamlit Cloud

The system SHALL include all necessary configuration files for Streamlit Cloud deployment.

#### Scenario: Create requirements.txt
**Given** the application is ready for deployment  
**When** preparing deployment files  
**Then** a `requirements.txt` file should exist in the project root  
**And** it should list all Python dependencies with versions:
- streamlit>=1.28.0
- folium>=0.14.0
- streamlit-folium>=0.15.0
- requests>=2.31.0
- beautifulsoup4>=4.12.0
- pandas>=2.0.0

#### Scenario: Create .streamlit/config.toml
**Given** the application needs custom configuration  
**When** preparing deployment files  
**Then** a `.streamlit/config.toml` file should exist  
**And** it should configure theme and server settings

#### Scenario: Create secrets configuration template
**Given** the application may need API keys (future)  
**When** preparing deployment files  
**Then** a `.streamlit/secrets.toml.example` file should exist  
**And** document any required secrets (e.g., CWA API key if needed)

#### Scenario: Deploy to Streamlit Cloud
**Given** all configuration files are in place  
**When** the repository is connected to Streamlit Cloud  
**Then** the application should deploy successfully  
**And** be accessible via a public URL (*.streamlit.app)  
**And** handle the SQLite database in the cloud environment

---

### Requirement: The system MUST handle cloud environment constraints

The system SHALL adapt to Streamlit Cloud's ephemeral file system.

#### Scenario: Handle ephemeral storage
**Given** Streamlit Cloud restarts the application  
**When** the application initializes  
**Then** the system should recreate the SQLite database if it doesn't exist  
**And** fetch fresh data from CWA OpenData  
**And** not crash due to missing database file

#### Scenario: Use session state for caching
**Given** the application is running in the cloud  
**When** users interact with the app  
**Then** the system should use `st.session_state` for in-memory caching  
**And** cache weather data for 30 minutes within a session  
**And** share cache across page reruns

---

## Configuration Files

### requirements.txt
```
streamlit>=1.28.0
folium>=0.14.0
streamlit-folium>=0.15.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
pandas>=2.0.0
```

### .streamlit/config.toml
```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"

[server]
headless = true
port = 8501
enableCORS = false
```

## File Structure

```
project/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── .streamlit/
│   ├── config.toml          # Streamlit configuration
│   └── secrets.toml.example # Secrets template
├── src/
│   ├── scraper.py           # Weather data scraper
│   ├── storage.py           # SQLite database operations
│   └── visualization.py     # Map rendering helpers
├── data/
│   └── weather.db           # SQLite database (local only)
└── README.md                # Setup and deployment instructions
```

## Dependencies
- `streamlit>=1.28.0`: Web application framework
- `folium>=0.14.0`: Interactive map library
- `streamlit-folium>=0.15.0`: Folium integration for Streamlit
- `requests>=2.31.0`: HTTP client for API calls
- `beautifulsoup4>=4.12.0`: HTML/XML parsing
- `pandas>=2.0.0`: Data manipulation

## Deployment Instructions

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
streamlit run app.py
```

### Streamlit Cloud Deployment
1. Push code to GitHub repository
2. Go to share.streamlit.io
3. Connect GitHub repository
4. Select `app.py` as the main file
5. Deploy

## Future Enhancements (Out of Scope)
- User authentication via Streamlit secrets
- Multiple weather parameters selection
- Historical data visualization with date picker
- Export data as CSV download
