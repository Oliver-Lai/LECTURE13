# Change: Add Taiwan Weather Temperature Map Web Application

## Why
Users need an intuitive way to visualize temperature forecast data across Taiwan. Currently, accessing CWA data requires navigating text-based or static formats, which is not user-friendly for quick geographic analysis. An interactive map provides immediate spatial understanding of temperature patterns.

## What Changes
- **NEW**: Weather data scraper capability for Taiwan's Central Weather Administration (CWA) OpenData
- **NEW**: SQLite database storage for persisting scraped weather data with historical tracking
- **NEW**: Streamlit web application with integrated Folium map visualization
- **NEW**: Streamlit Cloud deployment configuration for public access
- **REMOVED**: Flask web server (replaced by Streamlit)
- **REMOVED**: Leaflet.js frontend (replaced by Folium in Streamlit)

## Impact
- **Affected specs**: Creates 5 capabilities:
  - `weather-data-scraper`: Fetches and parses CWA temperature data
  - `sqlite-data-storage`: Persists weather data to SQLite for historical tracking and offline access
  - `web-application`: Streamlit application with map and data display
  - `temperature-map-visualization`: Folium-based interactive map interface
  - `streamlit-deployment`: Configuration for Streamlit Cloud deployment
- **Affected code**: New project - creates backend/ and frontend/ directories with full application structure
- **Users**: Enables quick visual understanding of Taiwan temperature patterns without parsing text data
- **Technical**: Establishes foundation for adding more weather parameters (rainfall, wind, humidity) in future
- **Timeline**: Estimated 18-22 hours of development work

## Scope
**In Scope:**
- Web scraper for CWA OpenData temperature forecasts
- SQLite database storage for weather data persistence and historical tracking
- Streamlit web application with Folium map integration
- Color-coded temperature markers with popups
- Data refresh functionality
- Streamlit Cloud deployment for public access

**Out of Scope (Future):**
- Historical data analysis and visualization
- Multiple weather parameters
- User authentication
- Real-time alerts
- Mobile native app
- Migration to production databases (PostgreSQL)
