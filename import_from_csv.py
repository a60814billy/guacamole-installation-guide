import requests
import csv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# You should store these configuration values in environment variables or a secure vault.
GUACAMOLE_API_ENDPOINT = "http://10.192.4.173:8080/guacamole/api"
GUACA_USER = "guacadmin"
GUACA_PASS = "guacadmin"


class ConnectionGroupTree:
    """
    A class to manage a tree structure of connection groups and connections.
    This class is decoupled from any API or external system.
    """

    def __init__(self):
        """Initialize an empty connection group tree with a ROOT node."""
        self.group_tree = {"ROOT": {"id": "ROOT", "children": {}, "connections": []}}
        self.path_to_id = {"ROOT": "ROOT"}  # Maps full paths to group IDs

    def add_group(self, group_id, name, parent_id="ROOT"):
        """
        Add a group to the tree structure.

        Args:
            group_id (str): The identifier for the group
            name (str): The name of the group
            parent_id (str): The identifier of the parent group (default: "ROOT")

        Returns:
            bool: True if the group was added successfully, False otherwise
        """
        try:
            # Find the parent node
            parent_node = self._find_node_by_id(parent_id)
            if not parent_node:
                logger.warning(f"Parent node with ID {parent_id} not found")
                return False

            # Add the group to the parent's children
            if name not in parent_node["children"]:
                parent_node["children"][name] = {
                    "id": group_id,
                    "children": {},
                    "connections": [],
                }

                # Update path_to_id mapping
                parent_path = self._get_path_by_id(parent_id)
                if parent_path == "ROOT":
                    full_path = name
                else:
                    full_path = f"{parent_path}/{name}"
                self.path_to_id[full_path] = group_id

                return True
            else:
                # Group with this name already exists at this level
                logger.info(f"Group '{name}' already exists under parent {parent_id}")
                return False
        except Exception as e:
            logger.error(f"Error adding group: {e}")
            return False

    def add_connection(self, connection_id, name, protocol, parent_id="ROOT"):
        """
        Add a connection to a specific group.

        Args:
            connection_id (str): The identifier for the connection
            name (str): The name of the connection
            protocol (str): The protocol used by the connection
            parent_id (str): The identifier of the parent group (default: "ROOT")

        Returns:
            bool: True if the connection was added successfully, False otherwise
        """
        try:
            # Find the parent node
            parent_node = self._find_node_by_id(parent_id)
            if not parent_node:
                logger.warning(f"Parent node with ID {parent_id} not found")
                return False

            # Add the connection to the parent's connections
            parent_node["connections"].append(
                {"id": connection_id, "name": name, "protocol": protocol}
            )

            return True
        except Exception as e:
            logger.error(f"Error adding connection: {e}")
            return False

    def get_group_id_by_path(self, path):
        """
        Return group ID for a given path.

        Args:
            path (str): The path to look up (e.g., "AIN/DC1/Rack10")

        Returns:
            str: The group ID if found, None otherwise
        """
        return self.path_to_id.get(path)

    def get_group_id_by_site(self, site_id):
        """
        Get the group ID corresponding to a site ID.

        A site ID is considered to be the first part of a path.
        For example, in "AIN/DC1/Rack10", the site ID is "AIN".

        Args:
            site_id (str): The site ID to look up

        Returns:
            str: The group ID if found, None otherwise
        """
        # First check if the site_id exists as a direct path
        if site_id in self.path_to_id:
            return self.path_to_id[site_id]

        # Otherwise, look for paths that start with the site_id
        for path, group_id in self.path_to_id.items():
            parts = path.split("/")
            if parts and parts[0] == site_id:
                # Return the ID of the top-level group matching the site ID
                return self.path_to_id.get(site_id)

        return None

    def get_parent_id_for_path(self, path, create_missing=False):
        """
        Get the parent ID for a given path, optionally creating parent groups if needed.

        Args:
            path (str): The path to process (e.g., "AIN/DC1/Rack10")
            create_missing (bool): Whether to create missing groups in the tree

        Returns:
            str: The parent ID for the given path
        """
        if not path:
            return "ROOT"

        # Check if the path already exists
        if path in self.path_to_id:
            return self.path_to_id[path]

        # Split the path into parts
        parts = path.split("/")

        # Start from the root
        parent_id = "ROOT"
        current_path = ""
        current_node = self.group_tree["ROOT"]

        # Process each part of the path
        for i, part in enumerate(parts):
            # Build the current path
            if current_path:
                current_path += f"/{part}"
            else:
                current_path = part

            # Check if this path already exists
            if current_path in self.path_to_id:
                parent_id = self.path_to_id[current_path]
                # Navigate to the correct node
                if part in current_node["children"]:
                    current_node = current_node["children"][part]
                continue

            # If we're not creating missing groups, return None
            if not create_missing:
                return None

            # Generate a new ID for this group (in a real implementation, this would be handled differently)
            new_id = f"generated_{current_path.replace('/', '_')}"

            # Add the group to our tree
            self.add_group(new_id, part, parent_id)

            # Update our tracking variables
            parent_id = new_id
            if part in current_node["children"]:
                current_node = current_node["children"][part]

        return parent_id

    def build_from_data(self, groups_data, connections_data):
        """
        Build the tree from external data sources.

        Args:
            groups_data (dict): Dictionary of group data from an external source
            connections_data (dict): Dictionary of connection data from an external source

        Returns:
            bool: True if the tree was built successfully, False otherwise
        """
        try:
            # Process groups to build the tree
            for group_id, group_info in groups_data.items():
                parent_id = group_info.get("parentIdentifier", "ROOT")
                name = group_info["name"]

                # Get the parent's full path
                parent_path = self._get_path_by_id(parent_id)

                # Build this group's full path
                if parent_path == "ROOT":
                    full_path = name
                else:
                    full_path = f"{parent_path}/{name}"

                # Add to our mappings
                self.path_to_id[full_path] = group_id

                # Add to the tree structure
                self.add_group(group_id, name, parent_id)

            # Add connections to the tree
            for conn_id, conn_info in connections_data.items():
                parent_id = conn_info.get("parentIdentifier", "ROOT")
                name = conn_info["name"]
                protocol = conn_info["protocol"]

                self.add_connection(conn_id, name, protocol, parent_id)

            return True
        except Exception as e:
            logger.error(f"Error building tree from data: {e}")
            return False

    def print_tree(self, node=None, indent=0):
        """
        Print the tree structure for visualization.

        Args:
            node (dict): The node to start printing from (default: ROOT)
            indent (int): The indentation level (default: 0)
        """
        if node is None:
            node = self.group_tree["ROOT"]
            print("\nConnection Group Tree Structure:")

        # Print connection groups
        for name, child in node["children"].items():
            print("  " * indent + f"- Group: {name} (ID: {child['id']})")
            self.print_tree(child, indent + 1)

        # Print connections in this group
        for conn in node.get("connections", []):
            print(
                "  " * indent
                + f"  * Connection: {conn['name']} ({conn['protocol']}, ID: {conn['id']})"
            )

    def _find_node_by_id(self, node_id):
        """
        Find a node in the tree by its ID.

        Args:
            node_id (str): The ID of the node to find

        Returns:
            dict: The node if found, None otherwise
        """
        if node_id == "ROOT":
            return self.group_tree["ROOT"]

        # Helper function for recursive search
        def search_node(node):
            # Check children
            for child in node["children"].values():
                if child["id"] == node_id:
                    return child

                # Recursively search in this child
                result = search_node(child)
                if result:
                    return result

            return None

        return search_node(self.group_tree["ROOT"])

    def _get_path_by_id(self, node_id):
        """
        Get the full path for a node by its ID.

        Args:
            node_id (str): The ID of the node

        Returns:
            str: The full path if found, None otherwise
        """
        if node_id == "ROOT":
            return "ROOT"

        for path, id in self.path_to_id.items():
            if id == node_id:
                return path

        return None


