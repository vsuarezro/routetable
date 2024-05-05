import sqlite3

import pytest
import app.storage as storage

@pytest.fixture(scope="module")  # Create database once per test module
def test_db():
    url = ":memory:"  # In-memory database
    conn = storage._initialize_database(url)  # Initialize the database
    yield conn
    storage._destroy_database(conn)  # Destroy the database after the test

def test_save_routes(test_db: sqlite3.Connection):
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

def test_save_and_get_routes(test_db: sqlite3.Connection):
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

@pytest.mark.parametrize(
    "route_data, modified_route_data, expected_key_change, key_before, key_after",
    [
        # Test case 1: next_hop change 
        (
            {"route": "10.0.0.0/24", "next_hop": "10.10.10.1", 
             "flags": "L", "route_type": "Local", 
             "route_protocol": "ISIS", "age": "00h08m44s",
             "interface_next_hop": None, "metric": "100112222", "preference": "170"
            }, 
            {"route": "10.0.0.0/24", "next_hop": "10.10.20.1", 
             "flags": "L", "route_type": "Local", 
             "route_protocol": "ISIS", "age": "00h08m44s",
             "interface_next_hop": None, "metric": "100112222", "preference": "170"
            }, 
            "next_hop",
            "next_hop_before",
            "next_hop_after"
        ),  
        # Test case 2: metric change
        (
            {"route": "10.0.0.0/24", "next_hop": "10.10.10.1", 
             "flags": "L", "route_type": "Local", 
             "route_protocol": "ISIS", "age": "00h08m44s",
             "interface_next_hop": None, "metric": "100",  "preference": "170"
            }, 
            {"route": "10.0.0.0/24", "next_hop": "10.10.10.1", 
             "flags": "L", "route_type": "Local", 
             "route_protocol": "ISIS", "age": "00h08m44s",
             "interface_next_hop": None, "metric": "110", "preference": "170"
            }, 
            "metric",
            "metric_before",
            "metric_after"
        ),
        # Test case 3: protocol change
        (
            {"route": "10.0.0.0/24", "next_hop": "10.10.10.1", 
             "flags": "L", "route_type": "Local", 
             "route_protocol": "ISIS", "age": "00h08m44s",
             "interface_next_hop": None, "metric": "100", "preference": "170"
            }, 
            {"route": "10.0.0.0/24", "next_hop": "10.10.10.1", 
             "flags": "L", "route_type": "Local", 
             "route_protocol": "BGP_LABEL", "age": "00h08m44s",
             "interface_next_hop": None, "metric": "100", "preference": "170"
            }, 
            "route_protocol",

            "route_protocol_before",
            "route_protocol_after"
        ),
        # Add more test cases for different change types ... 
    ]
)
def test_route_change_detection(route_data, modified_route_data, expected_key_change, key_before, key_after):
    timestamp1 = '2024-05-08_16:20'
    timestamp2 = '2024-05-08_16:35'  # Later timestamp
    database_connection = storage._initialize_database(":memory:")

    # Save the routes for both timestamps (initially the same)
    storage.save_routes(timestamp1, [route_data], database_connection=database_connection) 
    storage.save_routes(timestamp2, [modified_route_data], database_connection=database_connection) 

    # Perform comparison
    comparison_result = storage.changed_routes(timestamp1, timestamp2, database_connection=database_connection)
    
    # Validate the expected field is present
    assert expected_key_change in route_data

    # Assertions
    assert len(comparison_result['changed']) == 1 
    changed_route = comparison_result['changed'][0]
    assert changed_route['route'] == route_data['route']
    assert changed_route[key_after] == modified_route_data[expected_key_change]
    assert changed_route[key_before] == route_data[expected_key_change]
    
    # destroy database when test case ends
    storage._destroy_database(database_connection)

def test_added_route_detection(test_db: sqlite3.Connection):
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

