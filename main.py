#!/usr/bin/env python3
"""Disney World Wait Times Display - Main Entry Point."""

import argparse
import sys
import threading
import time
from pathlib import Path

import yaml

from src.utils.logging_config import setup_logging, get_logger
from src.api.queue_times import QueueTimesClient
from src.api.weather import WeatherClient
from src.display.renderer import DisplayConfig, RideDisplay
from src.data.database import get_database
from src.web.server import run_server as run_web_server
from src.events.scheduler import EventScheduler


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    path = Path(config_path)
    if not path.exists():
        return {}

    with open(path) as f:
        return yaml.safe_load(f) or {}


def print_text_summary(data):
    """Print text-only summary of wait times (for --text-only mode)."""
    print("\n" + "=" * 60)
    print("DISNEY WORLD WAIT TIMES")
    print("=" * 60)

    for park_slug, park in data.parks.items():
        print(f"\n{park.name}")
        print("-" * 40)

        open_rides = park.open_rides
        if not open_rides:
            print("  No rides currently reporting wait times")
            continue

        for ride in sorted(open_rides, key=lambda r: -r.wait_time):
            print(f"  {ride.name}: {ride.display_wait}")

    total = len(data.all_open_rides)
    print(f"\n{'=' * 60}")
    print(f"Total open rides: {total}")
    if data.last_fetch:
        print(f"Data fetched at: {data.last_fetch.strftime('%I:%M %p')}")
    print("=" * 60 + "\n")


def create_data_refresh_thread(client, display, interval, logger, database=None):
    """Create a background thread that periodically refreshes data.

    Args:
        client: QueueTimesClient instance
        display: RideDisplay instance
        interval: Refresh interval in seconds
        logger: Logger instance
        database: Optional WaitTimesDatabase instance for storing history
    """

    def refresh_loop():
        consecutive_failures = 0
        max_failures = 5

        while display.running:
            time.sleep(interval)
            if not display.running:
                break

            logger.info("Refreshing wait times data...")
            try:
                data = client.fetch_all_parks()
                if data.fetch_success:
                    display.set_rides(data)
                    logger.info(
                        f"Wait times refreshed: {len(data.all_open_rides)} rides"
                    )
                    consecutive_failures = 0

                    # Store in database if available
                    if database:
                        database.store_wait_times(data.all_open_rides)
                        # Periodic cleanup
                        database.cleanup_old_data()
                else:
                    consecutive_failures += 1
                    logger.warning(
                        f"Failed to refresh data (attempt {consecutive_failures})"
                    )

                    if consecutive_failures >= max_failures:
                        logger.error(
                            f"Data refresh failed {max_failures} times in a row"
                        )

            except Exception as e:
                consecutive_failures += 1
                logger.error(f"Error refreshing data: {e}")

    thread = threading.Thread(target=refresh_loop, daemon=True, name="DataRefresh")
    return thread