class GuacamoleAPI:
    """
    A class to handle interactions with the Guacamole API.
    """

    def __init__(self, api_endpoint, username, password):
        """
        Initialize the GuacamoleAPI with connection details.

        Args:
            api_endpoint (str): The base URL for the Guacamole API
            username (str): The username for authentication
            password (str): The password for authentication
        """
        self.api_endpoint = api_endpoint
        self.username = username
        self.password = password
        self.auth_token = None

    def authenticate(self):
        """
        Authenticate with the Guacamole API and get an auth token.

        Returns:
            str: The authentication token if successful, None otherwise
        """
        try:
            resp = requests.post(
                f"{self.api_endpoint}/tokens",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={"username": self.username, "password": self.password},
            )

            if resp and resp.status_code == 200:
                self.auth_token = resp.json().get("authToken")
                return self.auth_token
            else:
                logger.error(f"Authentication failed: {resp.status_code} - {resp.text}")
                return None
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return None

    def create_connection_group(self, name, parent_id):
        """
        Create a connection group in Guacamole.

        Args:
            name (str): The name of the group
            parent_id (str): The ID of the parent group

        Returns:
            dict: The response data if successful, None otherwise
        """
        try:
            if not self.auth_token:
                logger.error("Not authenticated. Call authenticate() first.")
                return None

            resp = requests.post(
                f"{self.api_endpoint}/session/data/postgresql/connectionGroups?token={self.auth_token}",
                json={
                    "parentIdentifier": str(parent_id),
                    "name": name,
                    "type": "ORGANIZATIONAL",
                    "attributes": {
                        "max-connections": "",
                        "max-connections-per-user": "",
                        "enable-session-affinity": "",
                    },
                },
            )

            if resp and resp.status_code == 200:
                return resp.json()
            else:
                logger.error(
                    f"Failed to create connection group: {resp.status_code} - {resp.text}"
                )
                return None
        except Exception as e:
            logger.error(f"Error creating connection group: {e}")
            return None

    def create_connection(self, connection_data):
        """
        Create a connection in Guacamole.

        Args:
            connection_data (dict): The connection data

        Returns:
            str: The connection ID if successful, None otherwise
        """
        try:
            if not self.auth_token:
                logger.error("Not authenticated. Call authenticate() first.")
                return None

            resp = requests.post(
                f"{self.api_endpoint}/session/data/postgresql/connections?token={self.auth_token}",
                json=connection_data,
            )

            if resp and resp.status_code == 200:
                return resp.json().get("identifier")
            else:
                logger.error(
                    f"Failed to create connection: {resp.status_code} - {resp.text}"
                )
                return None
        except Exception as e:
            logger.error(f"Error creating connection: {e}")
            return None

    def delete_connection(self, connection_id):
        """
        Delete a connection from Guacamole.

        Args:
            connection_id (str): The ID of the connection to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.auth_token:
                logger.error("Not authenticated. Call authenticate() first.")
                return False

            resp = requests.delete(
                f"{self.api_endpoint}/session/data/postgresql/connections/{connection_id}?token={self.auth_token}"
            )

            if resp and resp.status_code == 204:
                return True
            else:
                logger.error(
                    f"Failed to delete connection: {resp.status_code} - {resp.text}"
                )
                return False
        except Exception as e:
            logger.error(f"Error deleting connection: {e}")
            return False

    def get_connection_groups(self):
        """
        Get all connection groups from Guacamole.

        Returns:
            dict: The connection groups if successful, empty dict otherwise
        """
        try:
            if not self.auth_token:
                logger.error("Not authenticated. Call authenticate() first.")
                return {}

            resp = requests.get(
                f"{self.api_endpoint}/session/data/postgresql/connectionGroups?token={self.auth_token}"
            )

            if resp and resp.status_code == 200:
                return resp.json()
            else:
                logger.error(
                    f"Failed to get connection groups: {resp.status_code} - {resp.text}"
                )
                return {}
        except Exception as e:
            logger.error(f"Error getting connection groups: {e}")
            return {}

    def get_connections(self):
        """
        Get all connections from Guacamole.

        Returns:
            dict: The connections if successful, empty dict otherwise
        """
        try:
            if not self.auth_token:
                logger.error("Not authenticated. Call authenticate() first.")
                return {}

            resp = requests.get(
                f"{self.api_endpoint}/session/data/postgresql/connections?token={self.auth_token}"
            )

            if resp and resp.status_code == 200:
                return resp.json()
            else:
                logger.error(
                    f"Failed to get connections: {resp.status_code} - {resp.text}"
                )
                return {}
        except Exception as e:
            logger.error(f"Error getting connections: {e}")
            return {}


def main():
    """
    Main function to process the CSV file and create connections in Guacamole.
    """
    # Initialize the Guacamole API
    api = GuacamoleAPI(GUACAMOLE_API_ENDPOINT, GUACA_USER, GUACA_PASS)
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
        with open("connections.csv", "r") as csvfile:
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

        logger.info("CSV import completed successfully!")

        # Print the tree structure for visualization
        tree.print_tree()

        # Example of using the get_group_id_by_site method
        site_id = "AIN"
        group_id = tree.get_group_id_by_site(site_id)
        if group_id:
            logger.info(f"Group ID for site '{site_id}': {group_id}")
        else:
            logger.info(f"No group found for site '{site_id}'")

    except Exception as e:
        logger.error(f"Error processing CSV file: {e}")


if __name__ == "__main__":
    main()
