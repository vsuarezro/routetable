
import pytest

import app.formatter as formatter

@pytest.fixture(scope="module") 
def test_route_dict_output():
    return {
        "added" : [
            {
                "id" : 1,
                "hostname": "HOSTNAME1",
                "service" : "SERVICE1",
                "route" : "1.1.1.1/32",
                "flags": "L",
                "route_type": "Local",
                "route_protocol": "ISIS",
                "age": "00h08m44s",
                "preference": "18",
                "next_hop": "10.190.144.128",
                "interface_next_hop": None,
                "metric": "100112222"
            },
            {
                "id" : 2,
                "hostname": "HOSTNAME1",
                "service" : "SERVICE1",
                "route" : "1.1.0.0/16",
                "flags": "L",
                "route_type": "Local",
                "route_protocol": "ISIS",
                "age": "00h08m44s",
                "preference": "18",
                "next_hop": "10.190.144.128",
                "interface_next_hop": None,
                "metric": "100112222"
            },
        ],
        "deleted" : [
            {
                "id" : 3,
                "hostname": "HOSTNAME1",
                "service" : "SERVICE1",
                "route" : "2.2.2.2/32",
                "flags": "L",
                "route_type": "Local",
                "route_protocol": "ISIS",
                "age": "00h08m44s",
                "preference": "18",
                "next_hop": "10.190.144.128",
                "interface_next_hop": None,
                "metric": "100112222"
            },
            {
                "id" : 4,
                "hostname": "HOSTNAME1",
                "service" : "SERVICE1",
                "route" : "2.2.0.0/16",
                "flags": "L",
                "route_type": "Local",
                "route_protocol": "ISIS",
                "age": "00h08m44s",
                "preference": "18",
                "next_hop": "10.190.144.128",
                "interface_next_hop": None,
                "metric": "100112222"
            },
        ],
        "changed" : [
            {
                "route" : "3.3.3.1/32",
                "next_hop_before" : "10.3.3.1" ,
                "next_hop_after" : "10.3.3.2",
                "metric_before" : "100",
                "metric_after" : "200",
                "route_protocol_before" : "ISIS",
                "route_protocol_after" : "BGP_LABEL",
            },
            {
                "route" : "3.3.3.2/32",
                "next_hop_before" : "10.3.3.1" ,
                "next_hop_after" : "10.3.3.1",
                "metric_before" : "100",
                "metric_after" : "100",
                "route_protocol_before" : "ISIS",
                "route_protocol_after" : "BGP_LABEL",
            },
            {
                "route" : "3.3.3.3/32",
                "next_hop_before" : "10.3.3.1" ,
                "next_hop_after" : "10.3.3.1",
                "metric_before" : "100",
                "metric_after" : "200",
                "route_protocol_before" : "ISIS",
                "route_protocol_after" : "ISIS",
            },
            {
                "route" : "3.3.3.4/32",
                "next_hop_before" : "10.3.3.1" ,
                "next_hop_after" : "10.3.3.2",
                "metric_before" : "100",
                "metric_after" : "100",
                "route_protocol_before" : "ISIS",
                "route_protocol_after" : "ISIS",
            }
        ],

    }

@pytest.fixture(scope="module") 
def test_hostname():
    return "HOSTNAME1"

@pytest.fixture(scope="module") 
def test_service():
    return "SERVICE1"

@pytest.fixture(scope="module") 
def test_timestamp1():
    return "2023-04-03_13:00"


@pytest.fixture(scope="module") 
def test_timestamp2():
    return "2023-04-05_23:00"



def test_output_text(test_route_dict_output, test_hostname, test_service, test_timestamp1, test_timestamp2):
    print(formatter.output_text(test_route_dict_output,test_hostname, test_service, test_timestamp1, test_timestamp2))
    output = formatter.output_text(test_route_dict_output,test_hostname, test_service, test_timestamp1, test_timestamp2)
    assert output is not None
    assert "Added" in output
    assert "Deleted" in output
    assert "Modified" in output


def test_output_csv(test_route_dict_output):
    print(formatter.output_csv(test_route_dict_output,test_hostname, test_service, test_timestamp1, test_timestamp2))
    output = formatter.output_csv(test_route_dict_output,test_hostname, test_service, test_timestamp1, test_timestamp2)
    assert output is not None
    assert "status,hostname,service,route,route_protocol,next_hop,metric" in output
    assert "+added" in output
    assert "-deleted" in output
    assert "~modified" in output


@pytest.mark.skip(reason="not yet implemented")
def test_output_table(test_route_dict_output):
    print(formatter.output_table(test_route_dict_output))
    assert formatter.output_table(test_route_dict_output)

def test_output_json(test_route_dict_output):
    print(formatter.output_json(test_route_dict_output,test_hostname, test_service, test_timestamp1, test_timestamp2))
    output = formatter.output_json(test_route_dict_output,test_hostname, test_service, test_timestamp1, test_timestamp2)
    assert output is not None
    assert "added" in output
    assert "deleted" in output
    assert "changed" in output


def test_output_xml(test_route_dict_output):
    print(formatter.output_xml(test_route_dict_output,test_hostname, test_service, test_timestamp1, test_timestamp2), )
    output = formatter.output_xml(test_route_dict_output,test_hostname, test_service, test_timestamp1, test_timestamp2)
    assert output is not None   

def test_output_yaml(test_route_dict_output):
    print(formatter.output_yaml(test_route_dict_output,test_hostname, test_service, test_timestamp1, test_timestamp2))
    output = formatter.output_yaml(test_route_dict_output,test_hostname, test_service, test_timestamp1, test_timestamp2)
    assert output is not None
    assert "added" in output
    assert "deleted" in output
    assert "changed" in output