def create_weather_refresh_thread(weather_client, display, interval, logger):
    """Create a background thread that periodically refreshes weather data.

    Args:
        weather_client: WeatherClient instance
        display: RideDisplay instance
        interval: Refresh interval in seconds
        logger: Logger instance
    """

    def refresh_loop():
        while display.running:
            time.sleep(interval)
            if not display.running:
                break

            try:
                weather = weather_client.fetch_weather()
                if weather:
                    display.set_weather(weather)
                    logger.debug(f"Weather refreshed: {weather.temp_display}")
            except Exception as e:
                logger.error(f"Error refreshing weather: {e}")

    thread = threading.Thread(target=refresh_loop, daemon=True, name="WeatherRefresh")
    return thread


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="Disney World Wait Times Display",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run with GUI
  python main.py --fullscreen       # Fullscreen mode (for Pi)
  python main.py --text-only        # Print wait times to console
        """,
    )
    parser.add_argument(
        "--text-only",
        action="store_true",
        help="Print text summary only, no GUI",
    )
    parser.add_argument(
        "--fullscreen",
        action="store_true",
        help="Run in fullscreen mode",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to config file (default: config.yaml)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="Override log level from config",
    )
    parser.add_argument(
        "--no-console-log",
        action="store_true",
        help="Disable console logging (log to file only)",
    )
    parser.add_argument(
        "--test-event",
        choices=["fireworks", "fireworks-epcot", "parade"],
        help="Test event animation (fireworks, fireworks-epcot, or parade)",
    )
    args = parser.parse_args()

    # Load configuration first
    config = load_config(args.config)

    # Setup logging
    log_config = config.get("logging", {})
    log_level = args.log_level or log_config.get("level", "INFO")
    log_file = log_config.get("file", "waitimes.log")

    setup_logging(
        log_file=log_file,
        level=log_level,
        console=not args.no_console_log,
    )

    logger = get_logger(__name__)
    logger.info("Disney Wait Times Display starting...")
    logger.info(f"Configuration loaded from {args.config}")

    # Initialize API client
    api_config = config.get("api", {})
    client = QueueTimesClient(
        timeout=api_config.get("timeout", 10),
        max_retries=api_config.get("max_retries", 3),
        retry_delay=api_config.get("retry_delay", 30),
    )

    # Fetch initial wait times
    logger.info("Fetching wait times from queue-times.com...")
    data = client.fetch_all_parks()

    if not data.fetch_success:
        logger.error("Failed to fetch initial wait times")
        if not args.text_only:
            print("Error: Could not fetch wait times. Check network connection.")
        return 1

    logger.info(f"Fetched {len(data.all_open_rides)} open rides")

    # Text-only mode
    if args.text_only:
        print_text_summary(data)
        return 0

    # GUI mode
    display_config = config.get("display", {})
    rotation_config = config.get("rotation", {})

    disp_cfg = DisplayConfig(
        width=display_config.get("width", 800),
        height=display_config.get("height", 480),
        fullscreen=args.fullscreen or display_config.get("fullscreen", False),
        fps=display_config.get("fps", 30),
        display_duration=rotation_config.get("display_duration", 8.0),
        transition_duration=rotation_config.get("transition_duration", 0.5),
    )

    display = RideDisplay(disp_cfg)

    if not display.setup():
        logger.error("Failed to initialize display")
        return 1

    try:
        # Initialize database for historical data
        db_config = config.get("database", {})
        database = None
        if db_config.get("path"):
            database = get_database(
                db_path=db_config.get("path", "data/waitimes.db"),
                retention_days=db_config.get("retention_days", 30)
            )
            # Store initial data
            database.store_wait_times(data.all_open_rides)
            logger.info("Database initialized for historical data")

        # Start background data refresh thread
        refresh_interval = api_config.get("refresh_interval", 300)
        display.running = True  # Set before starting refresh thread
        refresh_thread = create_data_refresh_thread(
            client, display, refresh_interval, logger, database
        )
        refresh_thread.start()
        logger.info(f"Data refresh thread started (interval: {refresh_interval}s)")

        # Initialize weather if enabled
        weather_config = config.get("weather", {})
        if weather_config.get("enabled", False) and weather_config.get("api_key"):
            weather_client = WeatherClient(
                api_key=weather_config.get("api_key", ""),
                latitude=weather_config.get("latitude", 28.3772),
                longitude=weather_config.get("longitude", -81.5707),
            )

            # Fetch initial weather
            weather = weather_client.fetch_weather()
            if weather:
                display.set_weather(weather)
                logger.info(f"Initial weather: {weather.temp_display}, {weather.condition}")

            # Start weather refresh thread
            weather_interval = weather_config.get("refresh_interval", 1800)
            weather_thread = create_weather_refresh_thread(
                weather_client, display, weather_interval, logger
            )
            weather_thread.start()
            logger.info(f"Weather refresh thread started (interval: {weather_interval}s)")
        else:
            logger.info("Weather display disabled (no API key configured)")

        # Initialize event scheduler for fireworks/parades
        events_config = config.get("events", {})

        # Load video paths for events
        video_paths = {}
        videos_dir = Path("assets/videos")
        video_mappings = {
            "magic-kingdom_fireworks": "mk_fireworks.mp4",
            "epcot_fireworks": "epcot_fireworks.mp4",
            "magic-kingdom_parade": "mk_parade.mp4",
        }
        for key, filename in video_mappings.items():
            video_path = videos_dir / filename
            if video_path.exists():
                video_paths[key] = str(video_path)
                logger.info(f"Found event video: {key}")

        # Test event mode - create immediate event
        if args.test_event:
            from datetime import datetime, timedelta
            from src.events.scheduler import ScheduledEvent, EventType
            test_time = datetime.now() - timedelta(seconds=1)  # Started 1 second ago

            # Determine event type and park
            if args.test_event == "fireworks-epcot":
                event_type = EventType.FIREWORKS
                park_name = "EPCOT"
                park_slug = "epcot"
                duration = 240
            elif args.test_event == "fireworks":
                event_type = EventType.FIREWORKS
                park_name = "Magic Kingdom"
                park_slug = "magic-kingdom"
                duration = 240
            else:  # parade
                event_type = EventType.PARADE
                park_name = "Magic Kingdom"
                park_slug = "magic-kingdom"
                duration = 120

            test_event = ScheduledEvent(
                event_type=event_type,
                park_name=park_name,
                park_slug=park_slug,
                start_time=test_time.time(),
                duration_seconds=duration,
            )
            # Create minimal scheduler with test event
            test_scheduler = EventScheduler({})
            test_scheduler.events = [test_event]
            display.set_event_scheduler(test_scheduler, video_paths)
            logger.info(f"TEST MODE: {args.test_event} animation active")
        elif events_config.get("fireworks", {}).get("enabled") or events_config.get("parades", {}).get("enabled"):
            event_scheduler = EventScheduler(events_config)
            display.set_event_scheduler(event_scheduler, video_paths)
            logger.info("Event scheduler initialized for fireworks/parades")
        else:
            logger.info("Special events disabled (no events configured)")

        # Start web dashboard if enabled
        web_config = config.get("web", {})
        if web_config.get("enabled", False) and database:
            run_web_server(
                host=web_config.get("host", "0.0.0.0"),
                port=web_config.get("port", 8080),
                database=database
            )

        # Run main display loop
        logger.info("Entering main display loop")
        display.run_loop(data)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1
    finally:
        display.shutdown()
        logger.info("Application shutdown complete")

    return 0


if __name__ == "__main__":
    sys.exit(main())
