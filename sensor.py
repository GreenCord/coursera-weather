import board
import adafruit_ahtx0

class AHT20Sensor:
    sensor = adafruit_ahtx0.AHTx0(board.I2C())

    humVal = -9999
    tempVal = -9999

    def __init__(self):
        self.humVal = self.sensor.relative_humidity
        self.tempVal = self.sensor.temperature

    def generate_values(self):
        self.humVal = self.sensor.relative_humidity
        self.tempVal = self.sensor.temperature

        return self.humVal, self.tempVal