"""Visualization module for temperature map using Folium."""

import logging
from typing import Optional

import folium
from folium.plugins import MarkerCluster

from .config import DEFAULT_MAP_CENTER, DEFAULT_MAP_ZOOM

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Temperature color ranges (Celsius)
TEMPERATURE_COLORS = [
    (float('-inf'), 10, '#0000FF', 'Cold (<10°C)'),      # Blue
    (10, 15, '#00FFFF', 'Cool (10-15°C)'),               # Cyan
    (15, 20, '#00FF00', 'Mild (15-20°C)'),               # Green
    (20, 25, '#FFFF00', 'Warm (20-25°C)'),               # Yellow
    (25, 30, '#FFA500', 'Hot (25-30°C)'),                # Orange
    (30, float('inf'), '#FF0000', 'Very Hot (>30°C)')    # Red
]


def get_temperature_color(temperature: float) -> str:
    """Get color for a temperature value.
    
    Args:
        temperature: Temperature in Celsius.
        
    Returns:
        Hex color string.
    """
    for min_temp, max_temp, color, _ in TEMPERATURE_COLORS:
        if min_temp <= temperature < max_temp:
            return color
    return '#808080'  # Gray as fallback


def get_temperature_label(temperature: float) -> str:
    """Get label for a temperature value.
    
    Args:
        temperature: Temperature in Celsius.
        
    Returns:
        Temperature range label.
    """
    for min_temp, max_temp, _, label in TEMPERATURE_COLORS:
        if min_temp <= temperature < max_temp:
            return label
    return 'Unknown'


def create_folium_map(
    data: list[dict],
    center: Optional[list[float]] = None,
    zoom: int = DEFAULT_MAP_ZOOM,
    use_clustering: bool = False
) -> folium.Map:
    """Create a Folium map with temperature markers.
    
    Args:
        data: List of weather data dictionaries.
        center: Map center [lat, lon]. Defaults to Taiwan center.
        zoom: Initial zoom level.
        use_clustering: Whether to use marker clustering.
        
    Returns:
        Configured Folium Map object.
    """
    if center is None:
        center = DEFAULT_MAP_CENTER
    
    # Create base map
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles='OpenStreetMap',
        control_scale=True
    )
    
    # Add tile layer options
    folium.TileLayer(
        tiles='CartoDB positron',
        name='Light Mode',
        control=True
    ).add_to(m)
    
    # Create marker group or cluster
    if use_clustering:
        marker_group = MarkerCluster(name='Weather Stations')
    else:
        marker_group = folium.FeatureGroup(name='Weather Stations')
    
    # Add markers for each location
    for record in data:
        try:
            lat = record.get('latitude')
            lon = record.get('longitude')
            temp = record.get('temperature')
            name = record.get('location_name', 'Unknown')
            
            if lat is None or lon is None or temp is None:
                continue
            
            color = get_temperature_color(temp)
            
            # Create popup content
            popup_html = create_popup_html(record)
            popup = folium.Popup(popup_html, max_width=300)
            
            # Create circle marker
            folium.CircleMarker(
                location=[lat, lon],
                radius=10,
                popup=popup,
                tooltip=f"{name}: {temp}°C",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=2
            ).add_to(marker_group)
            
        except Exception as e:
            logger.warning(f"Failed to add marker for {record.get('location_name')}: {e}")
    
    marker_group.add_to(m)
    
    # Add legend
    legend_html = get_legend_html()
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m


