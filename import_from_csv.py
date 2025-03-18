import requests
import csv

# You should store these configuration values in environment variables or a secure vault.
GUACAMOLE_API_ENDPOINT = "http://10.192.4.173/api"
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

    # Build a dictionary of existing groups with name as key and identifier as value
    # The root group has identifier "ROOT"
    group_dict = {"ROOT": "ROOT"}
    for group_id, group_info in existing_groups.items():
        group_dict[group_info["name"]] = group_id

    # Dictionary to track created groups by their full path
    created_groups = {}

    # Read the CSV file
    with open("connections.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Parse the site (group chain)
            site_parts = row["site"].split("/")

            # Start from the root group
            parent_id = "ROOT"
            current_path = ""

            # Create or find each group in the chain
            for i, group_name in enumerate(site_parts):
                # Build the current path
                if current_path:
                    current_path += f"/{group_name}"
                else:
                    current_path = group_name

                # Check if this group already exists in our tracking dictionary
                if current_path in created_groups:
                    parent_id = created_groups[current_path]
                    continue

                # Check if this group exists on the server
                if group_name in group_dict:
                    # Group exists, use its ID
                    parent_id = group_dict[group_name]
                    created_groups[current_path] = parent_id
                else:
                    # Group doesn't exist, create it
                    new_group = create_connection_group(
                        auth_token, group_name, parent_id
                    )
                    parent_id = new_group.get("identifier")
                    group_dict[group_name] = parent_id
                    created_groups[current_path] = parent_id

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
                    "port": "22",
                },
            }

            # Create the connection
            requests.post(
                f"{GUACAMOLE_API_ENDPOINT}/session/data/postgresql/connections?token={auth_token}",
                json=connection_data,
            )
            print(f"Created connection: {row['device_name']} in group: {row['site']}")

    print("CSV import completed successfully!")


if __name__ == "__main__":
    main()
