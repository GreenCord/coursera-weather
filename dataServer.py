import datetime, json, sys
from broadcaster import Broadcaster
from sensor import AHT20Sensor
from simple_chalk import chalk
from time import sleep
from utils.custom_logging import Logger

file = open("./data/device.json")
device = json.load(file)
file.close()

class SensorData():

    def __init__(self, interval, *args, **kwargs):
        self.logger = Logger("SensorData")
        self.logger.info(chalk.white("Initializing SensorData using") + chalk.blueBright(f" {interval} second ") + chalk.white("readout interval."))
        
        self.sensor = AHT20Sensor()
        self.clientId = device["clientId"]
        self.broadcaster = Broadcaster(listener=False, topic ="aht20sensor")

        # Init Vars
        self.currentTemperature = 0 # °C by default
        self.currentHumidity = 0    # % relative Humidity
        self.n = int(interval)      # Number of ms between sensor readings

    def startSensing(self):
        self.logger.debug("startSensing called")
        while True:
            self.getReadout()
            sleep(self.n)

    def getReadout(self):
        h,t = self.sensor.getReadout()
        currentTime = datetime.datetime.now()
        readout = {
            "temp": t,
            "rhum": h,
            "timestamp": currentTime.timestamp(),
            "clientId": self.clientId
        }
        self.logger.info(f"New sensor readout • {chalk.blueBright(readout)}")
        
        if self.broadcaster.is_connected == False:
            self.logger.info(chalk.yellowBright("Broadcaster is not connected. ") + chalk.white("Connecting and sending the latest readout."))
            self.broadcaster.broker_connect().send(data=readout)
        else:
            self.logger.info(chalk.blueBright("Broadcaster is currently connected. ") + chalk.white("Sending the latest readout."))
            self.broadcaster.send(data=readout)
        
        return readout
    
# App Setup/Initialization
if sys.argv.__len__() == 1:
    print(chalk.redBright("ERROR: ") + chalk.white("Please provide a number of seconds to use as the sensor reading interval, e.g.: ") + chalk.whiteBright("python dataServer.py 60"))
    exit()
if __name__ == "__main__":
    interval = sys.argv[1]
    app = SensorData(interval)
    app.startSensing()