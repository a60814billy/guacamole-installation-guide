from typing import TypedDict, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class ConnectionGroup:
    name: str
    identifier: str
    parentIdentifier: str = None
    type: str = "ORGANIZATIONAL"
    activeConnections: int = 0
    attributes: dict = field(default_factory=dict)
    childrens: List["ConnectionGroup"] = field(default_factory=list)
    connections: List["Connection"] = field(default_factory=list)


@dataclass
class Connection:
    name: str
    identifier: str
    parentIdentifier: str
    protocol: str
    attributes: dict = field(default_factory=dict)


class ConnectionGroupTree:
    """
    A class to manage a tree structure of connection groups and connections.
    This class is decoupled from any API or external system.
    """

    def __init__(self):
        """Initialize an empty connection group tree with a ROOT node."""
        self.group_tree_root = ConnectionGroup(name="ROOT", identifier="ROOT")
        self.path_mapping: Dict[str, ConnectionGroup] = {"ROOT": self.group_tree_root}

    def find_group(self, group_id: str):
        stack = [self.group_tree_root]

        while len(stack) > 0:
            current = stack.pop()
            if current.identifier == group_id:
                return current
            stack.extend(current.childrens)

        return None

    def reverse_get_full_path_name(self, group: ConnectionGroup, postfix: str = ""):
        current_path = group.name
        if postfix != "":
            current_path = f"{current_path}/{postfix}"
        if group.parentIdentifier == None:
            return current_path
        return self.reverse_get_full_path_name(
            self.find_group(group.parentIdentifier), current_path
        )

    def build_from_data(
        self, connection_groups: List[Dict[str, Any]], connections: List[Dict[str, Any]]
    ):
        tmp_groups = [*connection_groups]
        while len(tmp_groups) > 0:
            group = tmp_groups.pop(0)
            parent_id = group["parentIdentifier"]
            parent_obj = self.find_group(parent_id)
            if parent_id is not None:
                grp = ConnectionGroup(
                    name=group["name"],
                    identifier=group["identifier"],
                    parentIdentifier=group["parentIdentifier"],
                    type=group["type"],
                    activeConnections=group["activeConnections"],
                    attributes=group["attributes"],
                )
                parent_obj.childrens.append(grp)
                self.path_mapping[self.reverse_get_full_path_name(grp)] = grp
            else:
                tmp_groups.append(group)

        tmp_connections = [*connections]
        while len(tmp_connections) > 0:
            connection = tmp_connections.pop(0)
            parent_id = connection["parentIdentifier"]
            parent_obj = self.find_group(parent_id)
            if parent_obj is not None:
                parent_obj.connections.append(
                    Connection(
                        name=connection["name"],
                        identifier=connection["identifier"],
                        parentIdentifier=connection["parentIdentifier"],
                        protocol=connection["protocol"],
                        attributes=connection["attributes"],
                    )
                )
            else:
                tmp_connections.append(connection)

    def print_tree(self):
        root = self.group_tree_root
        print("")
        print(f"- Group: {root.name} (ID: {root.identifier})")
        for connection in root.connections:
            print(f"  * Connection: {connection.name} (ID: {connection.identifier})")

        for child in root.childrens:
            self._print_tree_internal(child, 1)

    def _print_tree_internal(self, current, indent):
        print("  " * indent + f"- Group: {current.name} (ID: {current.identifier})")

        for connection in current.connections:
            print(
                "  " * (indent + 1)
                + f"* Connection: {connection.name} (ID: {connection.identifier})"
            )

        for child in current.childrens:
            self._print_tree_internal(child, indent + 1)
