import json
import logging
import paho.mqtt.client as paho
import ssl

from utils.custom_logging import Logger
from simple_chalk import blueBright, yellowBright, greenBright, white, whiteBright
from time import sleep

file = open("./data/device.json")
device = json.load(file)
file.close()

# Refactored original source - https://gist.github.com/skirdey/9cdead881799a47742ff3cd296d06cc1
# Reference: https://aws.amazon.com/blogs/iot/use-aws-iot-core-mqtt-broker-with-standard-mqtt-libraries/

class Broadcaster(object):

    def __init__(self, listener = False, topic = "default"):
        self.logger = Logger("Broadcaster")
        
        self.is_connected = False
        self.listener = listener
        self.topic = f"{device['thingName']}/{topic}"

    def __on_connect(self, client, userdata, flags, rc, properties):
        if rc == "Success":
            self.logger.info(f"Connected to endpoint {blueBright(device['awshost'])} with result code {blueBright(rc)}")
            self.is_connected = True
            if self.listener:
                self.mqttc.subscribe(self.topic)
        else:
            self.logger.warn(f"There was a problem establishing a connection. Result code: {yellowBright(rc)}")


    def __on_message(self, client, userdata, msg):
        self.logger.debug(f"__on_message userdata: {userdata}")
        self.logger.info("__on_message (Topic)" + blueBright(self.logger.sep) + whiteBright(msg.topic))
        self.logger.info("__on_message (Payload)" + blueBright(self.logger.sep) + whiteBright(msg.payload))

    def __on_publish(self, client, userdata, mid, rc, properties):
        self.logger.info(f"__on_publish rc: {rc}")
        self.mqttc.loop_stop()
    
    def __on_log(self, client, userdata, level, buf):
        self.logger.log(self.logger.sep + greenBright(buf))

    def broker_connect(self):
        self.logger.info("Initializing paho Client broker...")
        self.mqttc = paho.Client(
            client_id=device["clientId"],
            callback_api_version=paho.CallbackAPIVersion.VERSION2,
            protocol=5
        )
        self.mqttc.on_connect = self.__on_connect
        self.mqttc.on_message = self.__on_message
        self.mqttc.on_publish = self.__on_publish
        self.mqttc.on_log = self.__on_log

        caPath = device["caPath"]

        self.mqttc.tls_set(
            ca_certs=caPath, 
            certfile=device["certPath"], 
            keyfile=device["keyPath"], 
            tls_version=2
        )

        awshost = device["awshost"]
        awsport = device["awsport"]
        
        self.mqttc.connect(awshost,awsport,keepalive=60)
        self.logger.debug("broker_connect complete.")
        return self
    
    def broker_disconnect(self):
        self.logger.debug("broker_disconnect called.")
        self.logger.info("Disconnecting broker.")
        self.mqttc.disconnect()
        self.is_connected = False
        self.logger.debug("broker_disconnect complete.")
        return self

    def send(self, data):
        self.mqttc.loop_start()
        cnxString = "Waiting for connection..."
        while self.is_connected == False:
            self.logger.info(cnxString)
            cnxString += "."
            sleep(0.25)
        
        self.mqttc.publish(self.topic, json.dumps(data), qos=1)
        