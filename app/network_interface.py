"""
network_interface.py is an interface to send commands to multiple devices using threads and netmiko.
the script receives a list of devices with the following format:
{
    "device_type": vendor or type of device, (options include cisco_xe, cisco_xr, nokia, etc)
    "ip": ip address of the device, 
    "hostname": hostname, 
    "username": username, 
    "password": password, 
    "proxy: : (optional) proxy to use, 
    "commands": [ list of commands to send to the device in order of execution ], 
    other arguments for netmiko : value,
}


the script will generate a thread and on each thread will try to connect to the device and send the commands.
the result of each thread is put into another queue and the format of the response dictionary is as follows:
{
    "hostname" : hostname of the device,
    "ip" : ip address of the device,
    "output" : { comand1: output of command1, command2: output of command2, ... }
    "error" : error message if there was an error, if not then an empty string "",
}

The idea of the script is to be callable from another module. 
This script tries not to process the output in any way.
"""


from threading import Thread, get_native_id
from multiprocessing.pool import ThreadPool
from queue import Queue
import concurrent.futures

import os
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Starting {os.path.basename(__file__)}",)

from time import sleep
from random import random
import re

import socks 
from netmiko.exceptions import NetMikoAuthenticationException, NetMikoTimeoutException
from netmiko import ConnectHandler


