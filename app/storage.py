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

default_database_url = "routes.sqlite3"


def get_connection(db_url: str = default_database_url):
    """Returns a connection to the database"""
    return sqlite3.connect(db_url)

# Function to initialize the database
def initialize_database(db_url: str = default_database_url):
    """Creates necessary tables if they don't exist"""
    logger.debug(f"Initializing database at {db_url}")
    default_database_url = db_url
    with get_connection(db_url) as conn:
        conn = sqlite3.connect(db_url)
        cursor = conn.cursor()
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
        conn.commit()
    return default_database_url



def _destroy_database(url: str = default_database_url):
    with get_connection(url) as database_connection:
        if database_connection is None:
            database_connection = sqlite3.connect(default_database_url)
        cursor = database_connection.cursor()
        cursor.execute("DROP TABLE IF EXISTS igp_routes")
        database_connection.commit()
        database_connection.close()


def save_routes(
    timestamp: str, routes: list, url: str = default_database_url
) -> None:
    """Stores routes with a given timestamp in the SQLite database"""
    # breakpoint()
    with get_connection(url) as database_connection:
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



def get_routes(hostname:str, service:str, timestamp: str, url: str = default_database_url) -> list:
    """Retrieves routes for a hostname at a specific timestamp from the SQLite database"""
    with get_connection(url) as database_connection:
        cursor = database_connection.cursor()

        cursor.execute("SELECT * FROM igp_routes WHERE hostname=? AND service=? AND timestamp=?", (hostname, service, timestamp,))
        results = cursor.fetchall()

    routes = [
        dict(zip([column[0] for column in cursor.description], row)) for row in results
    ]

    return routes

def remove_routes(
    hostname: str,
    timestamp: str,
    url: str = default_database_url,
) -> None:
    """
    Remove routes from the database quering hostname and timestamp
    """
    with get_connection(url) as database_connection:
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
    url: str = default_database_url,
) -> dict:

    added_deleted_routes_dict = get_added_deleted_routes(hostname, service, timestamp1, timestamp2, url=url)
    changed_routes_dict = changed_routes(hostname, service, timestamp1, timestamp2, url)
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
    url: str = default_database_url,
) -> dict:
    # breakpoint()
    logger.debug(f"Getting added and deleted routes for {hostname} {service} {timestamp1} {timestamp2}")
    routes1 = get_routes(hostname, service, timestamp1, url)
    if routes1 is not None:
        logger.debug(f"Got routes for {hostname} {service} {timestamp1} first route: {routes1[0]}")
    routes2 = get_routes(hostname, service, timestamp2, url)
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
    url: str = default_database_url,
) -> dict:
    logger.debug(f"Getting changed routes for {hostname} {service} {timestamp1} {timestamp2}")
    routes1 = get_routes(hostname, service, timestamp1, url)
    routes2 = get_routes(hostname, service, timestamp2, url)

    if routes1 is None or routes2 is None:
        return None  # Or raise an exception if timestamps are invalid
    with get_connection(url) as database_connection:
        cursor = database_connection.cursor()
        cursor.execute(
            """
            SELECT 
                r1.route, 
                r1.next_hop AS next_hop_before, r2.next_hop AS next_hop_after,
                r1.metric AS metric_before, r2.metric AS metric_after,
                r1.route_protocol AS route_protocol_before, r2.route_protocol AS route_protocol_after
            FROM 
                igp_routes r1
            INNER JOIN 
                igp_routes r2 
            ON 
                r1.route = r2.route 
            WHERE 
                r1.hostname = ? AND r1.service = ? AND r1.timestamp = ? AND 
                r2.hostname = ? AND r2.service = ? AND r2.timestamp = ? AND 
                (r1.next_hop != r2.next_hop OR 
                r1.metric != r2.metric OR 
                r1.route_protocol != r2.route_protocol)
        """,
            (hostname, service, timestamp1, hostname, service, timestamp2),
        )

        changed_routes = [
            dict(zip([column[0] for column in cursor.description], row))
            for row in cursor.fetchall()
        ]

    return {"changed": changed_routes}

def get_list_of_timestamps(hostname:str=None, url: str = default_database_url) -> list:
    """
    Retrieves a list of timestamps for a given hostname from the database.
    If hostname is None, generate the list for all hostnames in the database. Order the results from newest to oldest.
    Returns a list of unique hostname,timestamp tuples.
    """
    
    if hostname:
        logger.debug(f"Getting list of timestamps for {hostname}") 
    else:
        logger.debug("Getting list of timestamps for all hostnames") 
    with get_connection(url) as database_connection:
        cursor = database_connection.cursor()
        if hostname is None:
            cursor.execute("SELECT DISTINCT hostname, service, timestamp FROM igp_routes ORDER BY timestamp DESC")
        else:
            cursor.execute("SELECT DISTINCT hostname, service, timestamp FROM igp_routes WHERE hostname=? ORDER BY timestamp DESC", (hostname,))

        results = cursor.fetchall()

    return results


def get_latest_timestamps(hostname: str, service:str, url: str = default_database_url) -> tuple:
    """
    Retrieves the two most recent timestamps for a given hostname and service combination from the database.

    Args:
        hostname: The hostname.
        service: The service name
        database_connection: The connection to the SQLite database.

    Returns:
        A tuple containing the two most recent timestamps, or None if no matching timestamps are found.
    """
    
    logging.debug(f"Getting latest timestamps for {hostname} and {service}")
    with get_connection(url) as database_connection:
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
