"""API client for queue-times.com wait times data."""

import logging
from datetime import datetime
from typing import Any, Optional

import requests

from src.models.ride import Park, Ride, WaitTimesData

logger = logging.getLogger(__name__)

# Queue-Times.com API base URL
BASE_URL = "https://queue-times.com/parks/{park_id}/queue_times.json"

# Walt Disney World park configurations
WDW_PARKS = {
    "magic_kingdom": {"id": 6, "name": "Magic Kingdom"},
    "epcot": {"id": 5, "name": "EPCOT"},
    "hollywood_studios": {"id": 7, "name": "Hollywood Studios"},
    "animal_kingdom": {"id": 8, "name": "Animal Kingdom"},
}


class QueueTimesClient:
    """Client for fetching wait times from queue-times.com."""

    def __init__(
        self,
        timeout: int = 10,
        max_retries: int = 3,
        retry_delay: int = 30,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Cache for storing last successful fetch
        self._cache: Optional[WaitTimesData] = None

    @property
    def cached_data(self) -> Optional[WaitTimesData]:
        """Return cached data if available."""
        return self._cache

    def fetch_park(self, park_slug: str) -> Optional[Park]:
        """Fetch wait times for a single park.

        Args:
            park_slug: Park identifier (e.g., 'magic_kingdom')

        Returns:
            Park object with rides, or None on failure
        """
        if park_slug not in WDW_PARKS:
            logger.error(f"Unknown park: {park_slug}")
            return None

        park_config = WDW_PARKS[park_slug]
        park_id = park_config["id"]
        park_name = park_config["name"]
        url = BASE_URL.format(park_id=park_id)

        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            rides = self._parse_rides(data, park_id, park_name)

            return Park(
                id=park_id,
                name=park_name,
                slug=park_slug,
                rides=rides,
                last_updated=datetime.now(),
            )

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout fetching {park_name}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error fetching {park_name}: {e}")
        except (ValueError, KeyError) as e:
            logger.warning(f"Parse error for {park_name}: {e}")

        return None

    def _parse_rides(
        self, data: dict[str, Any], park_id: int, park_name: str
    ) -> list[Ride]:
        """Parse ride data from API response.

        The API returns data structured as:
        {
            "lands": [
                {
                    "name": "Land Name",
                    "rides": [
                        {"id": 123, "name": "Ride Name", "wait_time": 45, "is_open": true},
                        ...
                    ]
                },
                ...
            ]
        }
        """
        rides = []

        lands = data.get("lands", [])
        for land in lands:
            land_rides = land.get("rides", [])
            for ride_data in land_rides:
                ride = Ride(
                    id=ride_data.get("id", 0),
                    name=ride_data.get("name", "Unknown"),
                    wait_time=ride_data.get("wait_time", 0) or 0,
                    is_open=ride_data.get("is_open", False),
                    park_id=park_id,
                    park_name=park_name,
                )
                rides.append(ride)

        return rides

    def fetch_all_parks(self) -> WaitTimesData:
        """Fetch wait times for all Walt Disney World parks.

        Returns:
            WaitTimesData containing all parks and rides
        """
        result = WaitTimesData()
        success_count = 0

        for park_slug in WDW_PARKS:
            park = self.fetch_park(park_slug)
            if park:
                result.parks[park_slug] = park
                success_count += 1
                logger.info(
                    f"Fetched {park.name}: {len(park.open_rides)} open rides"
                )

        result.last_fetch = datetime.now()
        result.fetch_success = success_count > 0

        if not result.fetch_success:
            result.error_message = "Failed to fetch data from all parks"
            logger.error(result.error_message)

            # Return cached data if available
            if self._cache:
                logger.info("Returning cached data due to fetch failure")
                return self._cache
        else:
            # Update cache on successful fetch
            self._cache = result
            total_rides = len(result.all_open_rides)
            logger.info(f"Successfully fetched {total_rides} open rides total")

        return result

    def get_wait_times(self, use_cache: bool = True) -> WaitTimesData:
        """Get wait times, using cache if appropriate.

        Args:
            use_cache: If True and cache is fresh, return cached data

        Returns:
            WaitTimesData with current wait times
        """
        # If we have fresh cached data, return it
        if use_cache and self._cache and not self._cache.is_stale:
            logger.debug("Returning fresh cached data")
            return self._cache

        # Otherwise fetch new data
        return self.fetch_all_parks()