# producer task
def producer_task(devices_queue, output_queue):
    def get_output(connection_handler, command):
        timeout = 360
        output = connection_handler.send_command_timing(command, read_timeout=timeout)
        return output
   
    def is_connected(net_connect, ip):
        try:
            net_connect.is_alive()
        except:
            print(">Producer: is {} alive -> {}".format(ip, False ))
            return False
        
        if net_connect.is_alive():
            print(">Producer: is {} alive -> {}".format(ip, True ))
            return True
        else:
            print(">Producer: is {} alive -> {}".format(ip, False ))
            return False
    
    logger.debug(f"producer_task {get_native_id()} started")    
    while True:
        # Get the dict of the next device to process
        device_dict = devices_queue.get()
        # Set the basic responde if there is an error in the processing of this device
        logger.debug(f">Producer {get_native_id()} found device: {device_dict}")

        if device_dict is None:
            devices_queue.put(None)
            logger.debug(f">Producer {get_native_id()} found no more devices. Shutting down")
            return
        logger.debug(f">Entering Producer {get_native_id()}, device:{device_dict.get('hostname')} ip: {device_dict.get('ip')}")

        # Save some values from the device_dict that later will be removed to acommodate the dictionary for 'ConnectHandler'
        hostname = device_dict.get("hostname")
        proxy_info = device_dict.get("proxy")
        commands = device_dict.get("commands")
        del device_dict["commands"]

        if device_dict.get("hostname"):
            # Remove hostname key from dictionary because 'ConnectHandler' doesn't use it
            del device_dict["hostname"]
        else:
            # Malformed dictionary, continue with next device in the queue
            logger.error(f">Producer {get_native_id()} malformed dictionary doesn't contain the 'hostname' key: {device_dict}")
            continue
       
        # PROXY
        # For device_dict to use a proxy, it must contain a "proxy" keyword
        # The value of the "proxy" keyword must contain a dictionary with all arguments to set a socks object
        NO_RESPONSE_DICT = {"output": {}}
        if device_dict.get("proxy"):
            logger.info(f">Producer {get_native_id()}. Device:{hostname} IP:{device_dict.get('ip')} has a proxy: {proxy_info}")
            sock = socks.socksocket()
            sock.set_proxy(
                **device_dict.get('proxy')
            )

            # If something goes wrong when connecting to the proxy, then put an error dictionary on the 
            # output queue and continue with the next device in the queue
            NO_RESPONSE_DICT["hostname"] = hostname
            NO_RESPONSE_DICT["ip"] = device_dict.get('ip')
            try:
                device_dict.get("sock").connect((device_dict.get('ip'), 22)) 
            except (socks.GeneralProxyError, socks.ProxyConnectionError) as exc:
                NO_RESPONSE_DICT["error"] = "ProxyConnectionError"
                output_queue.put(NO_RESPONSE_DICT)
                # send a debug message to inform the exception, and send an error message to the user to explain what went wrong with this device
                logger.error(f"hostname: {hostname}, ip: {device_dict.get('ip')}, Error connecting to the proxy {proxy_info}")
                logger.debug(f">Producer {get_native_id()} hostname: {hostname}, ip: {device_dict.get('ip')}, Error connecting to the proxy {proxy_info}",exc_info = exc)
                continue
            except (socks.ProxyAuthenticationError, socks.SOCKS5AuthError) as exc:
                NO_RESPONSE_DICT["error"] = "ProxyAuthenticationError"
                output_queue.put(NO_RESPONSE_DICT)
                logger.error(f"hostname: {hostname}, ip: {device_dict.get('ip')}, Error connecting to the proxy {proxy_info}")
                logger.debug(f">Producer {get_native_id()} hostname: {hostname}, ip: {device_dict.get('ip')}, Error connecting to the proxy {proxy_info}" ,exc_info = exc)
                continue
            except socks.ProxyTimeoutError as exc:
                NO_RESPONSE_DICT["error"] = "ProxyTimeout"
                output_queue.put(NO_RESPONSE_DICT)
                logger.error(f"hostname: {hostname}, ip: {device_dict.get('ip')}, Error connecting to the proxy {proxy_info}")
                logger.debug(f">Producer {get_native_id()} hostname: {hostname}, ip: {device_dict.get('ip')}, Error connecting to the proxy {proxy_info}" ,exc_info = exc)
                continue
            except socks.SOCKS5Error as exc:
                NO_RESPONSE_DICT["error"] = "SOCKS5Error"
                output_queue.put(NO_RESPONSE_DICT)
                logger.error(f"hostname: {hostname}, ip: {device_dict.get('ip')}, Error connecting to the proxy {proxy_info}")
                logger.debug(f">Producer {get_native_id()} hostname: {hostname}, ip: {device_dict.get('ip')}, Error connecting to the proxy {proxy_info}" ,exc_info = exc)
                continue
            except Exception as exc:
                NO_RESPONSE_DICT["error"] = "UnknownError"
                output_queue.put(NO_RESPONSE_DICT)
                logger.error(f"hostname: {hostname}, ip: {device_dict.get('ip')}, Error connecting to the proxy {proxy_info}")
                logger.debug(f">Producer {get_native_id()} hostname: {hostname}, ip: {device_dict.get('ip')}, Error connecting to the proxy {proxy_info}" ,exc_info = exc)
                continue
            # Proxy connected and key 'proxy' can now be removed for later usage in 'ConnectHandler'
            device_dict['sock'] = sock
            del device_dict["proxy"]
            logger.info(f"hostname: {hostname}, ip: {device_dict.get('ip')}: Sock connected")

        NO_RESPONSE_DICT["error"] = ""
        for retry in range(0,3):
            sleep(random() * retry * 10)
            
            # Connect to the device, and print out auth or timeout errors
            try:
                logger.info(f">Producer {get_native_id()}: Connecting to hostname {hostname} ip {device_dict.get('ip')} retry {retry}")
                net_connect_generic_pe = ConnectHandler(**device_dict) 
            except NetMikoTimeoutException as exc:
                logger.warning(f"hostname {hostname} ip {device_dict.get('ip')} Connection timeout. retry {retry}")
                NO_RESPONSE_DICT["error"] += "Timeout,"
            except NetMikoAuthenticationException as exc:
                logger.warning(f"hostname {hostname} ip {device_dict.get('ip')} Authentication failed. retry {retry}")
                NO_RESPONSE_DICT["error"] += "AuthenticationFailed,"
            except Exception as err:
                logger.warning(f"hostname {hostname} ip {device_dict.get('ip')} Unkown exception. retry {retry}")
                logger.debug(f"hostname {hostname} ip {device_dict.get('ip')} Unkown exception. retry {retry}",exc_info = err)
                NO_RESPONSE_DICT["error"] += "UnknownError,"
            else:
                logger.info("{}: SUCCESS: Authentication OK for {}.".format(hostname, device_dict.get('ip')))
                break # device is connected, break 'for loop', no need to retry
        else:
            #number of retries reached, can't connect to device
            logger.error(f"hostname: {hostname}, ip: {device_dict.get('ip')}, Maximum number of retries reached")
            NO_RESPONSE_DICT["hostname"] = hostname
            NO_RESPONSE_DICT["ip"] = device_dict.get('ip')
            NO_RESPONSE_DICT["output"] = {}
            NO_RESPONSE_DICT["error"] += "MaximumNumberRetriesReached"
            output_queue.put(NO_RESPONSE_DICT)
            continue
        
        if net_connect_generic_pe and not is_connected(net_connect_generic_pe, device_dict.get("ip")):
            # Device connection is not alive, put the error in the output_queue and continue witht he next device in the device_queue
            NO_RESPONSE_DICT["hostname"] = hostname
            NO_RESPONSE_DICT["ip"] = device_dict.get('ip')
            NO_RESPONSE_DICT["output"] = {}
            NO_RESPONSE_DICT["error"] = "ConnectionNotAlive"
            output_queue.put(NO_RESPONSE_DICT)
            continue

        RESPONSE_DICT = {}
        RESPONSE_DICT["hostname"] = hostname
        RESPONSE_DICT["ip"] = device_dict.get('ip')
        RESPONSE_DICT["output"] = {}
        RESPONSE_DICT["error"] = ""

        for command in commands:
            logger.debug(f">Producer {get_native_id()} hostname: {hostname}, ip: {device_dict.get('ip')}, command: {command}")
            logger.info(f"Executing {command} on hostname: {hostname}")
            RESPONSE_DICT["output"][command] = get_output(net_connect_generic_pe, command)
        else:
            logger.debug(f">Producer {get_native_id()} processed commands for hostname: {hostname}, ip: {device_dict.get('ip')}")
            # logger.debug(f">Producer {get_native_id()} result for hostname: {hostname}, output: {RESPONSE_DICT}")
            output_queue.put(RESPONSE_DICT)
            

