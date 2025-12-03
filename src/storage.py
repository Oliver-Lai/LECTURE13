"""SQLite storage module for weather data persistence."""

import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeatherDatabase:
    """SQLite database manager for weather data.
    
    This class handles all database operations including:
    - Schema initialization
    - Data insertion with upsert logic
    - Query operations
    - Data cleanup and retention
    """
    
    def __init__(self, db_path: str = "data/weather.db"):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: Optional[sqlite3.Connection] = None
        self._init_db()
    
    @property
    def connection(self) -> sqlite3.Connection:
        """Get database connection, creating if necessary."""
        if self._connection is None:
            self._connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False
            )
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor with automatic commit/rollback."""
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()
    
    def _init_db(self):
        """Initialize database schema."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS weather_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            temperature REAL NOT NULL,
            unit TEXT DEFAULT 'C',
            observation_time TEXT NOT NULL,
            county_name TEXT,
            town_name TEXT,
            weather_description TEXT,
            humidity REAL,
            wind_speed REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        create_indexes_sql = [
            """CREATE UNIQUE INDEX IF NOT EXISTS idx_location_observation 
               ON weather_records(location_name, observation_time);""",
            """CREATE INDEX IF NOT EXISTS idx_created_at 
               ON weather_records(created_at);""",
            """CREATE INDEX IF NOT EXISTS idx_observation_time 
               ON weather_records(observation_time);"""
        ]
        
        with self.get_cursor() as cursor:
            cursor.execute(create_table_sql)
            for index_sql in create_indexes_sql:
                cursor.execute(index_sql)
        
        logger.info(f"Database initialized at {self.db_path}")
    
    def save_weather_data(self, data: list[dict]) -> int:
        """Save weather data to database with upsert logic.
        
        Args:
            data: List of weather data dictionaries.
            
        Returns:
            Number of records saved/updated.
        """
        if not data:
            return 0
        
        upsert_sql = """
        INSERT INTO weather_records (
            location_name, latitude, longitude, temperature, unit,
            observation_time, county_name, town_name, weather_description,
            humidity, wind_speed, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(location_name, observation_time) DO UPDATE SET
            latitude = excluded.latitude,
            longitude = excluded.longitude,
            temperature = excluded.temperature,
            unit = excluded.unit,
            county_name = excluded.county_name,
            town_name = excluded.town_name,
            weather_description = excluded.weather_description,
            humidity = excluded.humidity,
            wind_speed = excluded.wind_speed,
            updated_at = CURRENT_TIMESTAMP;
        """
        
        saved_count = 0
        with self.get_cursor() as cursor:
            for record in data:
                try:
                    cursor.execute(upsert_sql, (
                        record.get("location_name"),
                        record.get("latitude"),
                        record.get("longitude"),
                        record.get("temperature"),
                        record.get("unit", "C"),
                        record.get("observation_time"),
                        record.get("county_name"),
                        record.get("town_name"),
                        record.get("weather_description"),
                        record.get("humidity"),
                        record.get("wind_speed")
                    ))
                    saved_count += 1
                except sqlite3.Error as e:
                    logger.warning(f"Failed to save record for {record.get('location_name')}: {e}")
        
        logger.info(f"Saved {saved_count} records to database")
        return saved_count
    
    def get_latest_data(self) -> list[dict]:
        """Get the most recent observation for each location.
        
        Returns:
            List of weather data dictionaries for latest observations.
        """
        query = """
        SELECT * FROM weather_records w1
        WHERE observation_time = (
            SELECT MAX(observation_time) 
            FROM weather_records w2 
            WHERE w2.location_name = w1.location_name
        )
        ORDER BY location_name;
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_data_by_location(self, location: str) -> list[dict]:
        """Get all records for a specific location.
        
        Args:
            location: Location name to query.
            
        Returns:
            List of weather data dictionaries.
        """
        query = """
        SELECT * FROM weather_records
        WHERE location_name = ?
        ORDER BY observation_time DESC;
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, (location,))
            rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_data_by_time_range(
        self, 
        start_time: str, 
        end_time: str
    ) -> list[dict]:
        """Get records within a time range.
        
        Args:
            start_time: Start time (ISO format).
            end_time: End time (ISO format).
            
        Returns:
            List of weather data dictionaries.
        """
        query = """
        SELECT * FROM weather_records
        WHERE observation_time BETWEEN ? AND ?
        ORDER BY observation_time DESC, location_name;
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, (start_time, end_time))
            rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """Remove records older than specified days.
        
        Args:
            days: Number of days to retain data.
            
        Returns:
            Number of records deleted.
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        delete_sql = """
        DELETE FROM weather_records
        WHERE created_at < ?;
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(delete_sql, (cutoff_date,))
            deleted_count = cursor.rowcount
        
        logger.info(f"Cleaned up {deleted_count} old records (older than {days} days)")
        return deleted_count
    
    def get_statistics(self) -> dict:
        """Get database statistics.
        
        Returns:
            Dictionary with statistics.
        """
        with self.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as total FROM weather_records")
            total = cursor.fetchone()["total"]
            
            cursor.execute("SELECT COUNT(DISTINCT location_name) as locations FROM weather_records")
            locations = cursor.fetchone()["locations"]
            
            cursor.execute("SELECT MIN(observation_time) as oldest, MAX(observation_time) as newest FROM weather_records")
            row = cursor.fetchone()
        
        return {
            "total_records": total,
            "unique_locations": locations,
            "oldest_record": row["oldest"],
            "newest_record": row["newest"]
        }
    
    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")


if __name__ == "__main__":
    # Quick test
    from src.scraper import fetch_weather_data
    
    db = WeatherDatabase("data/weather.db")
    
    try:
        # Fetch and save data
        data = fetch_weather_data()
        saved = db.save_weather_data(data)
        print(f"Saved {saved} records")
        
        # Get latest data
        latest = db.get_latest_data()
        print(f"Retrieved {len(latest)} latest records")
        
        # Get statistics
        stats = db.get_statistics()
        print(f"Statistics: {stats}")
        
    finally:
        db.close()
