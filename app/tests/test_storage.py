import sqlite3
import time 
import random
import copy

import pytest
import app.storage as storage

@pytest.fixture(scope="function")  # Create database once per test module
def test_db():
    storage.DatabaseConnection.set_database_url(":memory:")  # Use in-memory DB for tests
    storage.initialize_database()
    yield
    storage.DatabaseConnection.destroy_database()  
    # storage.DatabaseConnection.reset_instance()  # Clean up and reset the connection

def test_save_routes(test_db):
    timestamp = '2024-05-08_16:21'
    routes = [
        {
            "hostname" : "HOSTNAME1",
            "service" : "SERVICE1",
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
            "hostname" : "HOSTNAME1",
            "service" : "SERVICE1",
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
    hostname = "HOSTNAME1"
    service = "SERVICE1"
    # Save the routes
    storage.save_routes(timestamp, routes,)

    # Assertion: Check if the routes were saved correctly
    routes_from_db = storage.get_routes(hostname, service, timestamp)
    count = len(routes_from_db)
    # count = cursor.execute("SELECT COUNT(*) FROM igp_routes WHERE hostname=? AND service=? AND timestamp=?", (hostname, service, timestamp,)).fetchone()[0]
    assert count == len(routes)

def test_save_and_get_routes(test_db):
    timestamp = "2024-05-06_10:31"
    hostname = "HOSTNAME1"
    service = "SERVICE1"
    routes = [
        {
            "hostname" : "HOSTNAME1",
            "service" : "SERVICE1",
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
            "hostname" : "HOSTNAME1",
            "service" : "SERVICE1",
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
    storage.save_routes(timestamp, routes,)

    # Retrieve a specific route (e.g., the first one)
    retrieved_route = storage.get_routes(hostname, service, timestamp,)[0]  

    # Assertion: Compare relevant fields
    assert retrieved_route['hostname'] == routes[0]['hostname']
    assert retrieved_route['service'] == routes[0]['service']
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
    "route_data, modified_route_data, expected_key_change, key_before, key_after,",
    [
        # Test case 1: next_hop change 
        (
            {"hostname" : "HOSTNAME1", "service" : "SERVICE1",
             "route": "10.0.0.0/24", "next_hop": "10.10.10.1", 
             "flags": "L", "route_type": "Local", 
             "route_protocol": "ISIS", "age": "00h08m44s",
             "interface_next_hop": None, "metric": "100112222", "preference": "170"
            }, 
            {"hostname" : "HOSTNAME1", "service" : "SERVICE1",
             "route": "10.0.0.0/24", "next_hop": "10.10.20.1", 
             "flags": "L", "route_type": "Local", 
             "route_protocol": "ISIS", "age": "00h08m44s",
             "interface_next_hop": None, "metric": "100112222", "preference": "170"
            }, 
            "next_hop",
            "next_hop_before",
            "next_hop_after",
        ),  
        # Test case 2: metric change
        (
            {"hostname" : "HOSTNAME1", "service" : "SERVICE1",
             "route": "10.0.0.0/24", "next_hop": "10.10.10.1", 
             "flags": "L", "route_type": "Local", 
             "route_protocol": "ISIS", "age": "00h08m44s",
             "interface_next_hop": None, "metric": "100",  "preference": "170"
            }, 
            {"hostname" : "HOSTNAME1", "service" : "SERVICE1",
             "route": "10.0.0.0/24", "next_hop": "10.10.10.1", 
             "flags": "L", "route_type": "Local", 
             "route_protocol": "ISIS", "age": "00h08m44s",
             "interface_next_hop": None, "metric": "110", "preference": "170"
            }, 
            "metric",
            "metric_before",
            "metric_after",
        ),
        # Test case 3: protocol change
        (
            {"hostname" : "HOSTNAME1", "service" : "SERVICE1",
             "route": "10.0.0.0/24", "next_hop": "10.10.10.1", 
             "flags": "L", "route_type": "Local", 
             "route_protocol": "ISIS", "age": "00h08m44s",
             "interface_next_hop": None, "metric": "100", "preference": "170"
            }, 
            {"hostname" : "HOSTNAME1", "service" : "SERVICE1",
             "route": "10.0.0.0/24", "next_hop": "10.10.10.1", 
             "flags": "L", "route_type": "Local", 
             "route_protocol": "BGP_LABEL", "age": "00h08m44s",
             "interface_next_hop": None, "metric": "100", "preference": "170"
            }, 
            "route_protocol",
            "route_protocol_before",
            "route_protocol_after",
        ),
        # Add more test cases for different change types ... 
    ]
)
def test_route_change_detection(route_data, modified_route_data, expected_key_change, key_before, key_after,test_db):
    timestamp1 = '2024-05-08_16:20'
    timestamp2 = '2024-05-08_16:35'  # Later timestamp
    hostname = "HOSTNAME1"
    service = "SERVICE1"

    # Save the routes for both timestamps (initially the same)
    storage.save_routes(timestamp1, [route_data],) 
    storage.save_routes(timestamp2, [modified_route_data],) 

    # Perform comparison
    comparison_result = storage.changed_routes(hostname, service, timestamp1, timestamp2,)
    
    # Validate the expected field is present
    assert expected_key_change in route_data

    # Assertions
    assert len(comparison_result['changed']) == 1 
    changed_route = comparison_result['changed'][0]
    assert changed_route['route'] == route_data['route']
    assert changed_route[key_after] == modified_route_data[expected_key_change]
    assert changed_route[key_before] == route_data[expected_key_change]


def test_added_route_detection(test_db):
    timestamp1 = '2024-05-09_08:30'
    timestamp2 = '2024-05-09_09:15' 

    initial_routes = [
        {
            "hostname": "HOSTNAME1",
            "service" : "SERVICE1",
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
            "hostname": "HOSTNAME1",
            "service" : "SERVICE1",
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
            "hostname": "HOSTNAME1",
            "service" : "SERVICE1",
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

    hostname = "HOSTNAME1"
    service = "SERVICE1"

    # Save data
    storage.save_routes(timestamp1, initial_routes,)
    storage.save_routes(timestamp2, initial_routes + [new_route],) 

    # Comparison
    result = storage.get_added_deleted_routes(hostname, service, timestamp1, timestamp2,)

    assert len(result['added']) == 1 
    assert result['added'][0]["route"] == new_route["route"]

@pytest.mark.parametrize(
    "initial_routes, later_routes, removed_route",
    [
        # Test Case 1:
        (
            [
                {
                    "hostname": "HOSTNAME1", "service" : "SERVICE1",
                    "route": "1.1.1.10/32", "flags": "B",
                    "route_type": "Remote", "route_protocol": "BGP_LABEL",
                    "age": "10h49m31s", "preference": "170",
                    "next_hop": "10.20.30.40", "interface_next_hop": "tunneled:SR-ISIS:530001",
                    "metric": "100"
                },
                {
                    "hostname": "HOSTNAME1", "service" : "SERVICE1",
                    "route": "2.2.2.20/32", "flags": "L",
                    "route_type": "Local", "route_protocol": "ISIS",
                    "age": "00h08m44s", "preference": "18",
                    "next_hop": "10.190.144.128", "interface_next_hop": None,
                    "metric": "100112222"
                }
            ],
            [ 
                {
                    "hostname": "HOSTNAME1", "service" : "SERVICE1",
                    "route": "2.2.2.20/32", "flags": "L",
                    "route_type": "Local", "route_protocol": "ISIS",
                    "age": "00h08m44s", "preference": "18",
                    "next_hop": "10.190.144.128", "interface_next_hop": None,
                    "metric": "100112222"
                }
            ],
            {
                "hostname": "HOSTNAME1","service" : "SERVICE1",
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
def test_removed_route_detection(initial_routes, later_routes, removed_route, test_db):
    timestamp1 = '2024-05-09_08:30'
    timestamp2 = '2024-05-09_09:15' 
    hostname = "HOSTNAME1"
    service = "SERVICE1"

    # Save data
    storage.save_routes(timestamp1, initial_routes,)
    storage.save_routes(timestamp2, later_routes,) 

    # Comparison
    result = storage.get_added_deleted_routes(hostname, service, timestamp1, timestamp2,)

    assert len(result['deleted']) == 1 
    assert result['deleted'][0]["route"] == removed_route["route"]


def generate_test_route(route_prefix):
    """Generates a sample route dictionary.""" 
    return {
        "hostname": f"HOSTNAME1",
        "service": f"SERVICE1",
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

def generate_unique_routes_list(num_routes):
    """Generates a list of unique routes."""
    print(num_routes)
    population = [generate_test_route(random.choice([10, 20, 30, 40, 50])) for _ in range(int(num_routes / 4))]
    population.extend(generate_test_route(random.choice([10, 20, 30, 40, 50])) for _ in range(int(num_routes / 4)))
    population.extend(generate_test_route(random.choice([10, 20, 30, 40, 50])) for _ in range(int(num_routes / 4)))
    population.extend(generate_test_route(random.choice([10, 20, 30, 40, 50])) for _ in range(int(num_routes / 4)))
    return random.sample(population, num_routes)


@pytest.mark.parametrize("num_routes", [10000, ])
def test_large_scale_comparison(num_routes, test_db):
    timestamp1 = "2024-05-09_08:00"
    timestamp2 = "2024-05-09_08:15"
    hostname = "HOSTNAME1"
    service = "SERVICE1"

    # Generate routes 
    initial_routes = generate_unique_routes_list(num_routes)
    # Deep Copy 
    later_routes = copy.deepcopy(initial_routes) 
    later_routes = later_routes[:-10]  # Simulate 10 removed routes
    later_routes[-1]["next_hop"] = "TO_HOSTNAME3" # Simulate a change in a next_hop
    later_routes[-2]["metric"] = "20000" # Simulate a change in a metric
    later_routes[0]["route_protocol"] = "OTHER" # Simulate a change in a route_protocol
    later_routes.extend( [generate_test_route("1") for _ in range(10)] ) # Simulate 10 new route, e.g. 1.1.1.10/32

    # Store routes
    start_save_time1 = time.time()
    storage.save_routes(timestamp1, initial_routes,)
    save_routes_time1 = time.time() - start_save_time1

    start_save_time2 = time.time()
    storage.save_routes(timestamp2, later_routes,)
    save_routes_time2 = time.time() - start_save_time2

    # Benchmarking
    start_time = time.time()
    result = storage.get_added_deleted_routes(hostname, service, timestamp1, timestamp2,)
    compare_time = time.time() - start_time

    start_changed = time.time()
    changed_results = storage.changed_routes(hostname, service, timestamp1, timestamp2,)
    changed_time = time.time() - start_changed

    # Assertions
    assert len(result['deleted']) == 10  
    assert len(result['added']) == 10
    assert len(changed_results['changed']) == 3

    # Performance Reporting
    print(f"\nTotal save_routes 1st time: {save_routes_time1:.4f} seconds")
    print(f"Total save_routes 2nd time: {save_routes_time2:.4f} seconds")
    print(f"Total compare_routes time: {compare_time:.4f} seconds")
    print(f"Total changed_routes time: {changed_time:.4f} seconds")


@pytest.mark.parametrize(
    "routes",
    [
        (
            [
                {
                    "hostname": "HOSTNAME1", "service": "SERVICE1",
                    "route": "1.1.1.10/32", "flags": "B",
                    "route_type": "Remote", "route_protocol": "BGP_LABEL",
                    "age": "10h49m31s", "preference": "170",
                    "next_hop": "10.20.30.40", "interface_next_hop": "tunneled:SR-ISIS:530001",
                    "metric": "100"
                },
                {
                    "hostname": "HOSTNAME1","service": "SERVICE1",
                    "route": "2.2.2.20/32", "flags": "L",
                    "route_type": "Local", "route_protocol": "ISIS",
                    "age": "00h08m44s", "preference": "18",
                    "next_hop": "10.190.144.128", "interface_next_hop": None,
                    "metric": "100112222"
                },
                {
                    "hostname": "HOSTNAME1", "service": "SERVICE1",
                    "route": "2.2.2.21/32", "flags": "L",
                    "route_type": "Local", "route_protocol": "ISIS",
                    "age": "00h08m44s", "preference": "18",
                    "next_hop": "10.190.144.128", "interface_next_hop": None,
                    "metric": "100112222"
                },
                {
                    "hostname": "HOSTNAME2", "service": "SERVICE1",
                    "route": "2.2.2.21/32", "flags": "L",
                    "route_type": "Local", "route_protocol": "ISIS",
                    "age": "00h08m44s", "preference": "18",
                    "next_hop": "10.190.144.128", "interface_next_hop": None,
                    "metric": "100112222"
                }
            ]

        ),
        # Add more test cases with different routes being removed
    ]
)
def test_get_list_of_timestamps(routes, test_db):
    """
    Test storage.get_list_of_timestamps
    save routes to the database with different timestamps
    Retrive the list of timestamps from the database using storage.get_list_of_timestamps
    Assert the list of timestamps is correct
    """
    # Save routes with different timestamps
    timestamps = [
        "2024-05-08_16:21",
        "2024-05-08_16:22",
        "2024-05-08_16:23",
    ]
    storage.save_routes(timestamps[0], routes,)
    storage.save_routes(timestamps[1], routes,)
    storage.save_routes(timestamps[2], routes,)
    
    expected_timestamps = [("HOSTNAME1","SERVICE1","2024-05-08_16:23",), 
                           ("HOSTNAME2","SERVICE1","2024-05-08_16:23",), 
                           ("HOSTNAME1","SERVICE1","2024-05-08_16:22",), 
                           ("HOSTNAME2","SERVICE1","2024-05-08_16:22",),
                           ("HOSTNAME1","SERVICE1","2024-05-08_16:21",), 
                           ("HOSTNAME2","SERVICE1","2024-05-08_16:21",),
                        ]
    # Retrieve the list of timestamps
    retrieved_timestamps = storage.get_list_of_timestamps()

    assert retrieved_timestamps == expected_timestamps



@pytest.mark.parametrize(
    "routes",
    [
        (
            [
                {
                    "hostname": "HOSTNAME1", "service": "SERVICE1",
                    "route": "1.1.1.10/32", "flags": "B",
                    "route_type": "Remote", "route_protocol": "BGP_LABEL",
                    "age": "10h49m31s", "preference": "170",
                    "next_hop": "10.20.30.40", "interface_next_hop": "tunneled:SR-ISIS:530001",
                    "metric": "100"
                },
                {
                    "hostname": "HOSTNAME1","service": "SERVICE1",
                    "route": "2.2.2.20/32", "flags": "L",
                    "route_type": "Local", "route_protocol": "ISIS",
                    "age": "00h08m44s", "preference": "18",
                    "next_hop": "10.190.144.128", "interface_next_hop": None,
                    "metric": "100112222"
                },
                {
                    "hostname": "HOSTNAME1", "service": "SERVICE1",
                    "route": "2.2.2.21/32", "flags": "L",
                    "route_type": "Local", "route_protocol": "ISIS",
                    "age": "00h08m44s", "preference": "18",
                    "next_hop": "10.190.144.128", "interface_next_hop": None,
                    "metric": "100112222"
                },
                {
                    "hostname": "HOSTNAME2", "service": "SERVICE1",
                    "route": "2.2.2.21/32", "flags": "L",
                    "route_type": "Local", "route_protocol": "ISIS",
                    "age": "00h08m44s", "preference": "18",
                    "next_hop": "10.190.144.128", "interface_next_hop": None,
                    "metric": "100112222"
                }
            ]

        ),
        # Add more test cases with different routes being removed
    ]
)
def test_get_latest_timestamps(routes, test_db):
    """
    Test storage.get_latest_timestamps
    save routes to the database with different timestamps
    Retrive the list of timestamps from the database using storage.get_latest_timestamps for a specific hostname and service
    Assert the tuple of timestamps returned by storage.get_latest_timestamps is correct
    """
    # Save routes with different timestamps
    timestamps = [
        "2024-05-08_16:21",
        "2024-05-08_16:22",
        "2024-05-08_16:23",
    ]
    # Initialize the database
    # database_connection = storage._initialize_database(":memory:")

    storage.save_routes(timestamps[0], routes,)
    storage.save_routes(timestamps[1], routes,)
    storage.save_routes(timestamps[2], routes,)
    
    expected_timestamp1 = "2024-05-08_16:23" 
    expected_timestamp2 = "2024-05-08_16:22"
                           
    # Retrieve the list of timestamps
    retrieved_timestamps = storage.get_latest_timestamps("HOSTNAME1","SERVICE1",)

    assert retrieved_timestamps == (expected_timestamp1, expected_timestamp2)

    # Destroy database when test case ends
    # storage._destroy_database(database_connection)



ROUTES_TEST = [
                {
                    "hostname": "HOSTNAME1", "service": "SERVICE1",
                    "route": "1.1.1.10/32", "flags": "B",
                    "route_type": "Remote", "route_protocol": "BGP_LABEL",
                    "age": "10h49m31s", "preference": "170",
                    "next_hop": "10.20.30.40", "interface_next_hop": "tunneled:SR-ISIS:530001",
                    "metric": "100"
                },
                {
                    "hostname": "HOSTNAME1","service": "SERVICE1",
                    "route": "2.2.2.20/32", "flags": "L",
                    "route_type": "Local", "route_protocol": "ISIS",
                    "age": "00h08m44s", "preference": "18",
                    "next_hop": "10.190.144.128", "interface_next_hop": None,
                    "metric": "100112222"
                },
                {
                    "hostname": "HOSTNAME1", "service": "SERVICE1",
                    "route": "2.2.2.21/32", "flags": "L",
                    "route_type": "Local", "route_protocol": "ISIS",
                    "age": "00h08m44s", "preference": "18",
                    "next_hop": "10.190.144.128", "interface_next_hop": None,
                    "metric": "100112222"
                },
                {
                    "hostname": "HOSTNAME2", "service": "SERVICE2",
                    "route": "2.2.2.21/32", "flags": "L",
                    "route_type": "Local", "route_protocol": "ISIS",
                    "age": "00h08m44s", "preference": "18",
                    "next_hop": "10.190.144.128", "interface_next_hop": None,
                    "metric": "100112222"
                }
            ]



@pytest.mark.parametrize(
    "routes, hostname, service, timestamp_to_save, timestamp_to_get, expected_number_of_routes, expected_routes",
    [
        # Test case 1: first host routes
        (
            ROUTES_TEST,
            "HOSTNAME1",
            "SERVICE1",
            "2024-05-08_16:21",
            "2024-05-08_16:21",
            3,
            ["1.1.1.10/32", "2.2.2.20/32", "2.2.2.21/32"]
        ),
        # Test case 2: second host routes
        (
            ROUTES_TEST,
            "HOSTNAME2",
            "SERVICE2",
            "2024-05-08_16:21",
            "2024-05-08_16:21",
            1,
            ["2.2.2.21/32"]
        ),
        # Test case 3: host not found
        (
            ROUTES_TEST,
            "HOSTNAME3",
            "SERVICE1",
            "2024-05-08_16:21",
            "2024-05-08_16:21",
            0,
            []
        ),
        # Test case 4: service not found
        (
            ROUTES_TEST,
            "HOSTNAME1",
            "SERVICE3",
            "2024-05-08_16:21",
            "2024-05-08_16:21",
            0,
            []
        ),
        # Test case 5: timestamp not found
        (
            ROUTES_TEST,
            "HOSTNAME1",
            "SERVICE1",
            "2024-05-08_16:22",
            "2024-05-08_16:21",
            0,
            []
        ),
    ]   
)

def test_get_routes_when_more_than_one_hostname_and_service(routes, hostname, service, timestamp_to_save, timestamp_to_get, expected_number_of_routes, expected_routes, test_db):
    """
    Test storage.get_routes under diffenrent conditions when more than one host is saved
    """

    storage.save_routes(timestamp_to_save, routes,)

    # Retrieve the routes
    retrieved_routes = storage.get_routes(hostname, service, timestamp_to_get,)

    assert len(retrieved_routes) == expected_number_of_routes
    assert [route_item["route"] for route_item in retrieved_routes ].sort() == expected_routes.sort()

