"""Weather data scraper for CWA OpenData API."""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import requests

from .config import CWA_API_BASE_URL, get_cwa_api_key

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CWA API endpoints
STATION_OBSERVATION_ENDPOINT = "O-A0003-001"  # 即時觀測
WEEKLY_FORECAST_ENDPOINT = "F-D0047-091"  # 一週縣市預報（含經緯度）


@dataclass
class WeatherData:
    """Data class for weather observation."""
    
    location_name: str
    latitude: float
    longitude: float
    temperature: float
    unit: str
    observation_time: str
    county_name: str
    town_name: str
    weather_description: str
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None


def fetch_weather_data(
    max_retries: int = 3,
    timeout: int = 10,
    base_delay: float = 1.0
) -> list[dict]:
    """Fetch weather data from CWA OpenData API.
    
    Args:
        max_retries: Maximum number of retry attempts.
        timeout: Request timeout in seconds.
        base_delay: Base delay for exponential backoff.
        
    Returns:
        List of weather data dictionaries.
        
    Raises:
        requests.RequestException: If all retries fail.
    """
    api_key = get_cwa_api_key()
    url = f"{CWA_API_BASE_URL}/{STATION_OBSERVATION_ENDPOINT}"
    params = {
        "Authorization": api_key,
        "format": "JSON"
    }
    
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching weather data (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("success") != "true":
                raise ValueError(f"API returned unsuccessful response: {data}")
            
            weather_data = parse_weather_response(data)
            logger.info(f"Successfully fetched {len(weather_data)} weather records")
            return weather_data
            
        except requests.Timeout as e:
            last_exception = e
            logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries})")
        except requests.RequestException as e:
            last_exception = e
            logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
        except (ValueError, KeyError) as e:
            last_exception = e
            logger.error(f"Failed to parse response: {e}")
            raise
        
        # Exponential backoff
        if attempt < max_retries - 1:
            delay = base_delay * (2 ** attempt)
            logger.info(f"Retrying in {delay:.1f} seconds...")
            time.sleep(delay)
    
    logger.error(f"All {max_retries} attempts failed")
    raise last_exception or requests.RequestException("All retries failed")


def parse_weather_response(response_data: dict) -> list[dict]:
    """Parse CWA API response and extract weather data.
    
    Args:
        response_data: Raw API response dictionary.
        
    Returns:
        List of parsed weather data dictionaries.
    """
    weather_list = []
    
    stations = response_data.get("records", {}).get("Station", [])
    
    for station in stations:
        try:
            parsed = parse_station_data(station)
            if parsed:
                weather_list.append(parsed)
        except Exception as e:
            station_name = station.get("StationName", "Unknown")
            logger.warning(f"Failed to parse station '{station_name}': {e}")
            continue
    
    return weather_list


def parse_station_data(station: dict) -> Optional[dict]:
    """Parse individual station data.
    
    Args:
        station: Station data dictionary from API response.
        
    Returns:
        Parsed weather data dictionary or None if invalid.
    """
    station_name = station.get("StationName")
    if not station_name:
        return None
    
    # Get coordinates (use WGS84)
    geo_info = station.get("GeoInfo", {})
    coordinates = geo_info.get("Coordinates", [])
    
    lat, lon = None, None
    for coord in coordinates:
        if coord.get("CoordinateName") == "WGS84":
            lat = _safe_float(coord.get("StationLatitude"))
            lon = _safe_float(coord.get("StationLongitude"))
            break
    
    # Fallback to first available coordinates
    if lat is None and coordinates:
        lat = _safe_float(coordinates[0].get("StationLatitude"))
        lon = _safe_float(coordinates[0].get("StationLongitude"))
    
    if lat is None or lon is None:
        logger.debug(f"Station '{station_name}' has no valid coordinates")
        return None
    
    # Get weather elements
    weather_element = station.get("WeatherElement", {})
    temperature = _safe_float(weather_element.get("AirTemperature"))
    
    if temperature is None:
        logger.debug(f"Station '{station_name}' has no temperature data")
        return None
    
    # Get observation time
    obs_time = station.get("ObsTime", {}).get("DateTime", "")
    
    return {
        "location_name": station_name,
        "latitude": lat,
        "longitude": lon,
        "temperature": temperature,
        "unit": "C",
        "observation_time": obs_time,
        "county_name": geo_info.get("CountyName", ""),
        "town_name": geo_info.get("TownName", ""),
        "weather_description": weather_element.get("Weather", ""),
        "humidity": _safe_float(weather_element.get("RelativeHumidity")),
        "wind_speed": _safe_float(weather_element.get("WindSpeed"))
    }


