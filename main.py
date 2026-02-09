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
from src.display.renderer import DisplayConfig, RideDisplay


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


def create_data_refresh_thread(client, display, interval, logger):
    """Create a background thread that periodically refreshes data.

    Args:
        client: QueueTimesClient instance
        display: RideDisplay instance
        interval: Refresh interval in seconds
        logger: Logger instance
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
        # Start background data refresh thread
        refresh_interval = api_config.get("refresh_interval", 300)
        display.running = True  # Set before starting refresh thread
        refresh_thread = create_data_refresh_thread(
            client, display, refresh_interval, logger
        )
        refresh_thread.start()
        logger.info(f"Data refresh thread started (interval: {refresh_interval}s)")

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
