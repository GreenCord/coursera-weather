
import json

from sqsHandler import SQSHandler
from simple_chalk import chalk
from utils.custom_logging import Logger

class SensorDisplay():

    def __init__(self, *args, **kwargs):
        self.logger = Logger("SensorDisplay")
        self.sqs = SQSHandler()
      
        # Init Vars
        self.hello = "Hello"

    def startPolling(self, *args, **kwargs):
        self.logger.info("Polling for SQS Messages")
        readout = self.sqs.getMessage()
        if readout != None:
            self.handleMessage(readout)

    def handleMessage(self, readout):
        self.logger.debug('Received readout :: %s' % readout)
        
        # readout = readout.decode()
        data = json.loads(readout.decode())
        self.logger.info(data['temp'])
        self.logger.info(data['rhum'])
        self.logger.info(data['ts'])
        self.logger.info(data['clid'])

if __name__ == "__main__":
    app = SensorDisplay()
    app.startPolling()