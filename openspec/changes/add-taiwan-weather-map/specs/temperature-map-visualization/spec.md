# Specification: Temperature Map Visualization (Folium)

## Overview
A Folium-based interactive map component that visualizes temperature forecast data across Taiwan, integrated with Streamlit using the streamlit-folium package. Provides color-coded markers with popups for temperature information.

## ADDED Requirements

### Requirement: The system MUST initialize an interactive Folium map

The system SHALL create a Folium map centered on Taiwan with appropriate zoom levels.

#### Scenario: Create map centered on Taiwan
**Given** the visualization module is called  
**When** creating a new map  
**Then** the map should be centered at coordinates [23.5, 121.0]  
**And** the initial zoom level should be 7 (showing entire Taiwan)  
**And** OpenStreetMap tiles should be used as the base layer

#### Scenario: Set map dimensions
**Given** the map is embedded in Streamlit  
**When** using `st_folium()` to display  
**Then** the map width should be responsive to container  
**And** the height should be at least 500 pixels

---

### Requirement: The system MUST render temperature markers

The system SHALL display temperature data as color-coded circular markers on the map.

#### Scenario: Create CircleMarker for each location
**Given** valid temperature data is provided  
**When** rendering markers  
**Then** each location should be displayed as a Folium CircleMarker  
**And** the marker should be positioned at the correct [latitude, longitude]  
**And** the marker radius should be 8 pixels  
**And** the marker should have a stroke (border) for visibility

#### Scenario: Apply temperature color coding
**Given** a location with a specific temperature  
**When** creating the marker  
**Then** the marker fill color should be determined by temperature:
- Temperature < 10°C → Blue (#0000FF)
- Temperature 10-15°C → Cyan (#00FFFF)
- Temperature 15-20°C → Green (#00FF00)
- Temperature 20-25°C → Yellow (#FFFF00)
- Temperature 25-30°C → Orange (#FFA500)
- Temperature > 30°C → Red (#FF0000)

#### Scenario: Handle invalid coordinates
**Given** a temperature record with missing or invalid coordinates  
**When** processing the data  
**Then** the system should skip that marker  
**And** continue rendering remaining markers without error

---

### Requirement: The system MUST implement interactive popups

The system SHALL display detailed information when users click on temperature markers.

#### Scenario: Show popup on marker click
**Given** temperature markers are displayed on the map  
**When** the user clicks a marker  
**Then** a popup should appear  
**And** the popup should contain:
- Location name (in Chinese)
- Temperature value with unit (e.g., "28.5°C")
- Forecast time (formatted readably)

#### Scenario: Format popup content
**Given** a popup is created  
**When** the content is rendered  
**Then** the HTML should be properly formatted  
**And** use readable font sizes  
**And** include proper spacing

---

### Requirement: The system MUST provide a color legend

The system SHALL provide a legend explaining the temperature color scheme.

#### Scenario: Generate legend HTML
**Given** the visualization module is used  
**When** `get_legend_html()` is called  
**Then** it should return valid HTML  
**And** include all six temperature ranges with corresponding colors  
**And** be styled for readability

#### Scenario: Display legend in sidebar
**Given** the Streamlit app renders  
**When** the sidebar displays  
**Then** the legend should be visible  
**And** show all temperature ranges:
- "< 10°C" with blue indicator
- "10-15°C" with cyan indicator
- "15-20°C" with green indicator
- "20-25°C" with yellow indicator
- "25-30°C" with orange indicator
- "> 30°C" with red indicator

---

### Requirement: The system MUST support map interaction

The system SHALL allow users to interact with the map through zoom and pan.

#### Scenario: Enable zoom controls
**Given** the map is displayed  
**When** the user interacts with the map  
**Then** zoom controls should be visible  
**And** mouse wheel zoom should work  
**And** pinch-to-zoom should work on touch devices

#### Scenario: Enable pan navigation
**Given** the map is displayed  
**When** the user drags the map  
**Then** the map should pan to follow the drag  
**And** the movement should be smooth

---

## Code Structure

### visualization.py

```python
import folium
from typing import List, Dict

def get_temperature_color(temperature: float) -> str:
    """Return hex color based on temperature value."""
    pass

def create_folium_map(data: List[Dict]) -> folium.Map:
    """Create a Folium map with temperature markers."""
    pass

def get_legend_html() -> str:
    """Return HTML for temperature legend."""
    pass
```

## Dependencies
- `folium>=0.14.0`: Interactive map library
- `streamlit-folium>=0.15.0`: Streamlit integration

## Color Scale Reference

| Temperature Range | Color | Hex Code |
|------------------|-------|----------|
| < 10°C | Blue | #0000FF |
| 10-15°C | Cyan | #00FFFF |
| 15-20°C | Green | #00FF00 |
| 20-25°C | Yellow | #FFFF00 |
| 25-30°C | Orange | #FFA500 |
| > 30°C | Red | #FF0000 |
