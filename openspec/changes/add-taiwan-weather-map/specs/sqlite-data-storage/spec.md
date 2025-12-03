# Specification: SQLite Data Storage

## Overview
A Python-based data persistence layer that stores weather data scraped from CWA OpenData into a SQLite database. This enables historical data tracking, offline access, and efficient querying of past weather records.

## ADDED Requirements

### Requirement: The system MUST store weather data in SQLite database

The system SHALL persist all scraped weather data into a SQLite database for historical tracking and offline access.

#### Scenario: Initialize database on first run
**Given** the application starts for the first time  
**When** the database file does not exist  
**Then** the system should create a new SQLite database file at `data/weather.db`  
**And** create the required tables with proper schema  
**And** log the database initialization

#### Scenario: Successful data insertion
**Given** the scraper returns valid weather data  
**When** the data is received for storage  
**Then** the system should insert each location record into the database  
**And** include a timestamp for when the record was stored  
**And** log the number of records inserted

#### Scenario: Handle duplicate records
**Given** weather data for the same location and forecast time already exists  
**When** new data with the same location and forecast time is received  
**Then** the system should update the existing record with the new temperature value  
**And** update the `updated_at` timestamp  
**And** not create duplicate entries

---

### Requirement: The system MUST define a proper database schema

The system SHALL use a well-defined database schema that supports efficient queries and data integrity.

#### Scenario: Create weather_records table
**Given** the database is being initialized  
**When** the schema is created  
**Then** the system should create a `weather_records` table with columns:
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `location_name` (TEXT NOT NULL)
- `latitude` (REAL NOT NULL)
- `longitude` (REAL NOT NULL)
- `temperature` (REAL NOT NULL)
- `unit` (TEXT DEFAULT 'C')
- `forecast_time` (TEXT NOT NULL)
- `created_at` (TEXT DEFAULT CURRENT_TIMESTAMP)
- `updated_at` (TEXT DEFAULT CURRENT_TIMESTAMP)

#### Scenario: Create appropriate indexes
**Given** the database is being initialized  
**When** the schema is created  
**Then** the system should create indexes on:
- `location_name`
- `forecast_time`
- `created_at`
- Composite index on `(location_name, forecast_time)` for uniqueness

---

### Requirement: The system MUST support querying historical data

The system SHALL provide functions to query stored weather data for analysis and display.

#### Scenario: Query latest data for all locations
**Given** weather data exists in the database  
**When** the API requests current weather data  
**Then** the system should return the most recent record for each location  
**And** format the result as a list of dictionaries matching the scraper output format

#### Scenario: Query data by time range
**Given** weather data exists in the database  
**When** a query is made with `start_time` and `end_time` parameters  
**Then** the system should return all records within the specified time range  
**And** order results by `forecast_time` ascending

#### Scenario: Query data by location
**Given** weather data exists in the database  
**When** a query is made with a `location_name` parameter  
**Then** the system should return all records for that specific location  
**And** order results by `forecast_time` descending

#### Scenario: Query returns empty result
**Given** no weather data matches the query criteria  
**When** a query is executed  
**Then** the system should return an empty list `[]`  
**And** not raise any exceptions

---

### Requirement: The system MUST handle database errors gracefully

The system SHALL handle all database operations with proper error handling to maintain application stability.

#### Scenario: Handle connection failure
**Given** the database file cannot be accessed (permissions, disk full, etc.)  
**When** a database operation is attempted  
**Then** the system should catch the exception  
**And** log the error with details  
**And** return appropriate fallback values (empty list for queries, False for inserts)  
**And** not crash the application

#### Scenario: Handle write failures
**Given** a database insert or update operation fails  
**When** the error occurs  
**Then** the system should rollback any partial transaction  
**And** log the error with the affected data  
**And** continue processing remaining data if applicable

#### Scenario: Handle concurrent access
**Given** multiple processes may access the database  
**When** concurrent operations occur  
**Then** the system should use appropriate locking mechanisms (SQLite's built-in)  
**And** set a reasonable timeout for acquiring locks (30 seconds)  
**And** log warnings if lock contention occurs

---

### Requirement: The system MUST implement data cleanup

The system SHALL provide mechanisms to manage database size and remove old data.

#### Scenario: Delete records older than retention period
**Given** a retention period is configured (default: 30 days)  
**When** the cleanup function is called  
**Then** the system should delete all records where `created_at` is older than the retention period  
**And** log the number of records deleted  
**And** optionally run VACUUM to reclaim disk space

#### Scenario: Manual data export
**Given** historical data exists in the database  
**When** an export is requested  
**Then** the system should export data to CSV or JSON format  
**And** allow filtering by date range or location  
**And** return the export file path

---

## Data Structures

### Database Schema
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

CREATE INDEX IF NOT EXISTS idx_location_name ON weather_records(location_name);
CREATE INDEX IF NOT EXISTS idx_forecast_time ON weather_records(forecast_time);
CREATE INDEX IF NOT EXISTS idx_created_at ON weather_records(created_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_location_forecast ON weather_records(location_name, forecast_time);
```

### Storage Module Interface
```python
class WeatherDatabase:
    def __init__(self, db_path: str = "data/weather.db"):
        """Initialize database connection and create schema if needed."""
    
    def save_weather_data(self, data: list[dict]) -> int:
        """Save weather data to database. Returns number of records saved."""
    
    def get_latest_data(self) -> list[dict]:
        """Get the most recent record for each location."""
    
    def get_data_by_time_range(self, start_time: str, end_time: str) -> list[dict]:
        """Get all records within the specified time range."""
    
    def get_data_by_location(self, location_name: str) -> list[dict]:
        """Get all records for a specific location."""
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """Delete records older than specified days. Returns deleted count."""
    
    def export_to_csv(self, file_path: str, **filters) -> str:
        """Export data to CSV file. Returns the file path."""
    
    def close(self):
        """Close database connection."""
```

## Configuration

### Storage Configuration Options
- `DB_PATH`: Path to SQLite database file (default: `data/weather.db`)
- `DATA_RETENTION_DAYS`: Number of days to keep data (default: 30)
- `DB_TIMEOUT`: Database lock timeout in seconds (default: 30)
- `AUTO_VACUUM`: Whether to run VACUUM after cleanup (default: False)

## Dependencies
- `sqlite3`: Python standard library (no additional installation required)

## Error Handling

### Error Types
1. **ConnectionError**: Cannot open or create database file
2. **IntegrityError**: Constraint violation (duplicate records)
3. **OperationalError**: Lock timeout, disk full, etc.
4. **DatabaseError**: General database errors

### Error Response Strategy
- Log all errors with context (operation type, affected data)
- Use transactions for data integrity
- Rollback failed transactions
- Return appropriate fallback values
- Never let database errors crash the application

## Testing Requirements

### Unit Tests
- Test database initialization and schema creation
- Test data insertion with valid data
- Test duplicate handling (upsert logic)
- Test query functions with various filters
- Test error handling with mocked failures
- Test cleanup functionality

### Integration Tests
- Test full flow: scrape → store → query
- Test concurrent access from multiple threads
- Test database file persistence across restarts
- Test large dataset handling (1000+ records)

## Performance Requirements
- Database operations should complete within 1 second for typical loads (<100 records)
- Support storing at least 100,000 records without significant performance degradation
- Query operations should use indexes for optimal performance

## Future Enhancements (Out of Scope)
- Migration to PostgreSQL or other database for production
- Real-time replication or backup
- Complex analytics queries
- Data compression for large datasets
