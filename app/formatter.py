import io


def output_text(route_result):
    stream = io.StringIO()
    if route_result == None:
        stream = io.StringIO("No routes found")
        return stream.getvalue()
    

    hostname = route_result["added"][0]["hostname"]
    service = route_result["added"][0]["service"]
    print("#"*80, file=stream)
    print(f"HOSTNAME: {hostname}",file=stream)
    print(f"SERVICE: {service}",file=stream)
    print("Added routes:",file=stream)
    for route in route_result["added"]:
        print(f"+ {route['route']}",file=stream)
    
    print("Deleted routes:",file=stream)
    for route in route_result["deleted"]:
        print(f"- {route['route']}",file=stream)

    print("Modified routes:",file=stream)
    for route in route_result["changed"]:
        print(f"~ {route['route']}",file=stream)
        if route["next_hop_before"] != route["next_hop_after"]:
            print(f"  Next hop: {route['next_hop_before']} -> {route['next_hop_after']}",file=stream)

        if route["metric_before"] != route["metric_after"]:
            print(f"  Metric: {route['metric_before']} -> {route['metric_after']}",file=stream)

        if route["route_protocol_before"] != route["route_protocol_after"]:
            print(f"  Protocol: {route['route_protocol_before']} -> {route['route_protocol_after']}",file=stream)
    return stream.getvalue()




def output_csv(route_result):
    stream = io.StringIO()
    if route_result is None:
        stream = io.StringIO("No routes found")
        return stream.getvalue()
    
    hostname = route_result["added"][0]["hostname"]
    service = route_result["added"][0]["service"]
    header = "status,hostname,service,route,route_protocol,next_hop,metric"
    print(header,file=stream)
    for route in route_result["added"]:
        print(f"+added,{hostname},{service},{route['route']},{route['route_protocol']},{route['next_hop']},{route['metric']}",file=stream)
    
    for route in route_result["deleted"]:
        print(f"-deleted,{hostname},{service},{route['route']},{route['route_protocol']},{route['next_hop']},{route['metric']}",file=stream)

    for route in route_result["changed"]:
        print(f"~modified,{hostname},{service},{route['route']},{route['route_protocol_before']} -> {route['route_protocol_after']},{route['next_hop_before']} -> {route['next_hop_after']},{route['metric_before']} -> {route['metric_after']}",file=stream)

    print("",file=stream)
    return stream.getvalue()



fommatter_function = {
    "text": output_text,
    "csv": output_csv
}