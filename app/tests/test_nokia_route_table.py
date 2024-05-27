import pytest

import app.nokia.grammar as ngrammar

@pytest.fixture
def route_table():
    return """===============================================================================
Route Table (Router: Base)
===============================================================================
Dest Prefix[Flags]                            Type    Proto     Age        Pref
      Next Hop[Interface Name]                                    Metric   
-------------------------------------------------------------------------------
1.1.1.1/32 [B]                                Remote  BGP_LABEL 10h43m16s  170
       10.190.3.146 (tunneled:SR-ISIS:310032)                       441
10.0.1.2/32 [L]                               Remote  ISIS      00h08m44s  18
       10.190.144.128                                               192
10.0.3.3/32 [L]                               Remote  ISIS      25d20h48m  18
       10.190.144.128                                               83
10.32.68.4/32 [B]                             Remote  BGP VPN   01d00h03m  170
       10.190.126.2 (tunneled:BGP)                                  1004
10.32.219.5/24                                Remote  BGP VPN   09h21m20s  170
       10.190.3.235 (tunneled:SR-ISIS:373749)                       25
10.33.15.6/32 [B]                             Remote  BGP VPN   09h21m14s  170
       10.190.118.2 (tunneled:SR-ISIS:404083)                       26
10.38.145.7/30                                Local   Local     0241d11h   0
       INTERFACE-NAME_1                                             0
10.38.147.8/29                                Local   Local     0241d11h   0
       INTERFACE-NAME_2                                             0
10.38.147.9/29                                Remote  BGP VPN   87d10h57m  170
       10.190.0.57 (tunneled:SR-ISIS:540152)                        37
10.38.147.10/32                               Remote  Static    0241d11h   5
       10.38.147.2                                                  100
10.38.147.11/32                               Remote  Static    0241d11h   5
       10.38.147.2                                                  100
10.38.147.12/30                               Remote  BGP VPN   87d10h57m  170
       10.100.0.57 (tunneled:SR-ISIS:5400001)                        400
10.170.38.13/31                               Local   Local     0146d07h   0
       To REMOTE-HOSTNAME                                           0
10.147.0.14/16                                Blackh* Static    0365d12h   5
       Black Hole                                                   1
10.244.47.15/30                               Remote  BGP VPN   04h58m35s  170
       10.240.97.254 (tunneled)                                     100
10.56.12.16/30                                Remote  BGP VPN   05h03m23s  0
       Local VRF [1000000:interface_NAME_TO_hostnam*"               0
10.0.77.17/30                                 Remote  BGP VPN   05h03m23s  0
       Local VRF [1000000:INTERFACE_NAME_short_1]                   0
    """


