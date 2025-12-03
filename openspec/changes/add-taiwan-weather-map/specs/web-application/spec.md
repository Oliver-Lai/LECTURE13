# Specification: Web Application (Streamlit)

## Overview
A Streamlit-based web application that provides the user interface for the Taiwan weather temperature map, integrating data fetching, storage, and visualization components into a unified Python application.

## ADDED Requirements

### Requirement: The system MUST provide a Streamlit application entry point

The system SHALL create a main Streamlit application file that serves as the entry point for the web application.

#### Scenario: Launch Streamlit application locally
**Given** the user has installed all dependencies  
**When** the user runs `streamlit run app.py`  
**Then** the Streamlit server should start on port 8501 (default)  
**And** the browser should automatically open to the application  
**And** the application should display the Taiwan weather map interface

#### Scenario: Configure page settings
**Given** the Streamlit application loads  
**When** the page initializes  
**Then** the page title should be "Taiwan Weather Map"  
**And** the layout should be set to "wide" for optimal map display  
**And** the page icon should be displayed (temperature emoji)

---

### Requirement: The system MUST implement session state for data caching

The system SHALL use Streamlit's session state to cache weather data and avoid unnecessary API calls.

#### Scenario: Initialize session state
**Given** a user opens the application for the first time  
**When** the session starts  
**Then** `st.session_state.weather_data` should be initialized to None  
**And** `st.session_state.last_update` should be initialized to None

#### Scenario: Cache data after fetch
**Given** weather data is successfully fetched  
**When** the data is received  
**Then** the data should be stored in `st.session_state.weather_data`  
**And** the current timestamp should be stored in `st.session_state.last_update`

#### Scenario: Use cached data on rerun
**Given** weather data exists in session state  
**When** the page reruns (user interaction)  
**Then** the system should use the cached data  
**And** not trigger a new API call  
**And** display the cached last update time

---

### Requirement: The system MUST provide a sidebar with controls and statistics

The system SHALL display controls, statistics, and legend in the Streamlit sidebar.

#### Scenario: Display refresh button
**Given** the application is running  
**When** the sidebar renders  
**Then** a "Refresh Data" button should be visible  
**And** clicking it should trigger a new data fetch

#### Scenario: Display statistics
**Given** weather data is loaded  
**When** the sidebar renders  
**Then** the sidebar should show:
- Number of locations with data
- Average temperature across all locations
- Highest temperature with location name
- Lowest temperature with location name

#### Scenario: Display last update time
**Given** data has been fetched  
**When** the sidebar renders  
**Then** the last update timestamp should be displayed  
**And** formatted in a readable format (e.g., "Dec 3, 2025 2:30 PM")

---

### Requirement: The system MUST handle loading states

The system SHALL provide visual feedback during data loading operations.

#### Scenario: Show loading spinner
**Given** a data fetch operation begins  
**When** the system is waiting for the response  
**Then** a loading spinner should be displayed  
**And** the message "Loading weather data..." should appear

#### Scenario: Remove spinner on completion
**Given** a loading spinner is displayed  
**When** the data fetch completes (success or failure)  
**Then** the spinner should be removed  
**And** the appropriate content should be displayed

---

### Requirement: The system MUST handle errors gracefully

The system SHALL display user-friendly error messages and provide recovery options.

#### Scenario: Display error on fetch failure
**Given** the weather data fetch fails  
**When** the error is caught  
**Then** an error message should be displayed using `st.error()`  
**And** the message should be user-friendly (not technical details)

#### Scenario: Provide retry option
**Given** an error has occurred  
**When** the error is displayed  
**Then** a "Retry" button should be available  
**And** clicking it should attempt to fetch data again

---

## User Interface Layout

```
┌────────────────────────────────────────────────────────┐
│  🌡️ Taiwan Weather Temperature Map              [⟳]   │
├──────────────┬─────────────────────────────────────────┤
│   Sidebar    │                                         │
│              │                                         │
│ [Refresh]    │                                         │
│              │         Folium Map                      │
│ Statistics   │         (Interactive)                   │
│ ├ Locations  │                                         │
│ ├ Avg Temp   │                                         │
│ ├ Highest    │                                         │
│ └ Lowest     │                                         │
│              │                                         │
│ Last Update  │                                         │
│ Dec 3, 2:30  │                                         │
│              │                                         │
│ Legend       │                                         │
│ ├ 🔵 <10°C   │                                         │
│ ├ 🔷 10-15   │                                         │
│ ├ 🟢 15-20   │                                         │
│ ├ 🟡 20-25   │                                         │
│ ├ 🟠 25-30   │                                         │
│ └ 🔴 >30°C   │                                         │
└──────────────┴─────────────────────────────────────────┘
```

## Dependencies
- `streamlit>=1.28.0`: Web application framework
- `streamlit-folium>=0.15.0`: Folium integration for Streamlit

## Configuration

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
```