def _safe_float(value) -> Optional[float]:
    """Safely convert value to float.
    
    Args:
        value: Value to convert.
        
    Returns:
        Float value or None if conversion fails.
    """
    if value is None or value == "" or value == "-99":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def fetch_weekly_forecast(
    max_retries: int = 3,
    timeout: int = 15,
    base_delay: float = 1.0
) -> dict:
    """Fetch one-week weather forecast from CWA.
    
    Returns:
        Dictionary with 'dates' list and 'by_date' mapping.
    """
    api_key = get_cwa_api_key()
    url = f"{CWA_API_BASE_URL}/{WEEKLY_FORECAST_ENDPOINT}"
    params = {"Authorization": api_key, "format": "JSON"}
    
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching weekly forecast (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") != "true":
                raise ValueError(f"API unsuccessful: {data}")
            
            forecast = parse_weekly_forecast(data)
            logger.info(f"Fetched forecast for {len(forecast.get('dates', []))} time slots")
            return forecast
            
        except requests.Timeout as e:
            last_exception = e
            logger.warning(f"Timeout (attempt {attempt + 1}/{max_retries})")
        except requests.RequestException as e:
            last_exception = e
            logger.warning(f"Request failed: {e}")
        except Exception as e:
            logger.error(f"Parse error: {e}")
            raise
        
        if attempt < max_retries - 1:
            time.sleep(base_delay * (2 ** attempt))
    
    raise last_exception or requests.RequestException("All retries failed")


def parse_weekly_forecast(data: dict) -> dict:
    """Parse F-D0047-091 response into structured format."""
    result = {"dates": [], "by_date": {}}
    
    try:
        locations_data = data.get("records", {}).get("Locations", [])
        if not locations_data:
            return result
        
        locations = locations_data[0].get("Location", [])
        all_times = set()
        
        for loc in locations:
            location_name = loc.get("LocationName", "")
            lat = _safe_float(loc.get("Latitude"))
            lon = _safe_float(loc.get("Longitude"))
            
            if not location_name or lat is None or lon is None:
                continue
            
            elements = loc.get("WeatherElement", [])
            temp_elem = next((e for e in elements if e.get("ElementName") == "平均溫度"), None)
            wx_elem = next((e for e in elements if e.get("ElementName") == "天氣現象"), None)
            
            if not temp_elem:
                continue
            
            temp_times = temp_elem.get("Time", [])
            wx_times = wx_elem.get("Time", []) if wx_elem else []
            
            for i, t in enumerate(temp_times):
                start_time = t.get("StartTime", "")
                if not start_time:
                    continue
                
                # Parse time
                try:
                    dt = datetime.fromisoformat(start_time.replace("+08:00", ""))
                    time_key = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    time_key = start_time[:16]
                
                all_times.add(time_key)
                
                # Get temperature
                temp = None
                for ev in t.get("ElementValue", []):
                    temp = _safe_float(ev.get("Temperature"))
                    if temp is not None:
                        break
                
                if temp is None:
                    continue
                
                # Get weather description
                weather = ""
                if i < len(wx_times):
                    for wv in wx_times[i].get("ElementValue", []):
                        if wv.get("Weather"):
                            weather = wv.get("Weather", "")
                            break
                
                record = {
                    "location_name": location_name,
                    "latitude": lat,
                    "longitude": lon,
                    "temperature": temp,
                    "unit": "C",
                    "forecast_time": start_time,
                    "weather_description": weather,
                    "county_name": location_name,
                    "town_name": ""
                }
                
                if time_key not in result["by_date"]:
                    result["by_date"][time_key] = []
                result["by_date"][time_key].append(record)
        
        result["dates"] = sorted(list(all_times))
        
    except Exception as e:
        logger.error(f"Failed to parse forecast: {e}")
    
    return result


def get_forecast_dates(forecast: dict) -> list[str]:
    """Get sorted list of forecast dates/times."""
    return forecast.get("dates", [])


def get_forecast_by_date(forecast: dict, date_key: str) -> list[dict]:
    """Get forecast data for a specific date/time."""
    return forecast.get("by_date", {}).get(date_key, [])


if __name__ == "__main__":
    # Quick test
    try:
        print("=== Real-time Data ===")
        data = fetch_weather_data()
        print(f"Retrieved {len(data)} stations")
        
        print("\n=== Weekly Forecast ===")
        forecast = fetch_weekly_forecast()
        dates = get_forecast_dates(forecast)
        print(f"Time slots: {len(dates)}")
        print(f"First 3: {dates[:3]}")
        if dates:
            first = get_forecast_by_date(forecast, dates[0])
            print(f"Locations in first slot: {len(first)}")
            if first:
                print(f"Sample: {first[0]}")
    except Exception as e:
        print(f"Error: {e}")
