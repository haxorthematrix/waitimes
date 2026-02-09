"""SQLite database for historical wait time data."""

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class WaitTimesDatabase:
    """SQLite database for storing historical wait time data."""

    def __init__(self, db_path: str = "data/waitimes.db", retention_days: int = 30):
        self.db_path = Path(db_path)
        self.retention_days = retention_days

        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Get a database connection with context manager."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Wait times table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wait_times (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    ride_id INTEGER NOT NULL,
                    ride_name TEXT NOT NULL,
                    park_name TEXT NOT NULL,
                    wait_time INTEGER NOT NULL,
                    is_open BOOLEAN NOT NULL DEFAULT 1
                )
            """)

            # Create indexes for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_wait_times_timestamp
                ON wait_times(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_wait_times_ride
                ON wait_times(ride_name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_wait_times_park
                ON wait_times(park_name)
            """)

            # Weather table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS weather (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    temperature REAL NOT NULL,
                    condition TEXT NOT NULL,
                    humidity INTEGER,
                    description TEXT
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_weather_timestamp
                ON weather(timestamp)
            """)

            conn.commit()
            logger.info(f"Database initialized: {self.db_path}")

    def store_wait_times(self, rides: list):
        """Store current wait times for all rides.

        Args:
            rides: List of Ride objects
        """
        if not rides:
            return

        timestamp = datetime.now()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            for ride in rides:
                cursor.execute("""
                    INSERT INTO wait_times
                    (timestamp, ride_id, ride_name, park_name, wait_time, is_open)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    timestamp,
                    ride.id,
                    ride.name,
                    ride.park_name,
                    ride.wait_time,
                    ride.is_open
                ))

            conn.commit()
            logger.debug(f"Stored {len(rides)} wait time records")

    def store_weather(self, temperature: float, condition: str,
                      humidity: int = None, description: str = None):
        """Store weather data.

        Args:
            temperature: Temperature in Fahrenheit
            condition: Weather condition (e.g., "Clear", "Rain")
            humidity: Humidity percentage
            description: Weather description
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO weather
                (timestamp, temperature, condition, humidity, description)
                VALUES (?, ?, ?, ?, ?)
            """, (datetime.now(), temperature, condition, humidity, description))
            conn.commit()

    def get_current_waits(self) -> list[dict]:
        """Get the most recent wait times for all rides.

        Returns:
            List of dicts with ride info and wait times
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get the most recent timestamp
            cursor.execute("""
                SELECT MAX(timestamp) as latest FROM wait_times
            """)
            row = cursor.fetchone()
            if not row or not row['latest']:
                return []

            latest = row['latest']

            # Get all rides at that timestamp
            cursor.execute("""
                SELECT ride_name, park_name, wait_time, is_open, timestamp
                FROM wait_times
                WHERE timestamp = ?
                ORDER BY park_name, wait_time DESC
            """, (latest,))

            return [dict(row) for row in cursor.fetchall()]

    def get_ride_history(self, ride_name: str, hours: int = 24) -> list[dict]:
        """Get wait time history for a specific ride.

        Args:
            ride_name: Name of the ride
            hours: Number of hours of history to fetch

        Returns:
            List of dicts with timestamp and wait_time
        """
        since = datetime.now() - timedelta(hours=hours)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, wait_time
                FROM wait_times
                WHERE ride_name = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            """, (ride_name, since))

            return [dict(row) for row in cursor.fetchall()]

    def get_park_history(self, park_name: str, hours: int = 24) -> list[dict]:
        """Get average wait time history for a park.

        Args:
            park_name: Name of the park
            hours: Number of hours of history

        Returns:
            List of dicts with timestamp and avg_wait
        """
        since = datetime.now() - timedelta(hours=hours)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, AVG(wait_time) as avg_wait, COUNT(*) as ride_count
                FROM wait_times
                WHERE park_name = ? AND timestamp >= ? AND is_open = 1
                GROUP BY timestamp
                ORDER BY timestamp ASC
            """, (park_name, since))

            return [dict(row) for row in cursor.fetchall()]

    def get_ride_stats(self, ride_name: str, days: int = 7) -> dict:
        """Get statistics for a specific ride.

        Args:
            ride_name: Name of the ride
            days: Number of days to analyze

        Returns:
            Dict with min, max, avg wait times
        """
        since = datetime.now() - timedelta(days=days)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    MIN(wait_time) as min_wait,
                    MAX(wait_time) as max_wait,
                    AVG(wait_time) as avg_wait,
                    COUNT(*) as data_points
                FROM wait_times
                WHERE ride_name = ? AND timestamp >= ? AND is_open = 1
            """, (ride_name, since))

            row = cursor.fetchone()
            if row:
                return {
                    'min_wait': row['min_wait'] or 0,
                    'max_wait': row['max_wait'] or 0,
                    'avg_wait': round(row['avg_wait'] or 0, 1),
                    'data_points': row['data_points'] or 0
                }
            return {'min_wait': 0, 'max_wait': 0, 'avg_wait': 0, 'data_points': 0}

    def get_all_rides(self) -> list[str]:
        """Get list of all unique ride names in database.

        Returns:
            List of ride names
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT ride_name FROM wait_times ORDER BY ride_name
            """)
            return [row['ride_name'] for row in cursor.fetchall()]

    def get_all_parks(self) -> list[str]:
        """Get list of all unique park names in database.

        Returns:
            List of park names
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT park_name FROM wait_times ORDER BY park_name
            """)
            return [row['park_name'] for row in cursor.fetchall()]

    def cleanup_old_data(self):
        """Remove data older than retention period."""
        cutoff = datetime.now() - timedelta(days=self.retention_days)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM wait_times WHERE timestamp < ?
            """, (cutoff,))
            wait_deleted = cursor.rowcount

            cursor.execute("""
                DELETE FROM weather WHERE timestamp < ?
            """, (cutoff,))
            weather_deleted = cursor.rowcount

            conn.commit()

            if wait_deleted > 0 or weather_deleted > 0:
                logger.info(
                    f"Cleaned up old data: {wait_deleted} wait records, "
                    f"{weather_deleted} weather records"
                )

    def get_database_stats(self) -> dict:
        """Get database statistics.

        Returns:
            Dict with record counts and date ranges
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM wait_times")
            wait_count = cursor.fetchone()['count']

            cursor.execute("SELECT MIN(timestamp) as oldest, MAX(timestamp) as newest FROM wait_times")
            row = cursor.fetchone()
            oldest = row['oldest']
            newest = row['newest']

            return {
                'wait_records': wait_count,
                'oldest_record': oldest,
                'newest_record': newest,
                'db_path': str(self.db_path),
                'retention_days': self.retention_days
            }


# Global database instance
_database: Optional[WaitTimesDatabase] = None


def get_database(db_path: str = "data/waitimes.db", retention_days: int = 30) -> WaitTimesDatabase:
    """Get or create the global database instance."""
    global _database
    if _database is None:
        _database = WaitTimesDatabase(db_path, retention_days)
    return _database
