import os
import csv
import logging
import argparse
from dotenv import load_dotenv
from src.connection_group_tree import ConnectionGroupTree
from src.guacamole_api import GuacamoleAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """
    Main function to process the CSV file and create connections in Guacamole.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Import connections from CSV file to Guacamole"
    )
    parser.add_argument(
        "--csv",
        type=str,
        default="connections.csv",
        help="Path to the CSV file (default: connections.csv)",
    )
    args = parser.parse_args()

    # Load environment variables from .env file
    load_dotenv()

    # Get configuration from environment variables
    api_endpoint = os.getenv("GUACAMOLE_API_ENDPOINT")
    username = os.getenv("GUACA_USER")
    password = os.getenv("GUACA_PASS")

    if not all([api_endpoint, username, password]):
        logger.error("Missing required environment variables. Check your .env file.")
        return

    # Initialize the Guacamole API
    api = GuacamoleAPI(api_endpoint, username, password)
    if not api.authenticate():
        logger.error("Failed to authenticate with Guacamole API")
        return

    # Get existing data from Guacamole
    existing_groups = api.get_connection_groups()
    existing_connections = api.get_connections()

    # Initialize the connection group tree
    tree = ConnectionGroupTree()
    tree.build_from_data(existing_groups, existing_connections)

    # Process the CSV file
    try:
        with open(args.csv, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Parse the site (group chain)
                site_path = row["site"]

                # Start from the root group
                parent_id = "ROOT"
                current_path = ""

                # Process each part of the site path
                site_parts = site_path.split("/")
                for group_name in site_parts:
                    # Build the current path
                    if current_path:
                        current_path += f"/{group_name}"
                    else:
                        current_path = group_name

                    # Check if this path already exists
                    if current_path in tree.path_to_id:
                        parent_id = tree.path_to_id[current_path]
                        continue

                    # Group doesn't exist, create it
                    new_group = api.create_connection_group(group_name, parent_id)
                    if not new_group:
                        logger.error(
                            f"Failed to create group: {group_name} under {parent_id}"
                        )
                        continue

                    parent_id = new_group.get("identifier")

                    # Update our tree
                    tree.add_group(
                        parent_id,
                        group_name,
                        parent_id if parent_id != "ROOT" else "ROOT",
                    )
                    tree.path_to_id[current_path] = parent_id

                # Create the connection in the final group
                connection_data = {
                    "parentIdentifier": str(parent_id),
                    "name": row["device_name"],
                    "protocol": row["protocol"],
                    "attributes": {
                        "guacd-hostname": "guacd",
                        "guacd-port": "4822",
                        "guacd-encryption": "none",
                    },
                    "parameters": {
                        "hostname": row["hostname"],
                        "username": row["username"],
                        "password": row["password"],
                        "port": row.get("port", "22"),
                    },
                }

                # Create the connection
                connection_id = api.create_connection(connection_data)
                if connection_id:
                    # Add to our tree
                    tree.add_connection(
                        connection_id, row["device_name"], row["protocol"], parent_id
                    )
                    logger.info(
                        f"Created connection: {row['device_name']} in group: {row['site']}"
                    )
                else:
                    logger.error(f"Failed to create connection: {row['device_name']}")

        logger.info(f"CSV import from {args.csv} completed successfully!")

        # Print the tree structure for visualization
        tree.print_tree()

        # Example of using the get_group_id_by_site method
        site_id = "AIN"
        group_id = tree.get_group_id_by_site(site_id)
        if group_id:
            logger.info(f"Group ID for site '{site_id}': {group_id}")
        else:
            logger.info(f"No group found for site '{site_id}'")

    except FileNotFoundError:
        logger.error(f"CSV file not found: {args.csv}")
    except Exception as e:
        logger.error(f"Error processing CSV file: {e}")


if __name__ == "__main__":
    main()
