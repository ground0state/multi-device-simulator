'''
/*
 * Copyright 2019 ground0state. All Rights Reserved.
 * Released under the MIT license
 * https://opensource.org/licenses/mit-license.php
/
/*
 * Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */
 '''

import argparse
import json
import logging
import threading
import time
from datetime import datetime

import socks
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from generator.ARIMA_generator import ARIMA111

AllowedActions = ['both', 'publish', 'subscribe']


# Configure logging
now = datetime.today().strftime('%Y%m%d%H%M%S')
logger = logging.getLogger("clien.py")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
fileHandler = logging.FileHandler(filename=f"./logs/{now}.log", mode='a')
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
fileHandler.setFormatter(formatter)
logger.addHandler(streamHandler)
logger.addHandler(fileHandler)
logger.debug(f"start script")


with open('conf/setting.json') as f:
    args = json.load(f)

host = args["endpoint"]
rootCAPath = args["rootCAPath"]
certificatePath = args["certificatePath"]
privateKeyPath = args["privateKeyPath"]
port = args["port"]
useWebsocket = args["useWebsocket"]
clientIdList = args["clientIdList"]
topic = args["topic"]
numOfSensors = args["numOfSensors"]
mode = args["mode"]

useProxy = args["useProxy"]
proxyAddr = args["proxyAddr"]
proxyPort = args["proxyPort"]
proxyType = args["proxyType"]

logger.debug(f"host: {host}")
logger.debug(f"port: {port}")
logger.debug(f"clientId: {clientIdList}")
logger.debug(f"topic: {topic}")
logger.debug(f"mode: {mode}")
logger.debug(f"numOfSensors: {numOfSensors}")

if mode not in AllowedActions:
    logger.debug(("Unknown --mode option %s. Must be one of %s" %
                  (mode, str(AllowedActions))))
    raise ValueError(
        ("Unknown --mode option %s. Must be one of %s" % (mode, str(AllowedActions))))

if useWebsocket and certificatePath and privateKeyPath:
    logger.debug(
        "X.509 cert authentication and WebSocket are mutual exclusive. Please pick one.")
    raise ValueError(
        "X.509 cert authentication and WebSocket are mutual exclusive. Please pick one.")

if not useWebsocket and (not certificatePath or not privateKeyPath):
    logger.debug("Missing credentials for authentication.")
    raise ValueError("Missing credentials for authentication.")

if numOfSensors <= 0:
    logger.debug("Number of sensors must be positive.")
    raise ValueError("Number of sensors must be positive.")


# Port defaults
if useWebsocket and not port:  # When no port override for WebSocket, default to 443
    port = 443
if not useWebsocket and not port:  # When no port override for non-WebSocket, default to 8883
    port = 8883


class MyAWSIoTMQTTClient():

    def __init__(self, logger, clientId, numOfSensors, host, port, rootCAPath, privateKeyPath, certificatePath, useWebsocket=None, useProxy=False, proxyAddr=None, proxyPort=None, proxyType=None):
        # Init AWSIoTMQTTClient
        myAWSIoTMQTTClient = None
        if useWebsocket:
            myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
            myAWSIoTMQTTClient.configureEndpoint(host, port)
            myAWSIoTMQTTClient.configureCredentials(rootCAPath)
        else:
            myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
            myAWSIoTMQTTClient.configureEndpoint(host, port)
            myAWSIoTMQTTClient.configureCredentials(
                rootCAPath, privateKeyPath, certificatePath)

        # AWSIoTMQTTClient connection configuration
        myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
        # Infinite offline Publish queueing
        myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)
        myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
        myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
        myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

        # AWSIoTMQTTClient socket configuration
        # import pysocks to help us build a socket that supports a proxy configuration
        if useProxy:
            # set proxy arguments (for SOCKS5 proxy: proxy_type=2, for HTTP proxy: proxy_type=3)
            proxy_config = {"proxy_addr": proxyAddr,
                            "proxy_port": proxyPort, "proxy_type": proxyType}
            # create anonymous function to handle socket creation
            def socket_factory(): return socks.create_connection((host, port), **proxy_config)
            myAWSIoTMQTTClient.configureSocketFactory(socket_factory)

        self.myAWSIoTMQTTClient = myAWSIoTMQTTClient
        self.logger = logger
        self.clientId = clientId
        self.sensor_list = [clientId + "-" + "sensor" +
                            str(i+1) for i in range(numOfSensors)]
        self.data_generator_list = [ARIMA111() for i in range(numOfSensors)]

    def run(self, mode="both"):
        # Connect and subscribe to AWS IoT
        self.myAWSIoTMQTTClient.connect()
        if mode == 'both' or mode == 'subscribe':
            self.logger.debug(f"{self.clientId}: subscribe start")
            self.myAWSIoTMQTTClient.subscribe(topic, 1, self._customCallback)
        time.sleep(2)

        # Publish to the same topic in a loop forever
        self.logger.debug(f"{self.clientId}: publish start")
        try:
            while True:
                if mode == 'both' or mode == 'publish':
                    t = int(time.time())
                    for sensorName, data_generator in zip(self.sensor_list, self.data_generator_list):
                        message = {}
                        message['device'] = sensorName
                        message['value'] = data_generator.get_value(p=0.01)
                        message['timestamp'] = t*1000
                        messageJson = json.dumps(message)
                        self.myAWSIoTMQTTClient.publish(topic, messageJson, 1)
                        if mode == 'publish':
                            print('Published topic %s: %s\n' %
                                  (topic, messageJson))
                time.sleep(0.5)

        except KeyboardInterrupt as e:
            self.logger.debug(
                f"KeyboardInterrupt: {datetime.today().strftime('%Y%m%d%H%M%S')}")

        except Exception:
            self.logger.debug(
                f"Other error: {datetime.today().strftime('%Y%m%d%H%M%S')}")

    # Custom MQTT message callback
    def _customCallback(self, client, userdata, message):
        print("Received a new message: ")
        print(message.payload)
        print("from topic: ")
        print(message.topic)
        print("--------------\n\n")


wokers = []

for clientId in clientIdList:
    worker = None
    worker = MyAWSIoTMQTTClient(logger, clientId, numOfSensors,
                                host, port, rootCAPath, privateKeyPath, certificatePath)

    t = threading.Thread(target=worker.run, args=(mode,))
    t.start()
    wokers.append(t)
