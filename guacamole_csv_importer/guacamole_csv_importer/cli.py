"""Command-line interface for Guacamole CSV Importer.

This module provides a command-line interface for importing connections from CSV files
into Apache Guacamole.
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

from .importer import ConnectionImporter
from .api_client import GuacamoleAPIClient
from . import __version__


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration.

    Args:
        verbose: Whether to enable verbose logging
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(level=log_level, format=log_format)

    # Reduce verbosity of requests library
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Import connections from CSV files into Apache Guacamole"
    )

    parser.add_argument(
        "csv_file",
        type=Path,
        help="Path to the CSV file containing connection data",
    )

    parser.add_argument(
        "--url",
        required=False,
        help="Base URL of the Guacamole API (e.g., 'http://localhost:8080/guacamole/api')",
    )

    parser.add_argument(
        "--username",
        "-u",
        required=False,
        help="Guacamole admin username",
    )

    parser.add_argument(
        "--password",
        "-p",
        required=False,
        help="Guacamole admin password",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"Guacamole CSV Importer {__version__}",
    )

    return parser.parse_args(args)


def build_api_client(parsed_args: argparse.Namespace) -> GuacamoleAPIClient:
    """Build an API client from parsed arguments."""
    url = parsed_args.url or os.getenv("GUACAMOLE_URL")
    username = parsed_args.username or os.getenv("GUACAMOLE_USERNAME")
    password = parsed_args.password or os.getenv("GUACAMOLE_PASSWORD")

    if not url or not username or not password:
        raise ValueError(
            "You must provide Apache Guacamole API URL, username, and password via arguments or environment variables"
        )

    return GuacamoleAPIClient(url, username, password)


def main(args: Optional[List[str]] = None) -> int:
    """Run the Guacamole CSV Importer.

    Args:
        args: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    load_dotenv()
    parsed_args = parse_args(args)
    setup_logging(parsed_args.verbose)

    logger = logging.getLogger(__name__)
    logger.info(f"Guacamole CSV Importer {__version__}")

    try:
        # Validate CSV file
        if not parsed_args.csv_file.exists():
            logger.error(f"CSV file not found: {parsed_args.csv_file}")
            return 1

        guacamole_api_client = build_api_client(parsed_args)

        # Create importer
        importer = ConnectionImporter(guacamole_api_client)

        # Import connections
        successful, total = importer.import_connections(parsed_args.csv_file)

        # Report results
        if successful == total:
            logger.info(f"Successfully imported all {total} connections")
            return 0
        elif successful > 0:
            logger.warning(f"Imported {successful}/{total} connections")
            return 0
        else:
            logger.error("Failed to import any connections")
            return 1

    except Exception as e:
        logger.exception(f"Error importing connections: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
