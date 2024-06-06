import paho.mqtt.client as paho
import ssl
from time import sleep
from random import uniform
import json

import logging
logging.basicConfig(level=logging.INFO)

# Refactored original source - https://gist.github.com/skirdey/9cdead881799a47742ff3cd296d06cc1
# Reference: https://aws.amazon.com/blogs/iot/use-aws-iot-core-mqtt-broker-with-standard-mqtt-libraries/

file = open("./deviceData/device.json")
device = json.load(file)
file.close()

class PubSub(object):

    def __init__(self, listener = False, topic = "default"):
        self.is_connected = False
        self.listener = listener
        self.topic = f"{device['thingName']}/{topic}"
        self.logger = logging.getLogger(repr(self))

    def __on_connect(self, client, userdata, flags, rc, properties):
        self.logger.info("__on_connect: connected to endpoint %s with result code %s", device["awshost"], rc)
        self.logger.info("__on_connect: userdata: %s, flags: %s, properties: %s", userdata, flags, properties)
        self.logger.info("+++++_on_connect rc: {0}".format(rc))
        if rc == "Success":
            self.is_connected = True
            if self.listener:
                self.mqttc.subscribe(self.topic)


    def __on_message(self, client, userdata, msg):
        self.logger.info("__on_message: {0}, {1} - {2}".format(userdata, msg.topic, msg.payload))

    def __on_publish(self, client, userdata, mid, rc, properties):
        self.logger.info("__on_publish: client: %s, userdata: %s, mid: %s, rc: %s, properties: %s",client,userdata,mid,rc,properties)
        self.logger.info("+++++_on_publish rc: {0}".format(rc))
        self.mqttc.loop_stop()
    
    def __on_log(self, client, userdata, level, buf):
        self.logger.info("__on_log: {0}, {1}, {2}, {3}".format(client, userdata, level, buf))

    def broker_connect(self):
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
       
        return self
    
    def broker_disconnect(self):
        self.mqttc.disconnect()
        self.is_connected = False

        return self

    def send(self, data):
       
        self.mqttc.loop_start()
        cnxString = "Waiting for connection..."
        while self.is_connected == False:
            self.logger.info(cnxString)
            cnxString += "."
            sleep(0.25)
        
        self.logger.info("Publishing")
        self.mqttc.publish(self.topic, json.dumps(data), qos=1)
