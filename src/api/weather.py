"""Weather API client using OpenWeatherMap."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Weather condition to icon mapping
WEATHER_ICONS = {
    # Clear
    "01d": "☀️",   # clear sky day
    "01n": "🌙",   # clear sky night
    # Clouds
    "02d": "⛅",   # few clouds day
    "02n": "☁️",   # few clouds night
    "03d": "☁️",   # scattered clouds
    "03n": "☁️",
    "04d": "☁️",   # broken clouds
    "04n": "☁️",
    # Rain
    "09d": "🌧️",   # shower rain
    "09n": "🌧️",
    "10d": "🌦️",   # rain day
    "10n": "🌧️",   # rain night
    # Thunderstorm
    "11d": "⛈️",
    "11n": "⛈️",
    # Snow
    "13d": "❄️",
    "13n": "❄️",
    # Mist/Fog
    "50d": "🌫️",
    "50n": "🌫️",
}


@dataclass
class WeatherData:
    """Current weather data."""

    temperature: float  # Fahrenheit
    condition: str      # e.g., "Clear", "Clouds", "Rain"
    icon_code: str      # e.g., "01d", "10n"
    humidity: int       # percentage
    description: str    # e.g., "clear sky", "light rain"
    last_updated: datetime = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

    @property
    def icon(self) -> str:
        """Get emoji icon for weather condition."""
        return WEATHER_ICONS.get(self.icon_code, "🌡️")

    @property
    def temp_display(self) -> str:
        """Get formatted temperature string."""
        return f"{int(round(self.temperature))}°F"


class WeatherClient:
    """Client for fetching weather data from OpenWeatherMap."""

    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(
        self,
        api_key: str,
        latitude: float = 28.3772,   # Walt Disney World
        longitude: float = -81.5707
    ):
        self.api_key = api_key
        self.latitude = latitude
        self.longitude = longitude
        self._cached_data: Optional[WeatherData] = None
        self._last_fetch: Optional[datetime] = None

    def fetch_weather(self) -> Optional[WeatherData]:
        """Fetch current weather data.

        Returns:
            WeatherData object or None if fetch fails
        """
        if not self.api_key:
            logger.warning("Weather API key not configured")
            return self._cached_data

        try:
            params = {
                "lat": self.latitude,
                "lon": self.longitude,
                "appid": self.api_key,
                "units": "imperial"  # Fahrenheit
            }

            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            weather_data = WeatherData(
                temperature=data["main"]["temp"],
                condition=data["weather"][0]["main"],
                icon_code=data["weather"][0]["icon"],
                humidity=data["main"]["humidity"],
                description=data["weather"][0]["description"]
            )

            self._cached_data = weather_data
            self._last_fetch = datetime.now()

            logger.info(
                f"Weather fetched: {weather_data.temp_display}, "
                f"{weather_data.condition}"
            )

            return weather_data

        except requests.RequestException as e:
            logger.error(f"Failed to fetch weather: {e}")
            return self._cached_data
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to parse weather data: {e}")
            return self._cached_data

    @property
    def cached_data(self) -> Optional[WeatherData]:
        """Get cached weather data."""
        return self._cached_data

    @property
    def data_age_minutes(self) -> int:
        """Get age of cached data in minutes."""
        if self._last_fetch is None:
            return -1
        age = datetime.now() - self._last_fetch
        return int(age.total_seconds() / 60)


# Global weather client instance
_weather_client: Optional[WeatherClient] = None


def get_weather_client(
    api_key: str = "",
    latitude: float = 28.3772,
    longitude: float = -81.5707
) -> WeatherClient:
    """Get or create the global WeatherClient instance."""
    global _weather_client
    if _weather_client is None:
        _weather_client = WeatherClient(api_key, latitude, longitude)
    return _weather_client
