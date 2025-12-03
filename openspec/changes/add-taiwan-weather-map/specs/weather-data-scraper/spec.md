# Specification: Weather Data Scraper

## Overview
A Python-based web scraping component that fetches temperature forecast data from Taiwan's Central Weather Administration (CWA) OpenData platform and transforms it into a structured format for downstream processing.

## ADDED Requirements

### Requirement: The system MUST fetch weather data from CWA OpenData

The system SHALL retrieve temperature forecast data from the CWA OpenData API endpoint.

#### Scenario: Successful data retrieval
**Given** the CWA OpenData API is available at `https://opendata.cwa.gov.tw/dataset/forecast/F-A0010-001`  
**When** the scraper initiates a data fetch request  
**Then** the system should receive a valid HTTP 200 response with weather data  
**And** the response should be stored in memory for processing

#### Scenario: Network timeout handling
**Given** the CWA OpenData API is slow to respond  
**When** the request exceeds 10 seconds  
**Then** the system should timeout the request  
**And** retry up to 3 times with exponential backoff (2s, 4s, 8s)  
**And** log the timeout event

#### Scenario: API unavailable
**Given** the CWA OpenData API returns HTTP 500 or is unreachable  
**When** the scraper attempts to fetch data  
**Then** the system should log the error with timestamp  
**And** return an empty result set  
**And** not crash the application

---

### Requirement: The system MUST parse CWA data format correctly

The system SHALL correctly parse the data format returned by CWA OpenData (XML or JSON).

#### Scenario: Parse XML response
**Given** the CWA API returns data in XML format  
**When** the scraper receives the response  
**Then** the system should parse the XML structure  
**And** extract location names, coordinates, and temperature values  
**And** handle nested XML elements correctly

#### Scenario: Parse JSON response
**Given** the CWA API returns data in JSON format  
**When** the scraper receives the response  
**Then** the system should parse the JSON structure  
**And** extract location names, coordinates, and temperature values  
**And** handle nested JSON objects and arrays

#### Scenario: Invalid data format
**Given** the CWA API returns malformed or unexpected data  
**When** the parser attempts to process the response  
**Then** the system should catch parsing exceptions  
**And** log the error with the raw response snippet  
**And** return an empty result set without crashing

---

### Requirement: The system MUST extract temperature and location data

The system SHALL extract relevant temperature forecast information and geographic coordinates for each location.

#### Scenario: Extract complete data record
**Given** a valid CWA response with weather station data  
**When** the scraper processes a location record  
**Then** the system should extract:
- Location name (Chinese and/or English)
- Latitude (decimal degrees)
- Longitude (decimal degrees)
- Temperature value (numeric)
- Temperature unit (Celsius)
- Forecast timestamp (ISO 8601 format)

#### Scenario: Handle missing coordinates
**Given** a location record without latitude or longitude  
**When** the scraper processes the record  
**Then** the system should skip that record  
**And** log a warning with the location name  
**And** continue processing remaining records

#### Scenario: Handle missing temperature
**Given** a location record without temperature data  
**When** the scraper processes the record  
**Then** the system should skip that record  
**And** log a warning with the location name  
**And** continue processing remaining records

---

### Requirement: The system MUST return structured data

The system SHALL output scraped data in a consistent, structured format for the data processing layer.

#### Scenario: Return list of location dictionaries
**Given** successful parsing of CWA data  
**When** the scraper completes processing  
**Then** the system should return a Python list of dictionaries  
**And** each dictionary should contain keys: `location_name`, `latitude`, `longitude`, `temperature`, `forecast_time`, `unit`  
**And** all numeric values should be properly typed (float for coordinates and temperature)

#### Scenario: Return empty list on failure
**Given** the scraper encounters unrecoverable errors  
**When** processing completes  
**Then** the system should return an empty list `[]`  
**And** log the failure reason  
**And** not return `None` or raise exceptions

---

### Requirement: The system MUST implement logging

The system SHALL log all scraping activities for debugging and monitoring.

#### Scenario: Log successful scrape
**Given** a successful data retrieval and parsing  
**When** the scraper completes  
**Then** the system should log an INFO message with:
- Timestamp
- Number of locations retrieved
- Total execution time

#### Scenario: Log errors and warnings
**Given** any error or warning condition occurs  
**When** the event is detected  
**Then** the system should log with appropriate level (WARNING or ERROR)  
**And** include relevant context (URL, location name, error message)

---

### Requirement: The system MUST handle rate limiting

The system SHALL respect CWA's API usage policies and avoid overwhelming the server.

#### Scenario: Enforce minimum request interval
**Given** the scraper is configured with a minimum request interval (default 60 seconds)  
**When** a new scrape request is initiated  
**Then** the system should check the time since last request  
**And** wait if the interval has not elapsed  
**And** log the wait time

#### Scenario: Prevent concurrent requests
**Given** a scrape operation is in progress  
**When** another scrape request is initiated  
**Then** the system should return the in-progress operation's result or wait for completion  
**And** not initiate duplicate requests

---

## Data Structures

### Scraper Output Format
```python
[
    {
        "location_name": str,      # "台北", "高雄", etc.
        "latitude": float,         # 25.0330
        "longitude": float,        # 121.5654
        "temperature": float,      # 28.5
        "forecast_time": str,      # "2025-12-03T14:00:00+08:00"
        "unit": str                # "C" or "Celsius"
    },
    ...
]
```

## Configuration

### Scraper Configuration Options
- `CWA_API_URL`: Base URL for CWA OpenData (configurable)
- `REQUEST_TIMEOUT`: HTTP request timeout in seconds (default: 10)
- `MAX_RETRIES`: Maximum retry attempts (default: 3)
- `MIN_REQUEST_INTERVAL`: Minimum seconds between requests (default: 60)
- `LOG_LEVEL`: Logging verbosity (default: INFO)

## Dependencies
- `requests>=2.31.0`: HTTP client
- `beautifulsoup4>=4.12.0` or `lxml>=4.9.0`: XML/HTML parsing
- `python-dateutil>=2.8.0`: Date parsing utilities

## Error Handling

### Error Types
1. **NetworkError**: Connection issues, timeouts
2. **ParseError**: Invalid data format, parsing failures
3. **ValidationError**: Missing required fields, invalid data values

### Error Response Strategy
- Always return valid (possibly empty) data structures
- Log all errors with appropriate context
- Use exponential backoff for transient errors
- Fail gracefully without crashing the application

## Testing Requirements

### Unit Tests
- Test XML parsing with sample CWA response
- Test JSON parsing with sample CWA response
- Test error handling with malformed data
- Test retry logic with mocked failures
- Test data extraction with various data scenarios

### Integration Tests
- Test actual CWA API call (rate-limited, not in CI/CD)
- Test end-to-end scraping with real data
- Test concurrent request handling

## Performance Requirements
- Complete scraping operation within 15 seconds under normal conditions
- Support processing at least 100 weather stations
- Memory usage should not exceed 100MB for scraping operations

## Future Enhancements (Out of Scope)
- Support for multiple data types (rainfall, wind speed)
- Asynchronous scraping with asyncio
- Distributed scraping with multiple workers
- Database storage for historical data
