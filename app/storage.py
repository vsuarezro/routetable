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
import json

route_history = {}  # Global dictionary to hold route data

database_url = ':memory:'

# Function to initialize the database
def _initialize_database(db_url:str = database_url):
    """Creates necessary tables if they don't exist"""
    conn = sqlite3.connect(database_url) 
    cursor = conn.cursor()
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS igp_routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Auto-incrementing ID
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
    ''') 
    conn.commit()  
    return conn

# Call the initialization function when the module is imported
conn = _initialize_database() 

def _destroy_database(database_connection :sqlite3.connect = conn):
    conn = sqlite3.connect(database_url)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS igp_routes")
    conn.commit()
    conn.close()

def save_routes(timestamp:str, routes:list, database_connection :sqlite3.connect = conn) -> None:
    """Stores routes with a given timestamp in the SQLite database"""
    # breakpoint()
    cursor = database_connection .cursor()

    cursor.executemany("""
        INSERT INTO igp_routes (timestamp, route, flags, route_type, route_protocol, age, preference, next_hop, interface_next_hop, metric) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
        [(timestamp, route['route'], route['flags'], route['route_type'], route['route_protocol'], route['age'], route['preference'], route['next_hop'], route['interface_next_hop'], route['metric']) for route in routes]
    )
    database_connection .commit()
    # database_connection .close() # Close the connection after saving


def get_routes(timestamp:str, database_connection :sqlite3.connect = conn) -> list:
    """Retrieves routes for a timestamp from the SQLite database"""
    cursor = database_connection .cursor()

    cursor.execute("SELECT * FROM igp_routes WHERE timestamp=?", (timestamp,))
    results = cursor.fetchall()  
    
    routes = [dict(zip([column[0] for column in cursor.description], row)) for row in results]
    
    # database_connection .close()
    return routes 

def compare_routes(timestamp1:datetime, timestamp2:datetime, fields:list = ["route"], database_connection :sqlite3.connect = conn) -> dict:
    routes1 = get_routes(timestamp1, database_connection )
    routes2 = get_routes(timestamp2, database_connection )

    if routes1 is None or routes2 is None:
        return None  # Or raise an exception if timestamps are invalid

    # Create a dictionary of unique identifiers for routes in timestamp1
    unique_identifiers1 = {get_unique_identifier(route,fields): route for route in routes1}
    unique_identifiers2 = {get_unique_identifier(route,fields): route for route in routes2}

    # Iterate over unique identifiers in timestamp1 and compare with timestamp2
    added_routes = []
    removed_routes = []
    changed_routes = []
    for unique_identifier in unique_identifiers1:
        if unique_identifier not in unique_identifiers2:
            removed_routes.append(unique_identifiers1[unique_identifier])

    # Find added routes by checking for unique identifiers in timestamp2 that are not in timestamp1
    added_routes = [route for route in routes2 if get_unique_identifier(route,fields) not in unique_identifiers1]

    cursor = database_connection .cursor()
    cursor.execute("""
        SELECT 
            r1.route, r1.next_hop, r1.metric, r1.route_protocol
        FROM 
            igp_routes r1
        INNER JOIN 
            igp_routes r2 
        ON 
            r1.route = r2.route 
        WHERE 
            r1.timestamp = ? AND 
            r2.timestamp = ? AND 
            (r1.next_hop != r2.next_hop OR 
             r1.metric != r2.metric OR 
             r1.route_protocol != r2.route_protocol)
    """, (timestamp1, timestamp2))

    changed_routes = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]

    return {
        'added': added_routes,
        'removed': removed_routes,
        'changed': changed_routes
    }

    return {
        'added': added_routes,
        'removed': removed_routes,
        'changed': changed_routes
    }

def get_unique_identifier(route:dict, fields: list = None) -> str:
    """Generates a unique identifier for a route based on the specified fields.

    Args:
        route: The route dictionary.
        fields: A list of fields to include in the identifier. If None, all fields are used.

    Returns:
        A unique identifier string.
    """

    if fields is None:
        fields = route.keys()

    # Sort the fields to ensure consistent ordering
    fields = sorted(fields)

    # Generate the identifier string
    return f"{'-'.join([str(route[field]) for field in fields])}"