# producer manager task
# def producer_manager(number_of_threads:int, devices_queue:Queue, output_queue:Queue):
#     logger.debug(f"producer_manager {get_native_id()} started")
#     # create thread pool
#     with ThreadPool(number_of_threads) as pool:
#         # use threads to generate items and put into the queue
#         logger.debug(f"Started pool with {number_of_threads} threads")
#         _ = [pool.apply_async(producer_task, args=(devices_queue,output_queue)) for _ in range(number_of_threads)]
#         # wait for all tasks to complete
#         logger.debug(f"Producer_manager {get_native_id()} waiting for all tasks to complete")
#     # pool.close()
#     pool.join()
#     # put a signal to expect no further tasks results
#     output_queue.put(None)
#     # report a message
#     logger.info('>Producer_manager processed all devices')


# def execute_devices_commands(devices:list):
#     logger.debug("execute_devices_commands")
#     devices_queue = Queue()
#     for device in devices:
#         devices_queue.put(device)
#     else:
#         devices_queue.put(None)
    
#     logger.debug(f"devices_queue: {devices_queue}")

#     output_queue = Queue()
#     number_of_threads = min(len(devices), os.cpu_count() * 4)
#     logger.debug(f"number_of_threads: {number_of_threads}")

#     producer = Thread(target=producer_manager, args=(number_of_threads, devices_queue, output_queue,))
#     logger.debug(f"Starting producer: {producer}")
#     producer.start()
#     logger.debug(f"Waiting for producer: {producer}")
#     producer.join()
#     logger.debug(f"Finished producer: {producer}")

#     output_list = []
#     while not output_queue.empty():
#         data = output_queue.get()
#         if data is None:
#             _ = output_queue.get()
#             continue
#         output_list.append(output_queue.get())
#     return output_list


def execute_devices_commands(devices:list):
    logger.debug("execute_devices_commands")
    devices_queue = Queue()
    for device in devices:
        devices_queue.put(device)
    else:
        devices_queue.put(None)
    output_queue = Queue()
    number_of_workers = min(len(devices), os.cpu_count() * 4)
    logger.debug(f"number_of_threads: {number_of_workers}")

    output_list = list()
    with concurrent.futures.ThreadPoolExecutor(max_workers=number_of_workers) as executor:
        future_to_devices = {executor.submit(producer_task, devices_queue, output_queue): device for device in devices}
        for future in concurrent.futures.as_completed(future_to_devices):
            dev = future_to_devices[future]
            try:
                data = future.result()
            except Exception as exc:
                logger.debug(f"{dev}: Exception generated {exc}")
            else:
                logger.debug(f"DATA = {dev}\n{data}")
                # output_list.append(data)
    
    counter = 0
    while not output_queue.empty():
        logger.debug(f"Getting data from output_queue {counter}")
        counter += 1
        data = output_queue.get()
        if data is None:
            continue
        output_list.append(data)
    return output_list