expected_result = [
    {
    "route": "1.1.1.1/32",
    "flags": "B",
    "route_type": "Remote",
    "route_protocol": "BGP_LABEL",
    "age": "10h43m16s",
    "preference": "170",
    "next_hop": "10.190.3.146",
    "interface_next_hop": "tunneled:SR-ISIS:310032",
    "metric": "441"
    },
    {
    "route": "10.0.1.2/32",
    "flags": "L",
    "route_type": "Remote",
    "route_protocol": "ISIS",
    "age": "00h08m44s",
    "preference": "18",
    "next_hop": "10.190.144.128",
    "interface_next_hop": None,
    "metric": "192"
    },
    {
    "route": "10.0.3.3/32",
    "flags": "L",
    "route_type": "Remote",
    "route_protocol": "ISIS",
    "age": "25d20h48m",
    "preference": "18",
    "next_hop": "10.190.144.128",
    "interface_next_hop": None,
    "metric": "83"
    },
    {
    "route": "10.32.68.4/32",
    "flags": "B",
    "route_type": "Remote",
    "route_protocol": "BGP VPN",
    "age": "01d00h03m",
    "preference": "170",
    "next_hop": "10.190.126.2",
    "interface_next_hop": "tunneled:BGP",
    "metric": "1004"
    },
    {
    "route": "10.32.219.5/24",
    "flags": None,
    "route_type": "Remote",
    "route_protocol": "BGP VPN",
    "age": "09h21m20s",
    "preference": "170",
    "next_hop": "10.190.3.235",
    "interface_next_hop": "tunneled:SR-ISIS:373749",
    "metric": "25"
    },
    {
    "route": "10.33.15.6/32",
    "flags": "B",
    "route_type": "Remote",
    "route_protocol": "BGP VPN",
    "age": "09h21m14s",
    "preference": "170",
    "next_hop": "10.190.118.2",
    "interface_next_hop": "tunneled:SR-ISIS:404083",
    "metric": "26"
    },
    {
    "route": "10.38.145.7/30",
    "flags": None,
    "route_type": "Local",
    "route_protocol": "Local",
    "age": "0241d11h",
    "preference": "0",
    "next_hop": "INTERFACE-NAME_1",  # This should move to next_hop_interface, and next_hop be None
    "interface_next_hop": None,
    "metric": "0"
    },
    {
    "route": "10.38.147.8/29",
    "flags": None,
    "route_type": "Local",
    "route_protocol": "Local",
    "age": "0241d11h",
    "preference": "0",
    "next_hop": "INTERFACE-NAME_2",  # This should move to next_hop_interface, and next_hop be None
    "interface_next_hop": None,
    "metric": "0"
    },
    {
    "route": "10.38.147.9/29",
    "flags": None,
    "route_type": "Remote",
    "route_protocol": "BGP VPN",
    "age": "87d10h57m",
    "preference": "170",
    "next_hop": "10.190.0.57",  
    "interface_next_hop": "tunneled:SR-ISIS:540152",
    "metric": "37"
    },
    {
    "route": "10.38.147.10/32",
    "flags": None,
    "route_type": "Remote",
    "route_protocol": "Static",
    "age": "0241d11h",
    "preference": "5",
    "next_hop": "10.38.147.2",  
    "interface_next_hop": None,
    "metric": "100"
    },
    {
    "route": "10.38.147.11/32",
    "flags": None,
    "route_type": "Remote",
    "route_protocol": "Static",
    "age": "0241d11h",
    "preference": "5",
    "next_hop": "10.38.147.2",  
    "interface_next_hop": None,
    "metric": "100"
    },
    {
    "route": "10.38.147.12/30",
    "flags": None,
    "route_type": "Remote",
    "route_protocol": "BGP VPN",
    "age": "87d10h57m",
    "preference": "170",
    "next_hop": "10.100.0.57",  
    "interface_next_hop": "tunneled:SR-ISIS:5400001",
    "metric": "400"
    },
    {
    "route": "10.170.38.13/31",
    "flags": None,
    "route_type": "Local",
    "route_protocol": "Local",
    "age": "0146d07h",
    "preference": "0",
    "next_hop": "To REMOTE-HOSTNAME",  
    "interface_next_hop": None,
    "metric": "0"
    },
    {
    "route": "10.147.0.14/16",
    "flags": None,
    "route_type": "Blackh*",
    "route_protocol": "Static",
    "age": "0365d12h",
    "preference": "5",
    "next_hop": "Black Hole",  
    "interface_next_hop": None,
    "metric": "1"
    },
    {
    "route": "10.244.47.15/30",
    "flags": None,
    "route_type": "Remote",
    "route_protocol": "BGP VPN",
    "age": "04h58m35s",
    "preference": "170",
    "next_hop": "10.240.97.254",  
    "interface_next_hop": "tunneled",
    "metric": "100"
    },
    {
    "route": "10.56.12.16/30",
    "flags": None,
    "route_type": "Remote",
    "route_protocol": "BGP VPN",
    "age": "05h03m23s",
    "preference": "0",
    "next_hop": 'Local VRF [1000000:interface_NAME_TO_hostnam*"',  
    "interface_next_hop": None,
    "metric": "0"
    },
    {
    "route": "10.0.77.17/30",
    "flags": None,
    "route_type": "Remote",
    "route_protocol": "BGP VPN",
    "age": "05h03m23s",
    "preference": "0",
    "next_hop": 'Local VRF [1000000:INTERFACE_NAME_short_1]',  
    "interface_next_hop": None,
    "metric": "0"
    },
]

def test_nokia_igp_route_table_parse(route_table,):
    result = ngrammar.parse_output(route_table)
    print("Parsed route table:")
    print(result)
    for i in range(len(result)):
        print(result[i])
        assert result[i].get("route") == expected_result[i].get("route")
        assert result[i].get("flags") == expected_result[i].get("flags")
        assert result[i].get("route_type") == expected_result[i].get("route_type")
        assert result[i].get("route_protocol") == expected_result[i].get("route_protocol")
        assert result[i].get("age") == expected_result[i].get("age")
        assert result[i].get("preference") == expected_result[i].get("preference")
        assert result[i].get("next_hop") == expected_result[i].get("next_hop")
        assert result[i].get("interface_next_hop") == expected_result[i].get("interface_next_hop")
        assert result[i].get("metric") == expected_result[i].get("metric")



