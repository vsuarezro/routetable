import sqlite3

import pytest
import app.storage as storage

@pytest.fixture(scope="module")  # Create database once per test module
def test_db():
    url = ":memory:"  # In-memory database
    conn = storage._initialize_database(url)  # Initialize the database
    yield conn
    storage._destroy_database(conn)  # Destroy the database after the test

def test_save_routes(test_db):
    timestamp = '2024-05-08_16:21'
    routes = [
        {
            "route": "1.1.1.1/32",
            "flags": "B",
            "route_type": "Remote",
            "route_protocol": "BGP_LABEL",
            "age": "10h49m31s",
            "preference": "170",
            "next_hop": "10.20.30.40",
            "interface_next_hop": "tunneled:SR-ISIS:530001",
            "metric": "100"
        },
        {
            "route": "2.2.2.2/32",
            "flags": "L",
            "route_type": "Local",
            "route_protocol": "ISIS",
            "age": "00h08m44s",
            "preference": "18",
            "next_hop": "10.190.144.128",
            "interface_next_hop": None,
            "metric": "100112222"
        }
    ]

    storage.save_routes(timestamp, routes, test_db)

    # Assertion: Check if the routes were saved correctly
    cursor = test_db.cursor()
    count = cursor.execute("SELECT COUNT(*) FROM igp_routes WHERE timestamp=?", (timestamp,)).fetchone()[0]
    assert count == len(routes)

def test_save_and_get_routes(test_db):
    timestamp = "2024-05-06_10:31"
    routes = [
        {
            "route": "1.1.1.10/32",
            "flags": "B",
            "route_type": "Remote",
            "route_protocol": "BGP_LABEL",
            "age": "10h49m31s",
            "preference": "170",
            "next_hop": "10.20.30.40",
            "interface_next_hop": "tunneled:SR-ISIS:530001",
            "metric": "100"
        },
        {
            "route": "2.2.2.20/32",
            "flags": "L",
            "route_type": "Local",
            "route_protocol": "ISIS",
            "age": "00h08m44s",
            "preference": "18",
            "next_hop": "10.190.144.128",
            "interface_next_hop": None,
            "metric": "100112222"
        }
    ]

    # Save the routes
    storage.save_routes(timestamp, routes, database_connection =test_db)

    # Retrieve a specific route (e.g., the first one)
    retrieved_route = storage.get_routes(timestamp, database_connection =test_db)[0]  

    # Assertion: Compare relevant fields
    assert retrieved_route['route'] == routes[0]['route']
    assert retrieved_route['flags'] == routes[0]['flags']
    assert retrieved_route['route_type'] == routes[0]['route_type']
    assert retrieved_route['route_protocol'] == routes[0]['route_protocol']
    assert retrieved_route['preference'] == routes[0]['preference']
    assert retrieved_route['next_hop'] == routes[0]['next_hop']
    assert retrieved_route['interface_next_hop'] == routes[0]['interface_next_hop']
    assert retrieved_route['metric'] == routes[0]['metric']


def test_get_unique_identifier():
    route = {
        "route": "1.1.1.1/32",
        "route_protocol": "BGP_LABEL",
        "next_hop": "10.20.30.40",
        "metric": "100"
    }

    unique_identifier = storage.get_unique_identifier(route, ["route", "route_protocol", "next_hop", "metric"])

    assert unique_identifier == "100-10.20.30.40-1.1.1.1/32-BGP_LABEL"


def test_route_change_detection(test_db):
    timestamp1 = '2024-05-08_16:20'
    timestamp2 = '2024-05-08_16:35'  # Later timestamp

    # Original route data
    route_data = {
        "route": "10.0.0.0/24", 
        "flags": "B", 
        "route_type": "Remote", 
        "route_protocol": "BGP",
        "age": "01h00m00s",
        "preference": "100",
        "next_hop": "10.10.10.1",
        "interface_next_hop": "tunneled:SR-ISIS:500001",
        "metric": "50"
    }


    # Modify the route for timestamp2 (e.g., change the next-hop)
    modified_route_data = route_data.copy()
    modified_route_data['next_hop'] = "10.10.20.1"  

    # Save the routes for both timestamps (initially the same)
    storage.save_routes(timestamp1, [route_data], database_connection =test_db) 
    storage.save_routes(timestamp2, [modified_route_data], database_connection =test_db) 

    # Perform comparison
    comparison_result = storage.compare_routes(timestamp1, timestamp2, database_connection =test_db)

    # Assertions
    assert len(comparison_result['changed']) == 1 
    changed_route = comparison_result['changed'][0]
    assert changed_route['route'] == route_data['route'] 
    assert changed_route['next_hop'] != modified_route_data['next_hop'] 


def test_added_route_detection(test_db):
    timestamp1 = '2024-05-09_08:30'
    timestamp2 = '2024-05-09_09:15' 

    initial_routes = [
        {
            "route": "1.1.1.10/32",
            "flags": "B",
            "route_type": "Remote",
            "route_protocol": "BGP_LABEL",
            "age": "10h49m31s",
            "preference": "170",
            "next_hop": "10.20.30.40",
            "interface_next_hop": "tunneled:SR-ISIS:530001",
            "metric": "100"
        },
        {
            "route": "2.2.2.20/32",
            "flags": "L",
            "route_type": "Local",
            "route_protocol": "ISIS",
            "age": "00h08m44s",
            "preference": "18",
            "next_hop": "10.190.144.128",
            "interface_next_hop": None,
            "metric": "100112222"
        }
    ]

    new_route = {
            "route": "2.2.2.30/32",
            "flags": "L",
            "route_type": "Local",
            "route_protocol": "ISIS",
            "age": "00h08m44s",
            "preference": "18",
            "next_hop": "10.190.144.128",
            "interface_next_hop": None,
            "metric": "100112222"
        }

    # Save data
    storage.save_routes(timestamp1, initial_routes, database_connection =test_db)
    storage.save_routes(timestamp2, initial_routes + [new_route], database_connection =test_db) 

    # Comparison
    result = storage.compare_routes(timestamp1, timestamp2, database_connection =test_db)

    assert len(result['added']) == 1 
    assert result['added'][0]["route"] == new_route["route"]
