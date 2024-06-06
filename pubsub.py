import paho.mqtt.client as paho
import ssl
from time import sleep
from random import uniform
import json

import logging
logging.basicConfig(level=logging.DEBUG)

# Refactored original source - https://gist.github.com/skirdey/9cdead881799a47742ff3cd296d06cc1
# Reference: https://aws.amazon.com/blogs/iot/use-aws-iot-core-mqtt-broker-with-standard-mqtt-libraries/

file = open("./deviceData/device.json")
device = json.load(file)
file.close()

class PubSub(object):

    def __init__(self, listener = False, topic = "default"):
        self.connect = False
        self.listener = listener
        self.topic = topic
        self.logger = logging.getLogger(repr(self))

    def __on_connect(self, client, userdata, flags, rc, properties):
        self.logger.info("__on_connect: connected to endpoint %s with result code %s", device["awshost"], rc)
        self.logger.info("__on_connect: userdata: %s, flags: %s, properties: %s", userdata, flags, properties)
        self.logger.debug("+++++{0}".format(rc))
        if rc == "Success":
            self.is_connected = True
            if self.listener:
                self.mqttc.subscribe(self.topic)


    def __on_message(self, client, userdata, msg):
        self.logger.info("__on_message: {0}, {1} - {2}".format(userdata, msg.topic, msg.payload))

    def __on_log(self, client, userdata, level, buf):
        self.logger.debug("__on_log: {0}, {1}, {2}, {3}".format(client, userdata, level, buf))

    def bootstrap_mqtt(self):
        self.mqttc = paho.Client(
            client_id=device["clientId"],
            callback_api_version=paho.CallbackAPIVersion.VERSION2,
            protocol=5
        )
        self.mqttc.on_connect = self.__on_connect
        self.mqttc.on_message = self.__on_message
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

    def start(self):
        self.mqttc.loop_start()
        # self.mqttc.loop_forever()
        while True:
            sleep(2)
            if self.is_connected == True:
                self.logger.debug("Publishing")
                self.mqttc.publish(self.topic, json.dumps({"message": "Hello World"}), qos=1)
            else:
                self.logger.debug("Attempting to connect.")

if __name__ == '__main__':
    
    PubSub(listener = True, topic = "aht20sensor").bootstrap_mqtt().start()