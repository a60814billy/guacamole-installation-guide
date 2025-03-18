# Refactoring Plan for import_from_csv.py

## Overview
This document outlines the plan for refactoring the import_from_csv.py script to abstract the connection group tree into a class and add functionality to get a group ID from a site ID.

## Current Code Analysis
The current script:
1. Manages Guacamole connections and connection groups via API calls
2. Builds a tree structure of connection groups
3. Processes a CSV file to create connections in the appropriate groups
4. Uses a dictionary-based approach to track the connection group hierarchy

## Refactoring Plan

### 1. Create a Pure ConnectionGroupTree Class
Create a class that only manages the tree structure without any API dependencies:

```python
class ConnectionGroupTree:
    def __init__(self):
        self.group_tree = {"ROOT": {"id": "ROOT", "children": {}, "connections": []}}
        self.path_to_id = {"ROOT": "ROOT"}  # Maps full paths to group IDs
        
    def add_group(self, group_id, name, parent_id="ROOT"):
        # Add a group to the tree structure
        
    def add_connection(self, connection_id, name, protocol, parent_id="ROOT"):
        # Add a connection to a specific group
        
    def get_group_id_by_path(self, path):
        # Return group ID for a given path
        
    def get_group_id_by_site(self, site_id):
        # Return group ID for a given site ID
        # This will implement the requested functionality
        
    def get_parent_id_for_path(self, path):
        # Get the parent ID for a given path, creating parent groups if needed
        
    def build_from_data(self, groups_data, connections_data):
        # Build the tree from external data sources
        
    def print_tree(self):
        # Print the tree structure for visualization
```

### 2. Create a Separate GuacamoleAPI Class
This class will handle all API interactions independently:

```python
class GuacamoleAPI:
    def __init__(self, api_endpoint, username, password):
        self.api_endpoint = api_endpoint
        self.username = username
        self.password = password
        self.auth_token = None
        
    def authenticate(self):
        # Get authentication token
        
    def create_connection_group(self, name, parent_id):
        # Create a connection group
        
    def create_connection(self, connection_data):
        # Create a connection
        
    def delete_connection(self, connection_id):
        # Delete a connection
        
    def get_connection_groups(self):
        # Get all connection groups
        
    def get_connections(self):
        # Get all connections
```

### 3. Refactor Main Function
The main function will use both classes but keep them decoupled:

```python
def main():
    # Initialize API
    api = GuacamoleAPI(GUACAMOLE_API_ENDPOINT, GUACA_USER, GUACA_PASS)
    api.authenticate()
    
    # Get data from Guacamole
    existing_groups = api.get_connection_groups()
    existing_connections = api.get_connections()
    
    # Initialize connection group tree
    tree = ConnectionGroupTree()
    tree.build_from_data(existing_groups, existing_connections)
    
    # Process CSV file
    with open("connections.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Get or create the group path
            site_path = row["site"]
            parent_id = tree.get_parent_id_for_path(site_path)
            
            # If the parent doesn't exist in Guacamole, create it
            if parent_id not in existing_groups and parent_id != "ROOT":
                # Create the necessary groups in Guacamole
                # This would involve parsing the path and creating each group
                # ...
                
            # Create connection in Guacamole
            connection_data = {
                "parentIdentifier": parent_id,
                # Other connection data from CSV
            }
            connection_id = api.create_connection(connection_data)
            
            # Update our local tree
            tree.add_connection(connection_id, row["device_name"], row["protocol"], parent_id)
            
    print("CSV import completed successfully!")
    tree.print_tree()
```

### 4. Implement Site ID to Group ID Functionality
The ConnectionGroupTree class will have methods to:
- Parse site IDs from paths (e.g., extract "AIN" from "AIN/DC1/Rack10")
- Map site IDs to their corresponding group IDs
- Provide a clean interface to get a group ID from a site ID

For example:
```python
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
    for path, group_id in self.path_to_id.items():
        parts = path.split('/')
        if parts and parts[0] == site_id:
            # Return the ID of the top-level group matching the site ID
            return self.get_group_id_by_path(site_id)
    return None
```

### 5. Add Documentation and Error Handling
- Add docstrings to all classes and methods
- Implement proper error handling
- Add logging for better debugging

## Benefits of This Approach
1. Complete decoupling of the tree structure from the API
2. Better adherence to single responsibility principle
3. More reusable components
4. Clearer separation of concerns
5. Easier to test each component independently
6. Added functionality to get group ID from site ID
