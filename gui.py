import ast, datetime, json
import numpy as np
import pandas as pd
import platform

from mplCanvas import MplCanvas
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from sensor import AHT20Sensor
from simple_chalk import chalk
from sqsHandler import SQSHandler
from statistics import mean
from utils.convert import convertTemperature
from utils.custom_logging import Logger
from utils.worker import Worker

file = open("./data/device.json")
device = json.load(file)
file.close()

class SensorDisplay(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(SensorDisplay,self).__init__(*args, **kwargs)
        self.logger = Logger("SensorDisplay")
        self.sqs = SQSHandler()

        self.system = platform.system()
        self.logger.info(chalk.white("System detected") + self.logger.sep + chalk.green(self.system)) 
      
        # Init Vars
        self.clientId = device['clientId']
        self.data = {
            "temp": -9999,
            "rhum": -9999,
            "unit": "C",
            "history": [],
            "lastUpdated": datetime.datetime.now()
        }

        self.limits = {
            "temp": {
                "min": 10,
                "max": 32
            },
            "rhum": {
                "min": 20,
                "max": 50
            },
            "n": {
                "graph": 48, # Number of readouts for plotting on graphs
                "stats": 10 # Number of readouts for calculating min/max/avg
            }
        }

        self.stats = {
            "temp": {
                "min": None,
                "max": None,
                "avg": None
            },
            "rhum": {
                "min": None,
                "max": None,
                "avg": None
            },
            "areCalculated": False
        }
        
        # Define Fonts
        QFontDatabase.addApplicationFont("fonts/ttfs/Jura-Regular.ttf")
        buttonFont = QFont("Jura", 48)
        errorFont = QFont("Jura", 24)
        numberFont = QFont("Jura", 144)
        statsFont = QFont("Jura", 32)
        symbolFont = QFont("Jura", 72)
        self.graphLabelFont = QFont("Jura",14)
        
        # Colors & Styles
        self.defaultColor = "#C4CAD0"
        self.statsColor = "#006C67"
        self.colorNormal = "#006C67"
        self.colorTooHot = "#DB4437"
        self.colorTooCold = "#1789FC"
        self.colorTooHumid = "#DB4437"
        self.colorTooDry = "#1789FC"

        self.cBlack = "rgb(30, 27, 24)"
        self.QCBlack = QColor(30,27,24)
        
        # Layout Constants
        self.stretchValue = 1
        
        # Common Alignments
        rightVCenter = Qt.AlignRight | Qt.AlignVCenter
        leftVCenter = Qt.AlignLeft | Qt.AlignVCenter
        bottomHCenter = Qt.AlignHCenter | Qt.AlignBottom
        topHCenter = Qt.AlignHCenter | Qt.AlignTop

        # Init App Window
        self.setWindowTitle("Ambient Humidity + Temperature")
        self.setFixedSize(QSize(1024, 600))
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.Window, self.QCBlack)
        self.setPalette(palette)

        # Layout Main Container
        self.layoutContainer = QGridLayout()

        """
        Temperature Panel =====================================================
        """
        # Label: Temperature Icon SVG -----------------------------------------
        self.temperatureIcon = QLabel(self)
        self.temperatureIconPixmap = QPixmap("./svgs/thermometer-half.svg")
        self.temperatureIcon.setPixmap(self.temperatureIconPixmap.scaled(36, 72, transformMode=Qt.SmoothTransformation))
        self.temperatureIcon.setAlignment(rightVCenter)
        self.temperatureIcon.setStyleSheet(f"color: {self.defaultColor}")
        
        # Label: Numeric Temperature ------------------------------------------
        self.temperatureLabel = QLabel(f"{self.data['temp']}")
        self.temperatureLabel.setAlignment(leftVCenter)
        self.temperatureLabel.setFont(numberFont)
        self.temperatureLabel.setStyleSheet(f"color: {self.defaultColor}")

        # Label: Degree Symbol ------------------------------------------------
        self.temperatureDegreeSymbol = QLabel(f"°{self.data['unit']}")
        self.temperatureDegreeSymbol.setAlignment(leftVCenter)
        self.temperatureDegreeSymbol.setFont(numberFont)
        self.temperatureDegreeSymbol.setStyleSheet(f"color: {self.defaultColor}")

        # Layout - Temperature Label: Numeric Temperature + Degree Symbol -----
        self.temperatureLabelContainer = QHBoxLayout()
        self.temperatureLabelContainer.addWidget(self.temperatureLabel)
        self.temperatureLabelContainer.addWidget(self.temperatureDegreeSymbol)
        
        # Layout - Temperature Container: Icon + Temperature Label ------------
        self.temperatureContainer = QHBoxLayout()
        self.temperatureContainer.addStretch()
        self.temperatureContainer.addWidget(self.temperatureIcon)
        self.temperatureContainer.addLayout(self.temperatureLabelContainer)
        self.temperatureContainer.setAlignment(Qt.AlignCenter)
        self.temperatureContainer.addStretch()

        # Label: Stats field --------------------------------------------------
        self.temperatureStats = QLabel("")
        self.temperatureStats.setObjectName("temperatureStats")
        self.temperatureStats.setFont(statsFont)
        self.temperatureStats.setAlignment(bottomHCenter)

        # Label: Error field --------------------------------------------------
        self.temperatureError = QLabel("I'm an error label")
        self.temperatureError.setObjectName("temperatureError")
        self.temperatureError.setFont(errorFont)
        self.temperatureError.setAlignment(topHCenter)

        # Layout - Temperature Panel: Temperature Container + Error -----------
        self.temperaturePanel = QVBoxLayout()
        self.temperaturePanel.addStretch()
        self.temperaturePanel.addWidget(self.temperatureStats)
        self.temperaturePanel.addLayout(self.temperatureContainer)
        self.temperaturePanel.addWidget(self.temperatureError)
        self.temperaturePanel.addStretch()

        # Add the Temperature Panel to the main layout grid -------------------
        self.layoutContainer.addLayout(self.temperaturePanel, 1, 0)

        """
        Relative Humidity Panel ===============================================
        """
        # Label: Humidity Icon SVG --------------------------------------------
        self.humidityIcon = QLabel(self)
        self.humidityIconPixmap = QPixmap("./svgs/humidity.svg")
        self.humidityIcon.setPixmap(self.humidityIconPixmap.scaled(54, 72, transformMode=Qt.SmoothTransformation))
        self.humidityIcon.setAlignment(rightVCenter)

        # Label: Numeric Humidity ---------------------------------------------
        self.humidityLabel = QLabel(f"{self.data['rhum']}")
        self.humidityLabel.setAlignment(rightVCenter)
        self.humidityLabel.setFont(numberFont)

        # Label: % Symbol -----------------------------------------------------
        self.humidityPercentSymbol = QLabel("%")
        self.humidityPercentSymbol.setAlignment(leftVCenter)
        self.humidityPercentSymbol.setFont(symbolFont)

        # Layout - Humidity Label: Icon + Numeric Humidity + % Symbol ---------
        self.humidityLabelContainer = QHBoxLayout()
        self.humidityLabelContainer.addWidget(self.humidityLabel)
        self.humidityLabelContainer.addWidget(self.humidityPercentSymbol)
        self.humidityLabelContainer.setAlignment(leftVCenter)

        # Layout - Humidity Container:  Icon + Humidity Label -----------------
        self.humidityContainer = QHBoxLayout()
        self.humidityContainer.addStretch()
        self.humidityContainer.addWidget(self.humidityIcon)
        self.humidityContainer.addLayout(self.humidityLabelContainer)
        self.humidityContainer.setAlignment(Qt.AlignCenter)
        self.humidityContainer.addStretch()

        # Label: Stats field --------------------------------------------------
        self.humidityStats = QLabel("")
        self.humidityStats.setObjectName("humidityStats")
        self.humidityStats.setFont(statsFont)
        self.humidityStats.setAlignment(bottomHCenter)

        # Label: Humidity Error -----------------------------------------------
        self.humidityError = QLabel("I'm also an error label")
        self.humidityError.setObjectName("humidityError")
        self.humidityError.setFont(errorFont)
        self.humidityError.setAlignment(topHCenter)

        # Layout: Humidity Panel ----------------------------------------------
        self.humidityPanel = QVBoxLayout()
        self.humidityPanel.addStretch()
        self.humidityPanel.addWidget(self.humidityStats)
        self.humidityPanel.addLayout(self.humidityContainer)
        self.humidityPanel.addWidget(self.humidityError)
        self.humidityPanel.addStretch()
        
        # Add the Humidity Panel to the main layout grid  ---------------------
        self.layoutContainer.addLayout(self.humidityPanel, 1, 1)

        """
        Button Interactions ===================================================
        """
        # Layout: Button Panel (Buttons Added after their definitions) --------
        self.buttonPanel = QHBoxLayout()
        
        # Button to Convert Between °F/°C --------------------------
        self.btnConvertTemperature = QPushButton("Convert to °F")
        self.btnConvertTemperature.setFont(buttonFont)
        self.btnConvertTemperature.clicked.connect(self.convertCurrentTemperature)
        self.buttonPanel.addWidget(self.btnConvertTemperature)

        ## Button to exit the program -------------------------------
        self.btnClose = QPushButton("Quit")
        self.btnClose.setFont(buttonFont)
        self.btnClose.clicked.connect(self.shutdown)
        self.buttonPanel.addWidget(self.btnClose)

        # Add the Button Panel to the main layout grid ------------------------
        self.layoutContainer.addLayout(self.buttonPanel, 0, 0, 1, 2)

        """
        App Window Layout =====================================================
        """
        # Set up App window widget
        self.temperatureLabel.setText("-")
        self.temperatureError.setText("")
        self.humidityLabel.setText("-")
        self.humidityError.setText("")

        widget = QWidget()
        widget.setLayout(self.layoutContainer)
        self.setCentralWidget(widget)
        self.show()
        self.threadpool = QThreadPool()
        self.logger.info(chalk.white("Multithreading with maximum ") + chalk.blue(self.threadpool.maxThreadCount()) + chalk.white(" threads."))
        if self.system == "Darwin":
            self.show()
        else:
            self.showFullScreen()
        self.start()
        # End __init__ -~=~-~=~-~=~-~=~-~=~-~=~-~=~-~=~-~=~-~=~-~=~-~=~-~=~-~=~

    def start(self):
        # Pass the function to execute
        try: 
            worker = Worker(self.startPolling)
            self.logger.info(f"Worker started. • {worker}")
            worker.signals.progress.connect(self.updateLabels)
            worker.signals.result.connect(self.workerResult)
            worker.signals.finished.connect(self.workerFinished)

            # Execute
            self.threadpool.start(worker)
        except (KeyboardInterrupt, EOFError):
            self.shutdown()

    def startPolling(self, progressCallback):
        self.logger.info("Polling for SQS Messages")
        try:
            readout = self.sqs.getMessage()
            if readout != None:
                self.logger.debug('Received readout :: %s' % readout)
                readout = readout.decode()
                self.data['history'].append(readout)
                progressCallback.emit(readout)
        except (KeyboardInterrupt, EOFError):
            self.shutdown()

    # Method to handle temperature conversions
    def convertCurrentTemperature(self):
        if self.data['temp'] <= -9999:
            return
        origTemp = self.data['temp']
        origUnit = self.data['unit']
        
        if self.data['unit'] == "F":
            self.data['temp'] = round(convertTemperature(self.data['temp'], "C"))
            if self.stats['areCalculated']:
                self.stats['temp']['min'] = round(convertTemperature(self.stats['temp']['min'],"C"))
                self.stats['temp']['max'] = round(convertTemperature(self.stats['temp']['max'],"C"))
                self.stats['temp']['avg'] = round(convertTemperature(self.stats['temp']['avg'],"C"))
                self.temperatureStats.setText(f"Min: {self.stats['temp']['min']} / Max: {self.stats['temp']['max']} / Avg: {self.stats['temp']['avg']}")
            self.data['unit'] = "C"
            
            self.btnConvertTemperature.setText("Convert to °F")
        else:
            self.data['temp'] = round(convertTemperature(self.data['temp'], "F"))
            if self.stats['areCalculated']:
                self.stats['temp']['min'] = round(convertTemperature(self.stats['temp']['min'],"F"))
                self.stats['temp']['max'] = round(convertTemperature(self.stats['temp']['max'],"F"))
                self.stats['temp']['avg'] = round(convertTemperature(self.stats['temp']['avg'],"F"))
                self.temperatureStats.setText(f"Min: {self.stats['temp']['min']} / Max: {self.stats['temp']['max']} / Avg: {self.stats['temp']['avg']}")
            self.data['unit'] = "F"
            self.btnConvertTemperature.setText("Convert to °C")
        self.temperatureLabel.setText(f"{self.data['temp']}")
        self.temperatureDegreeSymbol.setText(f"°{self.data['unit']}")
        convertText = chalk.white("Converted ") + chalk.blueBright(origTemp) + chalk.blue("°") + chalk.blueBright(origUnit) + chalk.white(" to ") + chalk.blueBright(self.data['temp']) + chalk.blue("°") + chalk.blueBright(self.data['unit'])
        if self.stats['areCalculated']:
            convertText += chalk.white(" and converted displayed stats")
        convertText += chalk.white(".")
        self.logger.info(convertText)
    
    # Method to shut down and close the program
    def shutdown(self):
        self.close()
    
    # Method for calculating and displaying the stats for N readouts
    def getMinMaxAvg(self):
        '''
        Key Interaction:
        When the related button is pressed, this handles calculating the
        minimum, maximum, and average temperature and relative humidity
        using the readouts stored in self.history. The stats labels are
        updated with the calculated values.
        '''
        temps, rhums, timestamps, clientId = self.mapReadouts(self.limits['n']['stats']).values()

        self.stats['temp']['min'] = round(min(temps))
        self.stats['temp']['max'] = round(max(temps))
        self.stats['temp']['avg'] = round(mean(temps))
        self.stats['rhum']['min'] = round(min(rhums))
        self.stats['rhum']['max'] = round(max(rhums))
        self.stats['rhum']['avg'] = round(mean(rhums))
        self.stats['areCalculated'] = True
        temperatureStatText = f"Min: {self.stats['temp']['min']} / Max: {self.stats['temp']['max']} / Avg: {self.stats['temp']['avg']}"
        rHumidityStatText = f"Min: {self.stats['rhum']['min']} / Max: {self.stats['rhum']['max']} / Avg: {self.stats['rhum']['avg']}"
        self.temperatureStats.setText(temperatureStatText)
        self.humidityStats.setText(rHumidityStatText)

    # Method for graphing the sparklines to display/update on the GUI
    def graphData(self):
        '''
        Key Interaction:
        When the related button is pressed, this handled generating a sparkline
        graph for the historic values of temperature and relative humidity.
        It updates the stats labels with the result graph.
        '''
        self.logger.debug(f"Plotting graphs using history: {self.data['history']}")
        
        yTValues, yRHValues, xTimestamps, clientId = self.mapReadouts(self.limits['n']['graph']).values()

        df = pd.DataFrame(xTimestamps, columns = ['timestamp'])
        df['temperature'] = yTValues
        df['humidity'] = yRHValues

        # Store the value limits
        minTempLimit = self.limits['temp']['min']
        maxTempLimit = self.limits['temp']['max']
        minHumLimit = self.limits['rhum']['min']
        maxHumLimit = self.limits['rhum']['max']
        
        # Get the current ° unit
        unit = self.data['unit']

        # Temperatures from history are in °C; handle conversion if current unit is °F
        if unit == "F":
            minTempLimit = convertTemperature(minTempLimit, unit)
            maxTempLimit = convertTemperature(maxTempLimit, unit)

        # Line Colors
        itsCold = self.colorTooCold
        itsHot = self.colorTooHot
        itsNormal = self.colorNormal
        itsDry = self.colorTooDry
        itsHumid = self.colorTooHumid

        # Mask the Temperature Data and create the sparkline using line colors
        tUpper = np.ma.masked_where(df['temperature'] < maxTempLimit, df['temperature'])
        tLower = np.ma.masked_where(df['temperature'] > minTempLimit, df['temperature'])
        sparklineT = MplCanvas(self, width=4, height=1, dpi=100)
        sparklineT.axes.plot(df['timestamp'], df['temperature'], color=itsNormal)
        sparklineT.axes.plot(df['timestamp'], tLower, color=itsCold)
        sparklineT.axes.plot(df['timestamp'], tUpper, color=itsHot)

        # Mask the Humidity Data and create the sparkline using line colors
        hUpper = np.ma.masked_where(df['humidity'] < maxHumLimit, df['humidity'])
        hLower = np.ma.masked_where(df['humidity'] > minHumLimit, df['humidity'])
        sparklineH = MplCanvas(self, width=4, height=1, dpi=100)
        sparklineH.axes.plot(df['timestamp'], df['humidity'], color=itsNormal)
        sparklineH.axes.plot(df['timestamp'], hLower, color=itsDry)
        sparklineH.axes.plot(df['timestamp'], hUpper, color=itsHumid)

        # Create the sparkline graph layout and add/overwrite position on main layout
        self.sparklinesPanel = QHBoxLayout()
        self.sparklineTemperature = sparklineT
        self.sparklineTemperatureLabel = QLabel("Temperature:")
        self.sparklineTemperatureLabel.setFont(self.graphLabelFont)
        self.sparklineTemperatureLabel.setAlignment( Qt.AlignRight | Qt.AlignVCenter)
        self.sparklineHumidity = sparklineH
        self.sparklineHumidityLabel = QLabel("Humidity:")
        self.sparklineHumidityLabel.setFont(self.graphLabelFont)
        self.sparklineHumidityLabel.setAlignment( Qt.AlignRight | Qt.AlignVCenter)
        self.sparklinesPanel.addStretch()
        self.sparklinesPanel.addWidget(self.sparklineTemperatureLabel)
        self.sparklinesPanel.addWidget(self.sparklineTemperature)
        self.sparklinesPanel.addWidget(self.sparklineHumidityLabel)
        self.sparklinesPanel.addWidget(self.sparklineHumidity)
        self.sparklinesPanel.addStretch()
        self.layoutContainer.addLayout(self.sparklinesPanel, 2, 0, 1, 2)

    # Helper Method to map readouts into a Dict for each type of readout value, for graphing
    def mapReadouts(self, n: int):
        '''
        Returns a dict of n temps, rhums, timestamps. temps will be returned
        using the current temperatureUnit.
        '''
        readoutsToMap = self.data['history'][-n:]
        timestamps = []
        temps = []
        rhums = []
        for count, readout in enumerate(readoutsToMap):
            self.logger.debug(f'mapReadouts using readout: {ast.literal_eval(readout)}')

            temp, rhum, timestamp, clientId = ast.literal_eval(readout).values()            
            if self.data['unit'] == "F":
                temp = convertTemperature(temp, self.data['unit'])
            
            temps.append(temp)
            rhums.append(rhum)
            timestamps.append(timestamp)
        mappedValues = {
            "temps": temps,
            "rhums": rhums,
            "timestamps": timestamps,
            "clientId": clientId
        }
        return mappedValues
    
    # Method to update the labels on the screen.
    def updateLabels(self):
        self.logger.debug("updateLabels called.")
        readout = json.loads(self.data['history'][ len(self.data['history']) - 1 ])
        self.logger.info(f"updateLabels working with latest readout: {readout}")
        
        t = readout['temp']
        h = readout['rhum']

        # Alarms: Handle if temperature/humidity exceed limits
        ## Temperature ----------------------------------------------
        tempErrorText = ""
        tempErrorColor = ""
        if t > self.limits["temp"]["max"]:
            tempErrorText = "Too hot!"
            tempErrorColor = f"color: {self.colorTooHot}"
        elif t < self.limits["temp"]["min"]:
            tempErrorText = "Too cold!"
            tempErrorColor = f"color: {self.colorTooCold}"
        else:
            tempErrorText = "Normal"
            tempErrorColor = f"color: {self.colorNormal}"
                
        ## Humidity -------------------------------------------------
        rHumErrorText = ""
        rHumErrorColor = ""
        if h > self.limits["rhum"]["max"]:
            rHumErrorText = "Too humid!"
            rHumErrorColor = f"color: {self.colorTooHumid}"
        elif h < self.limits["rhum"]["min"]:
            rHumErrorText = "Too dry!"
            rHumErrorColor = f"color: {self.colorTooDry}"
        else:
            rHumErrorText = "Normal"
            rHumErrorColor = f"color: {self.colorNormal}"

        if self.data['unit'] == "F":
            t = convertTemperature(t, self.data['unit'])

        # Update Labels & Graph
        self.data["temp"] = t
        self.data["rhum"] = h
        self.temperatureLabel.setText(f"{round(self.data['temp'])}")
        self.temperatureError.setText(tempErrorText)
        self.temperatureError.setStyleSheet(tempErrorColor)
        self.humidityLabel.setText(f"{round(self.data['rhum'])}")
        self.humidityError.setText(rHumErrorText)
        self.humidityError.setStyleSheet(rHumErrorColor)
        self.getMinMaxAvg()
        self.graphData()
        self.logger.debug("updateLabels finished.")

    # Helper Method called when a worker thread ends.
    def workerFinished(self):
        self.logger.info("Worker finished.")
        self.start()

    # Helper Method to log the result of the thread.
    def workerResult(self,it):
        self.logger.info(f"Worker Result: {it}")

# General StyleSheet
style = """
    QLabel {
        color: rgb(196,202,208);
        line-height: 1
    }
    QLabel#temperatureStats,
    QLabel#humidityStats {
        color: rgb(0, 108, 103)
    }
    QPixmap {
        color: rgb(23,137,252);   
    }
    QPushButton{
        background: rgb(23,137,252);
        border: 2px solid rgb(23,137,252);
        border-radius: 16px;
        color: rgb(30,27,24);
        font-size: 24pt; 
        font-weight: 500;
        height: 48px;
        min-width: 300px;
    }
    QPushButton:hover{
        background: rgb(30,27,24);
        color: rgb(23,137,252);
    }
"""

if __name__ == "__main__":
    app = QApplication([])
    app.setStyleSheet(style)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    window = SensorDisplay()
    app.exec_()