# Design: Taiwan Weather Temperature Map

## Architecture Overview

This application follows a simplified Streamlit-based architecture for easy deployment:

```
┌─────────────────────────────────────────────────────────────┐
│                 Streamlit Cloud / Local                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Streamlit Application (app.py)                    │    │
│  │  - UI components (sidebar, main area)              │    │
│  │  - Session state management                        │    │
│  │  - User interaction handling                       │    │
│  └──────────────────┬─────────────────────────────────┘    │
│                     │                                        │
│  ┌──────────────────▼─────────────────────────────────┐    │
│  │  Folium Map Visualization                          │    │
│  │  - Interactive map rendering                        │    │
│  │  - Temperature markers with color coding           │    │
│  │  - Popups and legend                               │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Data Layer                                        │    │
│  │  ┌─────────────────┐  ┌─────────────────────────┐ │    │
│  │  │  SQLite Storage │  │  Weather Data Scraper   │ │    │
│  │  │  - Persistence  │  │  - CWA OpenData fetch   │ │    │
│  │  │  - Queries      │  │  - Parse & transform    │ │    │
│  │  └─────────────────┘  └─────────────────────────┘ │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                       │
                       │ HTTPS API
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  CWA OpenData API                            │
│  - Temperature forecast data                                 │
│  - JSON/XML response                                         │
└─────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. Streamlit Application (app.py)

**Technology**: Streamlit 1.28+

**Responsibilities**:
- Main application entry point
- UI layout and components
- Session state management for caching
- User interaction handling (refresh button, etc.)
- Integration of all modules

**Key Design Decisions**:
- Single-file main application for simplicity
- Use `st.session_state` for in-memory caching
- Sidebar for statistics and controls
- Main area for map display

**Application Layout**:
```
┌────────────────────────────────────────────────────────┐
│  Taiwan Weather Temperature Map                   [⟳]  │
├──────────────┬─────────────────────────────────────────┤
│   Sidebar    │                                         │
│              │                                         │
│ Statistics   │         Folium Map                      │
│ - Locations  │         (Full Width)                    │
│ - Avg Temp   │                                         │
│ - Min/Max    │                                         │
│              │                                         │
│ Last Update  │                                         │
│ [Refresh]    │                                         │
│              │                                         │
│ Legend       │                                         │
│ ■ <10°C      │                                         │
│ ■ 10-15°C    │                                         │
│ ...          │                                         │
└──────────────┴─────────────────────────────────────────┘
```

### 2. Web Scraper Component

**Technology**: Python with `requests` and `BeautifulSoup4` or `lxml`

**Responsibilities**:
- Fetch data from CWA OpenData API endpoint
- Parse XML/JSON response format
- Extract relevant fields (location name, coordinates, temperature)
- Handle network errors and timeouts
- Log scraping activities

**Key Design Decisions**:
- Use `requests` library for HTTP calls (simple, reliable)
- Parse response based on CWA's data format (likely XML or JSON)
- Implement exponential backoff for retries (3 attempts max)
- Cache raw responses for 30 minutes to reduce API load

**Data Flow**:
```
CWA OpenData URL → HTTP GET → Parse Response → Extract Data → 
Return Structured Dict/List
```

**Example Output Structure**:
```python
[
    {
        "location_name": "台北",
        "latitude": 25.0330,
        "longitude": 121.5654,
        "temperature": 28.5,
        "forecast_time": "2025-12-03T14:00:00",
        "unit": "C"
    },
    ...
]
```

### 2. SQLite Storage Component

**Technology**: Python with `sqlite3` (standard library)

**Responsibilities**:
- Initialize database and create schema on first run
- Persist scraped weather data for historical tracking
- Handle duplicate records with upsert logic
- Provide query functions for data retrieval
- Implement data retention and cleanup policies
- Support data export to CSV/JSON

**Key Design Decisions**:
- Use SQLite for simplicity (no external database server required)
- Store data with timestamps for historical tracking
- Use UNIQUE constraint on (location_name, forecast_time) to prevent duplicates
- Implement 30-day default retention policy
- Use context manager pattern for database connections

**Database Schema**:
```sql
CREATE TABLE IF NOT EXISTS weather_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_name TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    temperature REAL NOT NULL,
    unit TEXT DEFAULT 'C',
    forecast_time TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_location_forecast 
    ON weather_records(location_name, forecast_time);
