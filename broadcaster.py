import json
import paho.mqtt.client as paho

from utils.custom_logging import Logger
from simple_chalk import blue, blueBright, greenBright, magenta, magentaBright, white, whiteBright, yellowBright
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

    def __on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == "Success":
            self.logger.info(f"{magenta('Connected to endpoint')} {blueBright(device['awshost'])} {magenta('with result code')} {blueBright(rc)}")
            self.is_connected = True
            if self.listener == True:
                self.mqttc.subscribe(self.topic)
        else:
            self.logger.warn(f"There was a problem establishing a connection. Result code: {yellowBright(rc)}")

    def __on_connect_fail(self, client, userdata):
        self.logger.debug(f"__on_connect_fail client: {client}")
        self.logger.debug(f"__on_connect_fail userdata: {userdata}")
        self.logger.warn(yellowBright("Connection failed."))

    def __on_disconnect(self, client, userdata, disconnect_flags, rc, properties=None):
        self.logger.debug(f"__on_disconnect client: {client}")
        self.logger.debug(f"__on_disconnect userdata: {userdata}")
        self.logger.debug(f"__on_disconnect disconnect_flags: {disconnect_flags}")
        self.logger.debug(f"__on_disconnect properties: {properties}")
        self.logger.info(f"__on_disconnect rc: {rc}")

    def __on_log(self, client, userdata, level, buf):
        self.logger.debug(f"__on_log client: {client}")
        self.logger.debug(f"__on_log userdata: {userdata}")
        self.logger.debug(f"__on_log level: {level}")
        self.logger.log(self.logger.sep + white(buf))

    def __on_message(self, client, userdata, msg):
        self.logger.debug(f"__on_message client: {client}")
        self.logger.debug(f"__on_message userdata: {userdata}")
        self.logger.info("__on_message (Topic)" + blueBright(self.logger.sep) + whiteBright(msg.topic))
        self.logger.info("__on_message (Payload)" + blueBright(self.logger.sep) + whiteBright(msg.payload))

    def __on_preconnect(self, client, userdata):
        self.logger.debug(f"__on_subscribe client: {client}")
        self.logger.debug(f"__on_subscribe userdata: {userdata}")

    def __on_publish(self, client, userdata, mid, rc, properties=None):
        self.logger.debug(f"__on_publish client: {client}")
        self.logger.debug(f"__on_publish userdata: {userdata}")
        self.logger.debug(f"__on_publish mid: {mid}")
        self.logger.debug(f"__on_publish properties: {properties}")
        self.logger.info(f"__on_publish rc: {rc}")
        self.mqttc.loop_stop()
    
    def __on_subscribe(self, client, userdata, mid, reason_code_list, properties=None):
        self.logger.debug(f"__on_subscribe client: {client}")
        self.logger.debug(f"__on_subscribe userdata: {userdata}")
        self.logger.debug(f"__on_subscribe mid: {mid}")
        self.logger.debug(f"__on_subscribe properties: {properties}")
        self.logger.debug(f"__on_subscribe reason_code_list: {reason_code_list}")

    def __on_unsubscribe(self, client, userdata, mid, reason_code_list, properties=None):
        self.logger.debug(f"__on_unsubscribe client: {client}")
        self.logger.debug(f"__on_unsubscribe userdata: {userdata}")
        self.logger.debug(f"__on_unsubscribe mid: {mid}")
        self.logger.debug(f"__on_unsubscribe properties: {properties}")
        self.logger.debug(f"__on_unsubscribe reason_code_list: {reason_code_list}")

    def broker_connect(self):
        self.logger.info(blue("Initializing paho MQTT Client Broker..."))
        self.mqttc = paho.Client(
            client_id=device["clientId"],
            callback_api_version=paho.CallbackAPIVersion.VERSION2,
            protocol=5
        )
        self.mqttc.on_connect = self.__on_connect
        self.mqttc.on_connect_fail = self.__on_connect_fail
        self.mqttc.on_disconnect = self.__on_disconnect
        self.mqttc.on_message = self.__on_message
        self.mqttc.on_preconnect = self.__on_preconnect
        self.mqttc.on_publish = self.__on_publish
        self.mqttc.on_subscribe = self.__on_subscribe
        self.mqttc.on_unsubscribe = self.__on_unsubscribe
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
        self.logger.info(blue("Paho MQTT Client Broker initialized."))

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
        cnxString = f'{magenta("Waiting for connection")}{whiteBright("...")}'
        while self.is_connected == False:
            self.logger.info(cnxString)
            cnxString += magentaBright(".")
            sleep(0.25)
        
        self.mqttc.publish(self.topic, json.dumps(data), qos=1)
        self.logger.info("MQTT" + whiteBright(self.logger.sep) + blue("Data sent: ") + whiteBright("{0}".format(data)))
        