@pytest.mark.parametrize(
    "initial_routes, later_routes, removed_route",
    [
        # Test Case 1:
        (
            [
                {
                    "route": "1.1.1.10/32", "flags": "B",
                    "route_type": "Remote", "route_protocol": "BGP_LABEL",
                    "age": "10h49m31s", "preference": "170",
                    "next_hop": "10.20.30.40", "interface_next_hop": "tunneled:SR-ISIS:530001",
                    "metric": "100"
                },
                {
                    "route": "2.2.2.20/32", "flags": "L",
                    "route_type": "Local", "route_protocol": "ISIS",
                    "age": "00h08m44s", "preference": "18",
                    "next_hop": "10.190.144.128", "interface_next_hop": None,
                    "metric": "100112222"
                }
            ],
            [ 
                {
                    "route": "2.2.2.20/32", "flags": "L",
                    "route_type": "Local", "route_protocol": "ISIS",
                    "age": "00h08m44s", "preference": "18",
                    "next_hop": "10.190.144.128", "interface_next_hop": None,
                    "metric": "100112222"
                }
            ],
            {
                "route": "1.1.1.10/32", "flags": "B",
                "route_type": "Remote", "route_protocol": "BGP_LABEL",
                "age": "10h49m31s", "preference": "170",
                "next_hop": "10.20.30.40", "interface_next_hop": "tunneled:SR-ISIS:530001",
                "metric": "100"
            },
        ),
        # Add more test cases with different routes being removed
    ]
)
def test_removed_route_detection(initial_routes, later_routes, removed_route):
    timestamp1 = '2024-05-09_08:30'
    timestamp2 = '2024-05-09_09:15' 
    database_connection = storage._initialize_database(":memory:")

    # Save data
    storage.save_routes(timestamp1, initial_routes, database_connection=database_connection)
    storage.save_routes(timestamp2, later_routes, database_connection=database_connection) 

    # Comparison
    result = storage.compare_routes(timestamp1, timestamp2, database_connection=database_connection)

    assert len(result['removed']) == 1 
    assert result['removed'][0]["route"] == removed_route["route"]

    # destroy database when test case ends
    storage._destroy_database(database_connection)


import time 
import random
import copy

def generate_test_route(route_prefix):
    """Generates a sample route dictionary.""" 
    return {
        "route": f"{route_prefix}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}/{random.randint(1, 32)}",
        "flags": random.choice(["B", "L"]),
        "route_type" : random.choice(["Local", "Remote", "Blackh*"]),
        "route_protocol": random.choice(["BGP VPN", "BGP_LABEL", "ISIS", "Aggr", "Static", "OSPF", "Local", "BGP"]),
        "age": f"{random.randint(0, 99)}h{random.randint(0, 59)}m{random.randint(0, 59)}s",
        "preference": random.choice(["0", "5", "10", "15", "18", "150", "160", "165", "170"]),
        "next_hop": random.choice([f"10.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}", "TO_HOSTNAME1", "TO_HOSTANAME2"]),
        "interface_next_hop":  random.choice(["", "tunneled:SR-ISIS:530001", "tunneled:SR-TE:401", "tunneled:BGP", "tunneled:RSVP:85034",]),
        "metric": f"{random.randint(1, 19999)}",
    }

@pytest.mark.parametrize("num_routes", [10000])  # Adjust the number for your test
def test_large_scale_comparison(num_routes):
    timestamp1 = "2024-05-09_08:00"
    timestamp2 = "2024-05-09_08:15"
    database_connection = storage._initialize_database(":memory:")

    # Generate routes 
    initial_routes = [generate_test_route("10") for _ in range(num_routes)]
    # Deep Copy 
    later_routes = copy.deepcopy(initial_routes) 
    later_routes = later_routes[:-10]  # Simulate 10 removed routes
    later_routes[-1]["next_hop"] = "TO_HOSTNAME3" # Simulate a change in a next_hop
    later_routes[-2]["metric"] = "20000" # Simulate a change in a metric
    later_routes[0]["route_protocol"] = "OTHER" # Simulate a change in a route_protocol
    later_routes.extend( [generate_test_route("20") for _ in range(10)] ) # Simulate 10 new route

    # Store routes
    start_save_time1 = time.time()
    storage.save_routes(timestamp1, initial_routes, database_connection=database_connection)
    save_routes_time1 = time.time() - start_save_time1

    start_save_time2 = time.time()
    storage.save_routes(timestamp2, later_routes, database_connection=database_connection)
    save_routes_time2 = time.time() - start_save_time2

    # Benchmarking
    start_time = time.time()
    result = storage.compare_routes(timestamp1, timestamp2, database_connection=database_connection)
    compare_time = time.time() - start_time

    start_changed = time.time()
    changed_results = storage.changed_routes(timestamp1, timestamp2, database_connection=database_connection)
    changed_time = time.time() - start_changed

    # breakpoint()
    # Assertions (adjust if needed)
    assert len(result['removed']) == 10  
    assert len(result['added']) == 10
    assert len(changed_results['changed']) == 3

    # Performance Reporting
    print(f"\nTotal save_routes 1st time: {save_routes_time1:.4f} seconds")
    print(f"Total save_routes 2nd time: {save_routes_time2:.4f} seconds")
    print(f"Total compare_routes time: {compare_time:.4f} seconds")
    print(f"Total changed_routes time: {changed_time:.4f} seconds")

    # destroy database when test case ends
    storage._destroy_database(database_connection)