CREATE INDEX IF NOT EXISTS idx_created_at ON weather_records(created_at);
```

**Data Flow**:
```
Scraper Output → WeatherDatabase.save_weather_data() → 
SQLite INSERT/UPDATE → Return saved count
```

**Module Interface**:
```python
class WeatherDatabase:
    def __init__(self, db_path: str = "data/weather.db")
    def save_weather_data(self, data: list[dict]) -> int
    def get_latest_data(self) -> list[dict]
    def get_data_by_time_range(self, start: str, end: str) -> list[dict]
    def get_data_by_location(self, location: str) -> list[dict]
    def cleanup_old_data(self, days: int = 30) -> int
    def export_to_csv(self, path: str, **filters) -> str
    def close(self)
```

### 3. Data Processing Layer

**Technology**: Python with `pandas` (optional, for complex processing) or native data structures

**Responsibilities**:
- Transform scraped data into GeoJSON format for Leaflet.js
- Apply temperature color mapping
- Validate data integrity (check for missing coordinates, invalid temperatures)
- Implement data aggregation if multiple forecasts exist for same location
- Cache processed results

**Key Design Decisions**:
- Output GeoJSON format (standard for mapping libraries)
- Use temperature ranges for color coding (e.g., <10°C blue, 10-20°C green, 20-30°C yellow, >30°C red)
- Store processed data in memory with TTL (30 min refresh cycle)

**GeoJSON Output Example**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [121.5654, 25.0330]
      },
      "properties": {
        "location": "台北",
        "temperature": 28.5,
        "color": "#FFA500",
        "forecast_time": "2025-12-03T14:00:00"
      }
    }
  ]
}
```

### 4. Web Server Component

**Technology**: Python Flask or FastAPI

**Responsibilities**:
- Serve static files (HTML, CSS, JavaScript)
- Provide REST API endpoint for weather data
- Handle CORS for local development
- Trigger data refresh on request or schedule

**API Endpoints**:
```
GET /                        → Serve index.html
GET /api/weather/current     → Return current temperature GeoJSON
GET /api/weather/history     → Return historical data (from SQLite)
GET /api/weather/export      → Export data to CSV/JSON
GET /static/*                → Serve CSS/JS files
```

**Key Design Decisions**:
- Use Flask for simplicity (FastAPI if async is needed later)
- Integrate with SQLite storage for data persistence
- Enable CORS middleware for development
- Implement basic error responses (404, 500)

### 5. Map Visualization Component

**Technology**: HTML5, CSS3, JavaScript (Vanilla or minimal framework), Leaflet.js

**Responsibilities**:
- Initialize Leaflet map centered on Taiwan
- Fetch weather data from server API
- Render temperature markers/heat layer
- Handle user interactions (zoom, pan, marker clicks)
- Display legend for temperature colors
- Update data periodically or on user refresh

**Key Design Decisions**:
- Use OpenStreetMap tiles (free, no API key required)
- Implement marker clustering for dense areas (optional, if >100 locations)
- Use Circle Markers with color fill based on temperature
- Add popup on marker click showing location name and temperature
- Use Leaflet Heat plugin for continuous heat map overlay (optional enhancement)

**Map Configuration**:
```javascript
{
  center: [23.5, 121.0],  // Taiwan center
  zoom: 7,                 // Show entire Taiwan
  minZoom: 6,
  maxZoom: 18
}
```

**Temperature Color Scale**:
```
< 10°C  → #0000FF (Blue)
10-15°C → #00FFFF (Cyan)
15-20°C → #00FF00 (Green)
20-25°C → #FFFF00 (Yellow)
25-30°C → #FFA500 (Orange)
> 30°C  → #FF0000 (Red)
```

## Data Flow Diagram

```
┌──────────┐
│  Timer   │ (every 30 min or manual trigger)
└────┬─────┘
     │
     ▼
┌─────────────────┐
│  Web Scraper    │ → Fetch from CWA OpenData
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│ Parse & Extract │ → Raw temperature data
└────┬────────────┘
     │
     ├───────────────────────┐
     ▼                       ▼
┌─────────────────┐   ┌─────────────────┐
│ SQLite Storage  │   │ Data Processing │ → Transform data
│ (Persistence)   │   └────┬────────────┘
│ - Save records  │        │
│ - Query history │        ▼
└─────────────────┘   ┌─────────────────┐
     │                │ Session State   │ → Cache for 30 min
     │                └────┬────────────┘
     │                     │
     │                     ▼
     │                ┌─────────────────┐
     └───────────────►│ Streamlit App   │ → app.py
                      │                 │
                      └────┬────────────┘
                           │
                           ▼
                      ┌─────────────────┐
                      │  Folium Map     │ → Render visualization
                      └─────────────────┘
```

## Technology Stack

### Application Framework
- **Language**: Python 3.9+
- **Web Framework**: Streamlit 1.28+
- **Mapping**: Folium 0.14+ with streamlit-folium 0.15+
- **HTTP Client**: requests 2.31+
- **Parsing**: BeautifulSoup4 4.12+ or lxml 4.9+
- **Data Processing**: pandas 2.0+

