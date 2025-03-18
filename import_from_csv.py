import requests

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

    resp = requests.get(
        f"{GUACAMOLE_API_ENDPOINT}/session/data/postgresql/connectionGroups?token={auth_token}"
    )

    # Should read all group from guacamole server to build the group tree.

    # read the csv file.

    # the Site is the groups chain, use slash to separate the groups.
    # e.g. "DC1/Rack10" is a group named Rack10 under a group named DC1.
    # and the connection should put the Rack10

    # Create the connection in the group.


if __name__ == "__main__":
    main()
