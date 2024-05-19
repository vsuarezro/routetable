"""
storage.py is a library to store data in a sqlite database.
If the database does not exist then it is created when the module is imported
The database can save two different types of dictionaries:
one dictionary is for IGP routes, the dictionary has the following keys: 
route, flags, route_type, route_protocol, age, preference, next_hop, interface_next_hop, metric

example:
"route": "1.1.1.1/32",
"flags": "B",
"route_type": "Remote",
"route_protocol": "BGP_LABEL",
"age": "10h49m31s",
"preference": "170",
"next_hop": "10.20.30.40",
"interface_next_hop": "tunneled:SR-ISIS:530001",
"metric": "100"

The other dictionary has the following keys:
status_code, prefix, local_pref, med, next_hop, path_id, igp_cost, path, label

example:
"status_code": "u*>?",
"prefix": "65500:10:1.2.3.4/32",
"local_pref": "90",
"med": "None",
"next_hop": "10.20.30.40",
"path_id": "409912231",
"igp_cost": "100",
"path": "16960",
"label": "16000"

Each entry must be saved with a timestamp (example 2024-05-06_10:30)
All routes with a specific timestamp must be comparable to the routes saved with a different timestamp.
the comparison timestamps are user selectable.
"""

import sqlite3
import datetime
import logging
logger = logging.getLogger(__name__)  # Get a logger for the 'storage' module

database_url = "routes.sqlite3"

class DatabaseConnection:
    __instance = None  

    def __init__(self, url):
        if DatabaseConnection.__instance is not None:
            raise Exception("This class is a singleton! Use the get_instance() method.")
        else:
            DatabaseConnection.__instance = self
            self._conn = sqlite3.connect(url)

    @staticmethod
    def get_instance():
        """ Static access method. """
        if DatabaseConnection.__instance is None:
            DatabaseConnection(database_url)
        return DatabaseConnection.__instance

    def get_connection(self):
        """ Returns a connection to the database """
        return self._conn

    # New methods for testing
    @staticmethod
    def set_database_url(url):
        global database_url
        database_url = url

    @staticmethod
    def reset_instance():
        DatabaseConnection.__instance = None

    @staticmethod
    def destroy_database():
        with DatabaseConnection.get_instance().get_connection() as database_connection:
            if database_connection is not None:
                cursor = database_connection.cursor()
                cursor.execute("DROP TABLE IF EXISTS igp_routes")
                database_connection.commit()
        DatabaseConnection.__instance = None

# Function to initialize the database
def initialize_database(db_url: str = database_url):
    """Creates necessary tables if they don't exist"""
    logger.debug("initialize_database")
    logger.debug(f"Initializing database at {db_url}")
    global database_url
    database_url = db_url
    current_url = db_url
    with DatabaseConnection.get_instance().get_connection() as database_connection:
        database_connection = sqlite3.connect(db_url)
        cursor = database_connection.cursor()
        cursor.execute(
            """ 
            CREATE TABLE IF NOT EXISTS igp_routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Auto-incrementing ID
                hostname TEXT NOT NULL,
                service TEXT NOT NULL,
                timestamp TEXT NOT NULL,            
                route TEXT NOT NULL,
                flags TEXT,
                route_type TEXT,
                route_protocol TEXT,
                age TEXT,
                preference TEXT,
                next_hop TEXT,
                interface_next_hop TEXT,
                metric TEXT
            )
        """
        )
        database_connection.commit()
    return



