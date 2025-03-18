import requests
import csv

# You should store these configuration values in environment variables or a secure vault.
GUACAMOLE_API_ENDPOINT = "http://localhost:8080/guacamole/api"
GUACA_USER = "guacadmin"
GUACA_PASS = "guacadmin"


def get_auth_token():
    resp = requests.post(
        f"{GUACAMOLE_API_ENDPOINT}/tokens",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"username": GUACA_USER, "password": GUACA_PASS},
    )
    if resp and resp.status_code == 200:
        token = resp.json().get("authToken")
        return token


def create_connection_group(token, name, parent_id):
    resp = requests.post(
        f"{GUACAMOLE_API_ENDPOINT}/session/data/postgresql/connectionGroups?token={token}",
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
    return resp.json()


def create_connection(token, parent_id, name):
    data = {
        "parentIdentifier": str(parent_id),
        "name": name,
        "protocol": "ssh",
        "attributes": {
            "guacd-hostname": "guacd",
            "guacd-port": "4822",
            "guacd-encryption": "none",
        },
        "parameters": {
            "hostname": "localhost",
            "username": "guest",
            "password": "guest",
            "port": "22",
        },
    }
    requests.post(
        f"{GUACAMOLE_API_ENDPOINT}/session/data/postgresql/connections?token={token}",
        json=data,
    )


def delete_connection(token, id):
    requests.delete(
        f"{GUACAMOLE_API_ENDPOINT}/session/data/postgresql/connections/{id}?token={token}"
    )


def main():
    auth_token = get_auth_token()

    # Get all existing connection groups from the server
    resp = requests.get(
        f"{GUACAMOLE_API_ENDPOINT}/session/data/postgresql/connectionGroups?token={auth_token}"
    )
    existing_groups = resp.json()

    # Get all existing connections from the server
    resp = requests.get(
        f"{GUACAMOLE_API_ENDPOINT}/session/data/postgresql/connections?token={auth_token}"
    )
    existing_connections = resp.json()

    # Build a tree structure of existing groups
    # The root group has identifier "ROOT"
    group_tree = {"ROOT": {"id": "ROOT", "children": {}, "connections": []}}
    path_to_id = {"ROOT": "ROOT"}  # Maps full paths to group IDs

    # Process existing groups to build the tree
    for group_id, group_info in existing_groups.items():
        parent_id = group_info.get("parentIdentifier", "ROOT")
        name = group_info["name"]

        # Get the parent's full path
        parent_path = None
        for path, id in path_to_id.items():
            if id == parent_id:
                parent_path = path
                break

        if parent_path:
            # Build this group's full path
            if parent_path == "ROOT":
                full_path = name
            else:
                full_path = f"{parent_path}/{name}"

            # Add to our mappings
            path_to_id[full_path] = group_id

            # Add to the tree structure
            current = group_tree["ROOT"]
            if parent_path != "ROOT":
                parts = parent_path.split("/")
                for part in parts:
                    current = current["children"][part]

            if name not in current["children"]:
                current["children"][name] = {
                    "id": group_id,
                    "children": {},
                    "connections": [],
                }

    # Add existing connections to the tree
    for conn_id, conn_info in existing_connections.items():
        parent_id = conn_info.get("parentIdentifier", "ROOT")

        # Find the parent group in our tree
        parent_node = None
        parent_path = None

        for path, id in path_to_id.items():
            if id == parent_id:
                parent_path = path
                break

        if parent_path == "ROOT":
            parent_node = group_tree["ROOT"]
        else:
            # Navigate to the parent node
            parent_node = group_tree["ROOT"]
            parts = parent_path.split("/")
            for part in parts:
                if part in parent_node["children"]:
                    parent_node = parent_node["children"][part]
                else:
                    # If we can't find the parent, skip this connection
                    parent_node = None
                    break

        if parent_node:
            # Add the connection to the parent node
            parent_node["connections"].append(
                {
                    "id": conn_id,
                    "name": conn_info["name"],
                    "protocol": conn_info["protocol"],
                }
            )

    # Read the CSV file
    with open("connections.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Parse the site (group chain)
            site_parts = row["site"].split("/")

            # Start from the root group
            parent_id = "ROOT"
            current_path = ""
            current_node = group_tree["ROOT"]

            # Create or find each group in the chain
            for group_name in site_parts:
                # Build the current path
                if current_path:
                    current_path += f"/{group_name}"
                else:
                    current_path = group_name

                # Check if this path already exists in our mapping
                if current_path in path_to_id:
                    parent_id = path_to_id[current_path]
                    # Navigate to the correct node in our tree
                    if group_name in current_node["children"]:
                        current_node = current_node["children"][group_name]
                    continue

                # Group doesn't exist at this path, create it
                new_group = create_connection_group(auth_token, group_name, parent_id)
                parent_id = new_group.get("identifier")

                # Update our data structures
                path_to_id[current_path] = parent_id
                if group_name not in current_node["children"]:
                    current_node["children"][group_name] = {
                        "id": parent_id,
                        "children": {},
                        "connections": [],
                    }
                current_node = current_node["children"][group_name]

            # Now create the connection in the final group
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
            resp = requests.post(
                f"{GUACAMOLE_API_ENDPOINT}/session/data/postgresql/connections?token={auth_token}",
                json=connection_data,
            )

            # Add the connection to our tree structure
            connection_id = resp.json().get("identifier")
            if connection_id:
                current_node["connections"].append(
                    {
                        "id": connection_id,
                        "name": row["device_name"],
                        "protocol": row["protocol"],
                    }
                )

            print(f"Created connection: {row['device_name']} in group: {row['site']}")

    print("CSV import completed successfully!")

    # Print the tree structure for visualization
    print("\nConnection Group Tree Structure:")
    print_tree(group_tree["ROOT"])


def print_tree(node, indent=0):
    """Helper function to print the tree structure for debugging"""
    # Print connection groups
    for name, child in node["children"].items():
        print("  " * indent + f"- Group: {name} (ID: {child['id']})")
        print_tree(child, indent + 1)

    # Print connections in this group
    for conn in node.get("connections", []):
        print(
            "  " * indent
            + f"  * Connection: {conn['name']} ({conn['protocol']}, ID: {conn['id']})"
        )


if __name__ == "__main__":
    main()