def create_popup_html(record: dict) -> str:
    """Create HTML content for marker popup.
    
    Args:
        record: Weather data dictionary.
        
    Returns:
        HTML string for popup.
    """
    name = record.get('location_name', 'Unknown')
    temp = record.get('temperature', 'N/A')
    county = record.get('county_name', '')
    town = record.get('town_name', '')
    weather = record.get('weather_description', '')
    humidity = record.get('humidity')
    wind = record.get('wind_speed')
    obs_time = record.get('observation_time', '')
    
    location_str = f"{county} {town}".strip() or 'Taiwan'
    
    html = f"""
    <div style="font-family: Arial, sans-serif; min-width: 200px;">
        <h4 style="margin: 0 0 10px 0; color: #333;">{name}</h4>
        <p style="margin: 5px 0; color: #666; font-size: 12px;">
            📍 {location_str}
        </p>
        <hr style="margin: 10px 0; border: none; border-top: 1px solid #eee;">
        <p style="margin: 5px 0;">
            <strong style="font-size: 24px; color: {get_temperature_color(temp)};">{temp}°C</strong>
        </p>
    """
    
    if weather:
        html += f'<p style="margin: 5px 0;">🌤️ {weather}</p>'
    
    if humidity is not None:
        html += f'<p style="margin: 5px 0;">💧 濕度: {humidity}%</p>'
    
    if wind is not None:
        html += f'<p style="margin: 5px 0;">💨 風速: {wind} m/s</p>'
    
    if obs_time:
        # Format time for display
        time_display = obs_time.replace('T', ' ').replace('+08:00', '')
        html += f'<p style="margin: 10px 0 0 0; color: #999; font-size: 11px;">更新: {time_display}</p>'
    
    html += "</div>"
    return html


def get_legend_html() -> str:
    """Get HTML for temperature color legend.
    
    Returns:
        HTML string for legend overlay.
    """
    legend_items = ""
    for min_temp, max_temp, color, label in TEMPERATURE_COLORS:
        legend_items += f"""
        <div style="display: flex; align-items: center; margin: 3px 0;">
            <span style="
                background-color: {color};
                width: 20px;
                height: 20px;
                display: inline-block;
                margin-right: 8px;
                border-radius: 50%;
                border: 1px solid #ccc;
            "></span>
            <span style="font-size: 12px;">{label}</span>
        </div>
        """
    
    legend_html = f"""
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        z-index: 1000;
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        font-family: Arial, sans-serif;
    ">
        <h4 style="margin: 0 0 10px 0; font-size: 14px; color: #333;">溫度圖例</h4>
        {legend_items}
    </div>
    """
    return legend_html


def calculate_statistics(data: list[dict]) -> dict:
    """Calculate statistics from weather data.
    
    Args:
        data: List of weather data dictionaries.
        
    Returns:
        Dictionary with statistics.
    """
    if not data:
        return {
            "count": 0,
            "avg_temp": None,
            "min_temp": None,
            "max_temp": None,
            "min_location": None,
            "max_location": None
        }
    
    temps = [(r.get('temperature'), r.get('location_name')) 
             for r in data if r.get('temperature') is not None]
    
    if not temps:
        return {
            "count": len(data),
            "avg_temp": None,
            "min_temp": None,
            "max_temp": None,
            "min_location": None,
            "max_location": None
        }
    
    temp_values = [t[0] for t in temps]
    min_temp, min_loc = min(temps, key=lambda x: x[0])
    max_temp, max_loc = max(temps, key=lambda x: x[0])
    
    return {
        "count": len(data),
        "avg_temp": round(sum(temp_values) / len(temp_values), 1),
        "min_temp": min_temp,
        "max_temp": max_temp,
        "min_location": min_loc,
        "max_location": max_loc
    }


if __name__ == "__main__":
    # Quick test
    print(f"5°C  → {get_temperature_color(5)}")   # Should be #0000FF (Blue)
    print(f"12°C → {get_temperature_color(12)}")  # Should be #00FFFF (Cyan)
    print(f"18°C → {get_temperature_color(18)}")  # Should be #00FF00 (Green)
    print(f"23°C → {get_temperature_color(23)}")  # Should be #FFFF00 (Yellow)
    print(f"27°C → {get_temperature_color(27)}")  # Should be #FFA500 (Orange)
    print(f"35°C → {get_temperature_color(35)}")  # Should be #FF0000 (Red)