def save_routes(
    timestamp: str, routes: list,
) -> None:
    """Stores routes with a given timestamp in the SQLite database"""
    logger.debug("save_routes")
    with DatabaseConnection.get_instance().get_connection() as database_connection:
        cursor = database_connection.cursor()
        logger.debug(f"Saving routes with timestamp {timestamp}")
        logger.debug(f"first route: {routes[0]}")
        cursor.executemany(
            """
            INSERT INTO igp_routes (hostname, service, timestamp, route, flags, route_type, route_protocol, age, preference, next_hop, interface_next_hop, metric) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    route.get("hostname"),
                    route.get("service"),
                    timestamp,
                    route.get("route"),
                    route.get("flags", ""),
                    route.get("route_type", ""),
                    route.get("route_protocol", ""),
                    route.get("age", ""),
                    route.get("preference", ""),
                    route.get("next_hop", ""),
                    route.get("interface_next_hop", ""),
                    route.get("metric", ""),
                )
                for route in routes
            ],
        )
        database_connection.commit()
    logger.debug(f"Saved routes with timestamp {timestamp}. Committing changes to database {cursor}")



def get_routes(hostname:str, service:str, timestamp: str, ) -> list:
    """Retrieves routes for a hostname at a specific timestamp from the SQLite database"""
    logger.debug("get_routes")
    with DatabaseConnection.get_instance().get_connection() as database_connection:
        cursor = database_connection.cursor()
        try:
            cursor.execute("SELECT * FROM igp_routes WHERE hostname=? AND service=? AND timestamp=?", (hostname, service, timestamp,))
            results = cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error getting changed routes: {e}")
            raise 

    routes = [
        dict(zip([column[0] for column in cursor.description], row)) for row in results
    ]

    return routes

def remove_routes(
    hostname: str,
    timestamp: str,
) -> None:
    """
    Remove routes from the database quering hostname and timestamp
    """
    logger.debug("remove_routes")
    with DatabaseConnection.get_instance().get_connection() as database_connection:
        cursor = database_connection.cursor()
        rows_deleted = cursor.execute("DELETE FROM igp_routes WHERE hostname=? AND timestamp=?", (hostname, timestamp,)).rowcount
        database_connection.commit()
    return rows_deleted


def compare_routes(
    hostname: str,
    service: str,
    timestamp1: datetime,
    timestamp2: datetime,
    fields: list = ["route"],
) -> dict:
    logger.debug("compare_routes")
    added_deleted_routes_dict = get_added_deleted_routes(hostname, service, timestamp1, timestamp2,)
    changed_routes_dict = changed_routes(hostname, service, timestamp1, timestamp2,)
    if added_deleted_routes_dict is not None:
        logger.debug(f"Added and deleted routes: {added_deleted_routes_dict}")
    else:
        logger.debug(f"No added and deleted routes found")
    
    if changed_routes_dict is not None: 
        logger.debug(f"Changed routes: {changed_routes_dict}")
    else:
        logger.debug(f"No changed routes found")
    compared_routes = dict()
    compared_routes["added"] = added_deleted_routes_dict["added"]
    compared_routes["deleted"] = added_deleted_routes_dict["deleted"]
    compared_routes["changed"] = changed_routes_dict["changed"]

    return compared_routes

def get_added_deleted_routes(
    hostname: str,
    service: str,
    timestamp1: datetime,
    timestamp2: datetime,
    fields: list = ["hostname", "service", "route"],
) -> dict:
    logger.debug("get_added_deleted_routes")
    logger.debug(f"Getting added and deleted routes for {hostname} {service} {timestamp1} {timestamp2}")
    routes1 = get_routes(hostname, service, timestamp1,)
    if routes1 is not None:
        logger.debug(f"Got routes for {hostname} {service} {timestamp1} first route: {routes1[0]}")
    routes2 = get_routes(hostname, service, timestamp2,)
    if routes2 is not None:
        logger.debug(f"Got routes for {hostname} {service} {timestamp1} first route: {routes2[0]}")

    if routes1 is None or routes2 is None:
        logger.debug(f"No routes found for {hostname} {service} {timestamp1} {timestamp2}")
        NO_ROUTES = {
        "added": [],
        "deleted": [],
        }
        return NO_ROUTES  # Or raise an exception if timestamps are invalid

    # Create a dictionary of unique identifiers for routes in timestamp1
    unique_identifiers1 = {
        get_unique_identifier(route, fields): route for route in routes1
    }
    unique_identifiers2 = {
        get_unique_identifier(route, fields): route for route in routes2
    }

    # Iterate over unique identifiers in timestamp1 and compare with timestamp2
    added_routes = []
    removed_routes = []
    for unique_identifier in unique_identifiers1:
        if unique_identifier not in unique_identifiers2:
            removed_routes.append(unique_identifiers1[unique_identifier])

    # Find added routes by checking for unique identifiers in timestamp2 that are not in timestamp1
    added_routes = [
        route
        for route in routes2
        if get_unique_identifier(route, fields) not in unique_identifiers1
    ]

    return {
        "added": added_routes,
        "deleted": removed_routes,
    }


def changed_routes(
    hostname:str, 
    service:str,
    timestamp1: datetime,
    timestamp2: datetime,
    fields: list = ["route"],
) -> dict:
    logger.debug("changed_routes")
    logger.debug(f"Getting changed routes for {hostname} {service} {timestamp1} {timestamp2}")
    routes1 = get_routes(hostname, service, timestamp1,)
    routes2 = get_routes(hostname, service, timestamp2,)

    if routes1 is None or routes2 is None:
        return None  # Or raise an exception if timestamps are invalid

    # Group routes by prefix
    routes1_by_route = {}
    routes2_by_route = {}
    for route in routes1:
        routes1_by_route.setdefault(route["route"], []).append(route)
    for route in routes2:
        routes2_by_route.setdefault(route["route"], []).append(route)

    changed_routes = []
    for route, routes1_entries in routes1_by_route.items():
        routes2_entries = routes2_by_route.get(route, [])
        # Skip on deleted routes, if the result is an empty list, 
        # it means routes2_by_route.get(route) failed, and so the route
        # exists on routes1 (first timestamp) but not in the second
        if routes2_entries == []:
            continue

        # Check for differences in the set of next hops and metrics
        # by first getting a set of all meaningful keys 
        # for the entries of the route in both timestamps
        next_hops1 = set(entry["next_hop"] for entry in routes1_entries)
        next_hops2 = set(entry["next_hop"] for entry in routes2_entries)
        metrics1 = set(entry["metric"] for entry in routes1_entries)
        metrics2 = set(entry["metric"] for entry in routes2_entries)
        protocols1 = set(entry["route_protocol"] for entry in routes1_entries)
        protocols2 = set(entry["route_protocol"] for entry in routes2_entries)

        if next_hops1 != next_hops2 or metrics1 != metrics2 or protocols1 != protocols2:
            # Detect changes in the relevant fields
            # search for a r2_match that means all entries between r1 and r2 are equal
            # searches for an r2 (different r2) which has any of the meaningful keys different to r1
            # fill the fields with r1 and r2 values for first timestamp (before) and second timestamp (after)
            for r1 in routes1_entries:
                r2_match = next(
                    (
                        r2
                        for r2 in routes2_entries
                        if r2["next_hop"] == r1["next_hop"]
                        and r2["metric"] == r1["metric"]
                        and r2["route_protocol"] == r1["route_protocol"]
                    ),
                    None,
                )
                r2 = next(
                    (
                        r2
                        for r2 in routes2_entries
                        if r2["next_hop"] != r1["next_hop"]
                        or r2["metric"] != r1["metric"]
                        or r2["route_protocol"] != r1["route_protocol"]
                    ),
                    None,
                )

                if not r2_match:
                    changed_route = {
                        "route": route,
                        "next_hop_before": r1["next_hop"],
                        "next_hop_after": r2.get("next_hop") if r2 else None,
                        "metric_before": r1["metric"],
                        "metric_after": r2.get("metric") if r2 else None,
                        "route_protocol_before": r1["route_protocol"],
                        "route_protocol_after": r2.get("route_protocol") if r2 else None,
                    }
                    changed_routes.append(changed_route)

    return {"changed": changed_routes}


def get_list_of_timestamps(hostname:str=None,) -> list:
    """
    Retrieves a list of timestamps for a given hostname from the database.
    If hostname is None, generate the list for all hostnames in the database. Order the results from newest to oldest.
    Returns a list of unique hostname,timestamp tuples.
    """
    logger.debug("get_list_of_timestamps")
    if hostname:
        logger.debug(f"Getting list of timestamps for {hostname}") 
    else:
        logger.debug("Getting list of timestamps for all hostnames") 
    with DatabaseConnection.get_instance().get_connection() as database_connection:
        cursor = database_connection.cursor()
        if hostname is None:
            cursor.execute("SELECT DISTINCT hostname, service, timestamp FROM igp_routes ORDER BY timestamp DESC")
        else:
            cursor.execute("SELECT DISTINCT hostname, service, timestamp FROM igp_routes WHERE hostname=? ORDER BY timestamp DESC", (hostname,))

        results = cursor.fetchall()

    return results


def get_latest_timestamps(hostname: str, service:str,) -> tuple:
    """
    Retrieves the two most recent timestamps for a given hostname and service combination from the database.

    Args:
        hostname: The hostname.
        service: The service name
        database_connection: The connection to the SQLite database.

    Returns:
        A tuple containing the two most recent timestamps, or None if no matching timestamps are found.
    """
    logger.debug("get_latest_timestamps")
    logger.debug(f"Getting latest timestamps for {hostname} and {service}")
    with DatabaseConnection.get_instance().get_connection() as database_connection:
        cursor = database_connection.cursor()
        cursor.execute(
            """
            SELECT DISTINCT timestamp 
            FROM igp_routes
            WHERE hostname = ? AND service = ?
            ORDER BY timestamp DESC
            LIMIT 2
            """,
            (hostname, service),
        )
        results = cursor.fetchall()

    if len(results) == 2:
        return results[0][0], results[1][0]  # Extract timestamps from results
    else:
        return None  # Or you might want to raise an exception


def get_unique_identifier(route_dict: dict, fields: list = None) -> str:
    """Generates a unique identifier for a route based on the specified fields.

    Args:
        route: The route dictionary.
        fields: A list of fields to include in the identifier. If None, all fields are used.

    Returns:
        A unique identifier string.
    """
    if fields is None:
        fields = route_dict.keys()

    # Sort the fields to ensure consistent ordering
    fields = sorted(fields)
    # Generate the identifier string
    route_keys = [str(route_dict[field]) for field in fields]
    identifier = f"{'-'.join(route_keys)}"
    return identifier