### Deployment
- **Platform**: Streamlit Cloud (free tier available)
- **Database**: SQLite (ephemeral in cloud, persistent locally)
- **Configuration**: .streamlit/config.toml

### Development Tools
- **Package Manager**: pip
- **Environment**: venv or conda for Python isolation
- **Testing**: pytest

## File Structure

```
project/
├── app.py                    # Main Streamlit application entry point
├── requirements.txt          # Python dependencies
├── .streamlit/
│   ├── config.toml          # Streamlit configuration
│   └── secrets.toml.example # Secrets template (for API keys)
├── src/
│   ├── __init__.py
│   ├── scraper.py           # Web scraping logic
│   ├── storage.py           # SQLite database operations
│   └── visualization.py     # Map rendering helpers
├── data/
│   └── weather.db           # SQLite database file (local only, gitignored)
├── tests/
│   ├── test_scraper.py
│   └── test_storage.py
└── README.md                # Setup and deployment instructions
```

## Security Considerations

1. **Input Validation**: Validate and sanitize all data from CWA before processing
2. **Rate Limiting**: Implement request throttling to prevent abuse
3. **CORS**: Configure CORS properly (allow only specific origins in production)
4. **Error Handling**: Never expose internal error details to client
5. **Dependencies**: Keep libraries updated for security patches

## Performance Considerations

1. **Caching**: Cache scraped data for 30 minutes to reduce CWA API load
2. **Compression**: Use gzip compression for API responses
3. **Lazy Loading**: Load map tiles on demand
4. **Marker Optimization**: Use marker clustering if >100 locations
5. **Async Processing**: Consider async scraping if multiple data sources added later

## Error Handling Strategy

1. **Network Errors**: Retry with exponential backoff (3 attempts)
2. **Parse Errors**: Log error, return cached data if available, or empty result
3. **Invalid Data**: Filter out records with missing/invalid coordinates
4. **Application Errors**: Display user-friendly error message with retry option

## Testing Strategy

### Unit Tests
- Unit tests for scraper (mock HTTP responses)
- Unit tests for storage (SQLite operations)
- Unit tests for visualization helpers

### Integration Tests
- Test full flow from scraping to database storage
- Test map rendering with sample data

### Manual Tests
- Test Streamlit UI interactions
- Test map zoom, pan, marker clicks
- Test data refresh functionality
- Test on different screen sizes

## Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
streamlit run app.py
```

### Streamlit Cloud Deployment
1. Push code to GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app" and connect your GitHub repository
4. Select branch and `app.py` as the main file
5. Click "Deploy"

**Important Notes for Cloud Deployment**:
- SQLite database is ephemeral (resets on app restart)
- Use `st.session_state` for in-session caching
- App will fetch fresh data on each cold start
- Free tier: 1GB RAM, suitable for this application

### Configuration Files Required

**.streamlit/config.toml**:
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

**requirements.txt**:
```
streamlit>=1.28.0
folium>=0.14.0
streamlit-folium>=0.15.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
pandas>=2.0.0
```

## Extensibility

This design allows for future enhancements:

1. **Multiple Data Layers**: Add rainfall, wind speed, humidity overlays
2. **Time Slider**: Show forecast for different time periods
3. **Historical Data**: Compare current forecast with historical patterns
4. **Data Export**: Download button for CSV export (Streamlit native support)
5. **Multi-page App**: Separate pages for different features

## Design Decisions

### Why Streamlit instead of Flask + Leaflet.js?

| Aspect | Flask + Leaflet.js | Streamlit + Folium |
|--------|-------------------|-------------------|
| Complexity | High (separate frontend/backend) | Low (single Python file) |
| Deployment | Complex (need hosting for both) | Simple (Streamlit Cloud free) |
| Development | HTML/CSS/JS + Python | Python only |
| Maintenance | Two codebases | Single codebase |
| Interactivity | Full control | Good enough for this use case |

**Chosen**: Streamlit + Folium
**Rationale**: 
- Simpler development with Python-only codebase
- Free deployment on Streamlit Cloud
- Built-in session state for caching
- Good enough interactivity for weather visualization
- Faster iteration and easier maintenance

## Open Questions

1. **CWA Data Format**: Need to inspect actual API response to determine XML vs JSON parsing approach
2. **Update Frequency**: Should we fetch every 30 minutes, hourly, or on-demand?
3. **Number of Locations**: How many weather stations does CWA provide data for?
4. **Forecast Horizon**: Show only current forecast or next 24/48 hours?

These will be resolved during implementation phase by inspecting the actual CWA OpenData response.
