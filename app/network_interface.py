from threading import Thread, get_native_id
from multiprocessing.pool import ThreadPool
from queue import Queue

import os
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.info(f"Starting {os.path.basename(__file__)}",)

from time import sleep
from random import random
import re

import socks 
from netmiko.exceptions import NetMikoAuthenticationException, NetMikoTimeoutException
from netmiko import ConnectHandler

# producer task
def producer_task(devices_queue, output_queue):
    hostname_re = re.compile("hostname ([\w\-]+)", re.M)
   
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
    
    while True:
        # Get the dict of the next device to process
        device_dict = devices_queue.get()
        # Set the basic responde if there is an error in the processing of this device
        NO_RESPONSE_DICT = {"output": None}
        # Save some values from the device_dict that later will be removed to acommodate the dictionary for 'ConnectHandler'
        hostname = device_dict.get("hostname")
        proxy_info = device_dict.get("proxy") if device_dict.get("proxy") else None
        commands = device_dict.get("commands")
        del device_dict["commands"]

        if device_dict is None:
            devices_queue.put(None)
            logger.debug(f">Producer {get_native_id()} found no more devices. Shutting down")
            return
        logger.debug(f">Entering Producer {get_native_id()}, device:{hostname} ip: {device_dict.get('ip')}")

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
            NO_RESPONSE_DICT["output"] = None
            NO_RESPONSE_DICT["error"] += "MaximumNumberRetriesReached"
            output_queue.put(NO_RESPONSE_DICT)
            continue
        
        if net_connect_generic_pe and not is_connected(net_connect_generic_pe, device_dict.get("ip")):
            # Device connection is not alive, put the error in the output_queue and continue witht he next device in the device_queue
            NO_RESPONSE_DICT["hostname"] = hostname
            NO_RESPONSE_DICT["ip"] = device_dict.get('ip')
            NO_RESPONSE_DICT["output"] = None
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
            RESPONSE_DICT["output"][command] = get_output(net_connect_generic_pe, command)
        else:
            queue.put(RESPONSE_DICT)
            logger.info(f">Producer {get_native_id()} processed commands for hostname: {hostname}, ip: {device_dict.get('ip')}")

# producer manager task
def producer_manager(number_of_threads:int, devices_queue:Queue, output_queue:Queue):
    # create thread pool
    with ThreadPool(number_of_threads) as pool:
        # use threads to generate items and put into the queue
        _ = [pool.apply_async(producer_task, args=(devices_queue,output_queue)) for _ in range(number_of_threads)]
        # wait for all tasks to complete
        pool.close()
        pool.join()
    # put a signal to expect no further tasks
    devices_queue.put(None)
    # report a message
    logger.info('>Producer_manager processed all devices')
