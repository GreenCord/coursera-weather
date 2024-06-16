isPseudo = False
try:
    # Try loading the AHT20 Sensor resources when one is connected
    import board
    import adafruit_ahtx0
    sensor = adafruit_ahtx0.AHTx0(board.I2C())
except:
    # If initializing the AHT20 sensor fails, fall back to pseudosensor
    import random
    isPseudo = True

class AHT20Sensor:
    # Humidity Range for pseudosensor
    h_range = [0,20,20,40,40,60,60,80,80,90,70,70,50,50,30,30,10,10]
 
    # Celsius Range for pseudosensor
    t_range = [-29,-23,-18,-12,-1,10,21,27,32,26,15,4,-6,-12,-17,-23]
    
    h_range_index = 0
    t_range_index = 0

    humVal = 0
    tempVal = 0
    
    def __init__(self):
        if (isPseudo):
            # Use fake data if no sensor was detected
            self.humVal = self.h_range[ self.h_range_index ]
            self.tempVal = self.t_range[ self.t_range_index ]
        else:
            # Use actual sensor data
            self.humVal = sensor.relative_humidity
            self.tempVal = sensor.temperature

    def getReadout(self):
        if (isPseudo):
            # Use fake data if no sensor was detected
            self.humVal = self.h_range[ self.h_range_index ] + random.uniform(0,10)
            self.tempVal = self.t_range[ self.t_range_index ] + random.uniform(0,10)

            self.h_range_index += 1

            if self.h_range_index > len(self.h_range) - 1:
                self.h_range_index = 0
        
            self.t_range_index += 1

            if self.t_range_index > len(self.t_range) - 1:
                self.t_range_index = 0
        else:
            # Use actual sensor data
            self.humVal = sensor.relative_humidity
            self.tempVal = sensor.temperature

        return self.humVal, self.tempVal
    