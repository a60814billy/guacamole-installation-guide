import requests
import logging

# Configure logging
logger = logging.getLogger(__name__)


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
