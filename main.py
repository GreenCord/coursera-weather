import datetime
import json
import logging
import matplotlib
import numpy as np
import pandas as pd
import platform
from simple_chalk import chalk
import time

from broadcaster import Broadcaster
from utils.custom_logging import Logger
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt5.QtCore import Qt 
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from sensor import AHT20Sensor
from statistics import mean
from utils.worker import Worker
from utils.convert import convertTemperature

file = open("./data/device.json")
device = json.load(file)
file.close()

# Class for displaying the sparkline graphs in PyQt5
class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=4, height=1, dpi=100):
        r = 30 / 255
        g = 27 / 255
        b = 24 / 255

        # Sets up the figure and sets the face color to match GUI background
        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.patch.set_facecolor((r, g, b))
        
        # Sets up the axes & subplots and sets the subplot face color to match the GUI background
        self.axes = fig.add_subplot(111)
        self.axes.patch.set_facecolor((r, g, b))

        # Removes spines and ticks for true sparkline, removes some whitespace
        for k,v in self.axes.spines.items():
            v.set_visible(False)
        self.axes.set_xticks([])
        self.axes.set_yticks([])
        fig.tight_layout()

        super(MplCanvas, self).__init__(fig)

class MainWindow(QMainWindow):
    
    def __init__(self, *args, **kwargs):
        super(MainWindow,self).__init__(*args, **kwargs)
        self.logger = Logger("MainWindow")

        self.system = platform.system()
        self.logger.info(chalk.white("System detected") + self.logger.sep + chalk.green(self.system)) 

        self.ps = AHT20Sensor()
        self.clientId = device["clientId"]
        self.broadcaster = Broadcaster(listener = True, topic="aht20sensor")
        

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
        self.colorTooDry = "#C8963E"
        self.colorTooHumid = "#1789FC"

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
        self.setWindowTitle("My App")
        self.setFixedSize(QSize(1024, 600))
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.Window, self.QCBlack)
        self.setPalette(palette)

        # Init Vars
        self.currentTemperature = 0
        self.currentUnit = "C"
        self.currentHumidity = 0
        self.minTemperature = 16
        self.maxTemperature = 26
        self.minHumidity = 20
        self.maxHumidity = 50
        self.n = 10 # Number of iterations for generating multiple values
        self.nStats = 10 # Number of latest readouts to use for calculating min/max/avg
        self.nGraph = 48 # Number of latest readouts to plot on the graphs
        self.history = []
        self.statMinTemp = None
        self.statMaxTemp = None
        self.statAvgTemp = None
        self.statMinRHum = None
        self.statMaxRHum = None
        self.statAvgRHum = None
        self.statsCalculated = False
        self.sparklinesGraphed = False

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
        self.temperatureLabel = QLabel(f"{self.currentTemperature}")
        self.temperatureLabel.setAlignment(leftVCenter)
        self.temperatureLabel.setFont(numberFont)
        self.temperatureLabel.setStyleSheet(f"color: {self.defaultColor}")

        # Label: Degree Symbol ------------------------------------------------
        self.temperatureDegreeSymbol = QLabel(f"°{self.currentUnit}")
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
        self.layoutContainer.addLayout(self.temperaturePanel, 0, 0)

        """
        Relative Humidity Panel ===============================================
        """
        # Label: Humidity Icon SVG --------------------------------------------
        self.humidityIcon = QLabel(self)
        self.humidityIconPixmap = QPixmap("./svgs/humidity.svg")
        self.humidityIcon.setPixmap(self.humidityIconPixmap.scaled(54, 72, transformMode=Qt.SmoothTransformation))
        self.humidityIcon.setAlignment(rightVCenter)

        # Label: Numeric Humidity ---------------------------------------------
        self.humidityLabel = QLabel(f"{self.currentHumidity}")
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
        self.layoutContainer.addLayout(self.humidityPanel, 1, 0)

        """
        Button Interactions ===================================================
        """
        # Layout: Button Panel (Buttons Added after their definitions) --------
        self.buttonPanel = QVBoxLayout()

        ## Button to Get Current Readouts ---------------------------
        self.btnGetReadout = QPushButton("Get Readout")
        self.btnGetReadout.setFont(buttonFont)
        self.btnGetReadout.clicked.connect(self.getReadout)
        self.buttonPanel.addWidget(self.btnGetReadout)

        ## Button to Get n Readouts ---------------------------------
        self.btnGetNReadouts = QPushButton(f"Get {self.n} Readouts")
        self.btnGetNReadouts.setFont(buttonFont)
        self.btnGetNReadouts.clicked.connect(self.getNReadouts)
        self.buttonPanel.addWidget(self.btnGetNReadouts)

        ## Button to Get the Min/Max/Avg Values ---------------------
        self.btnGetMinMaxAvg = QPushButton(f"Stats for Last {self.nStats} Readouts")
        self.btnGetMinMaxAvg.setFont(buttonFont)
        self.btnGetMinMaxAvg.clicked.connect(self.getMinMaxAvg)
        self.buttonPanel.addWidget(self.btnGetMinMaxAvg)
        
        ## Button to Convert Between °F/°C --------------------------
        self.btnConvertTemperature = QPushButton("Convert to °F")
        self.btnConvertTemperature.setFont(buttonFont)
        self.btnConvertTemperature.clicked.connect(self.convertCurrentTemperature)
        self.buttonPanel.addWidget(self.btnConvertTemperature)

        ## Button to Plot Sparklines for Values ---------------------
        # Note: Button no longer needed, sparkline graphs updated dynamically

        # self.btnGraphData = QPushButton("Update Data Trends")
        # self.btnGraphData.setFont(buttonFont)
        # self.btnGraphData.clicked.connect(self.graphData)
        # self.buttonPanel.addWidget(self.btnGraphData)

        ## Button to exit the program -------------------------------
        self.btnClose = QPushButton("Quit")
        self.btnClose.setFont(buttonFont)
        self.btnClose.clicked.connect(self.shutdown)
        self.buttonPanel.addWidget(self.btnClose)

        # Add the Button Panel to the main layout grid ------------------------
        self.layoutContainer.addLayout(self.buttonPanel, 0, 1, 2, 1)

        """
        App Window Layout =====================================================
        """
        # Set up App window widget
        self.getReadout()
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
        # End __init__ -~=~-~=~-~=~-~=~-~=~-~=~-~=~-~=~-~=~-~=~-~=~-~=~-~=~-~=~
    
    # Method to shut down and close the program
    def shutdown(self):
        if self.broadcaster.is_connected == True:
            self.broadcaster.broker_disconnect()
        self.close()
    
    # Method to remove the stats from the GUI (usually when generating new readouts)
    def clearStatsLabel(self):
        self.temperatureStats.setText(f"")
        self.humidityStats.setText(f"")
        self.statsCalculated = False

    # Method to handle temperature conversions
    def convertCurrentTemperature(self):
        origTemp = self.currentTemperature
        origUnit = self.currentUnit
        
        if self.currentUnit == "F":
            self.currentTemperature = round(convertTemperature(self.currentTemperature, "C"))
            if self.statsCalculated:
                self.statMinTemp = round(convertTemperature(self.statMinTemp,"C"))
                self.statMaxTemp = round(convertTemperature(self.statMaxTemp,"C"))
                self.statAvgTemp = round(convertTemperature(self.statAvgTemp,"C"))
                self.temperatureStats.setText(f"Min: {self.statMinTemp} / Max: {self.statMaxTemp} / Avg: {self.statAvgTemp}")
            self.currentUnit = "C"
            
            self.btnConvertTemperature.setText("Convert to °F")
        else:
            self.currentTemperature = round(convertTemperature(self.currentTemperature, "F"))
            if self.statsCalculated:
                self.statMinTemp = round(convertTemperature(self.statMinTemp,"F"))
                self.statMaxTemp = round(convertTemperature(self.statMaxTemp,"F"))
                self.statAvgTemp = round(convertTemperature(self.statAvgTemp,"F"))
                self.temperatureStats.setText(f"Min: {self.statMinTemp} / Max: {self.statMaxTemp} / Avg: {self.statAvgTemp}")
            self.currentUnit = "F"
            self.btnConvertTemperature.setText("Convert to °C")
        self.temperatureLabel.setText(f"{self.currentTemperature}")
        self.temperatureDegreeSymbol.setText(f"°{self.currentUnit}")
        convertText = chalk.white("Converted ") + chalk.blueBright(origTemp) + chalk.blue("°") + chalk.blueBright(origUnit) + chalk.white(" to ") + chalk.blueBright(self.currentTemperature) + chalk.blue("°") + chalk.blueBright(self.currentUnit)
        if self.statsCalculated:
            convertText += chalk.white(" and converted displayed stats")
        convertText += chalk.white(".")
        self.logger.info(convertText)

    # Method for generating N readouts with 1s delay between
    def generateNReadouts(self, progressCallback):
        # This function is to be called via the Worker thread
        for n in range(0, self.n - 1):
            readout = self.generateReadout()
            self.history.append(readout)
            progressCallback.emit(readout)
            self.logger.debug("Sleep for 1 second.")
            time.sleep(1)
            self.logger.debug("Sleep done.")
        return

    # Method for generating a single readout
    def generateReadout(self):
        h,t = self.ps.generate_values()
        currentTime = datetime.datetime.now()

        readout = {
            "temp":t,
            "rhum":h,
            "timestamp": currentTime.timestamp(),
            "clientId": self.clientId
        }
        self.logger.info(f"New sensor readout • {chalk.blueBright(readout)}")
        
        if self.broadcaster.is_connected == False:
            self.logger.info(chalk.yellowBright("Broadcaster is not connected. ") + chalk.white("Connecting and sending last readout."))
            self.broadcaster.broker_connect().send(data=readout)
        else:
            self.logger.info(chalk.blueBright("Broadcaster is currently connected. ") + chalk.white("Sending last readout."))
            self.broadcaster.send(data=readout)
        
        return readout
    
    # Method for calculating and displaying the stats for N readouts
    def getMinMaxAvg(self):
        '''
        Key Interaction:
        When the related button is pressed, this handles calculating the
        minimum, maximum, and average temperature and relative humidity
        using the readouts stored in self.history. The stats labels are
        updated with the calculated values.
        '''
        temps, rhums, timestamps, clientId = self.mapReadouts(self.nStats).values()

        self.statMinTemp = round(min(temps))
        self.statMaxTemp = round(max(temps))
        self.statAvgTemp = round(mean(temps))
        self.statMinRHum = round(min(rhums))
        self.statMaxRHum = round(max(rhums))
        self.statAvgRHum = round(mean(rhums))
        self.statsCalculated = True
        temperatureStatText = f"Min: {self.statMinTemp} / Max: {self.statMaxTemp} / Avg: {self.statAvgTemp}"
        rHumidityStatText = f"Min: {self.statMinRHum} / Max: {self.statMaxRHum} / Avg: {self.statAvgRHum}"
        self.temperatureStats.setText(temperatureStatText)
        self.humidityStats.setText(rHumidityStatText)
   
    # Method for handling the interaction to generate N readouts using a Worker thread
    def getNReadouts(self):
        '''
        Key Interaction: 
        When the related button is pressed, this handles generating a defined 
        number of readouts asynchronously using a separate thread to prevent 
        locking up the GUI. When the worker is done, the value labels are 
        updated with the values from the last readout recorded.
        '''
        self.clearStatsLabel()

        # Pass the function to execute
        worker = Worker(self.generateNReadouts)
        self.logger.info(f"Worker started. • {worker}")
        worker.signals.progress.connect(self.updateLabels)
        worker.signals.result.connect(self.workerResult)
        worker.signals.finished.connect(self.workerFinished)

        # Execute
        self.threadpool.start(worker)
        
    # Method for handling the interaction to generate 1 readout (synchronous)
    def getReadout(self):
        '''
        Key Interaction:
        When the related button is pressed, this handles generating a single 
        readout synchronously and update the value labels with the values.
        '''
        self.clearStatsLabel()
        readout = self.generateReadout()
        self.history.append(readout)
        self.updateLabels()
    
    # Method for graphing the sparklines to display/update on the GUI
    def graphData(self):
        '''
        Key Interaction:
        When the related button is pressed, this handled generating a sparkline
        graph for the historic values of temperature and relative humidity.
        It updates the stats labels with the result graph.
        '''
        self.logger.debug(f"Plotting graphs using history: {self.history}")
        
        yTValues, yRHValues, xTimestamps, clientId = self.mapReadouts(self.nGraph).values()

        df = pd.DataFrame(xTimestamps, columns = ['timestamp'])
        df['temperature'] = yTValues
        df['humidity'] = yRHValues

        # Store the value limits
        minTempLimit = self.minTemperature
        maxTempLimit = self.maxTemperature
        minHumLimit = self.minHumidity
        maxHumLimit = self.maxHumidity

        # Temperatures from history are in °C; handle conversion if current unit is °F
        if self.currentUnit == "F":
            minTempLimit = convertTemperature(minTempLimit, self.currentUnit)
            maxTempLimit = convertTemperature(maxTempLimit, self.currentUnit)

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
        readoutsToMap = self.history[-n:]
        timestamps = []
        temps = []
        rhums = []
        for count, readout in enumerate(readoutsToMap):
            temp, rhum, timestamp, clientId = readout.values()            
            if self.currentUnit == "F":
                temp = convertTemperature(temp, self.currentUnit)
            
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
    
    # Helper Method to update the labels on the GUI when something changes
    def updateLabels(self):
        self.logger.debug(f"History updated, new length • {len(self.history)}")

        readout = self.history[ len(self.history) - 1 ]
        
        t = readout["temp"]
        h = readout["rhum"]

        # Alarms: Handle if temperature/humidity exceed limits
        ## Temperature ----------------------------------------------
        tempErrorText = ""
        tempErrorColor = ""
        if t > self.maxTemperature:
            tempErrorText = "Too hot!"
            tempErrorColor = f"color: {self.colorTooHot}"
        elif t < self.minTemperature:
            tempErrorText = "Too cold!"
            tempErrorColor = f"color: {self.colorTooCold}"
        else:
            tempErrorText = "Comfortable"
            tempErrorColor = f"color: {self.colorNormal}"
                
        ## Humidity -------------------------------------------------
        rHumErrorText = ""
        rHumErrorColor = ""
        if h > self.maxHumidity:
            rHumErrorText = "Too humid!"
            rHumErrorColor = f"color: {self.colorTooHumid}"
        elif h < self.minHumidity:
            rHumErrorText = "Too dry!"
            rHumErrorColor = f"color: {self.colorTooDry}"
        else:
            rHumErrorText = "Comfortable"
            rHumErrorColor = f"color: {self.colorNormal}"

        if self.currentUnit == "F":
            t = convertTemperature(t, self.currentUnit)

        # Update Labels & Graph
        self.currentTemperature = t
        self.currentHumidity = h
        self.temperatureLabel.setText(f"{round(self.currentTemperature)}")
        self.temperatureError.setText(tempErrorText)
        self.temperatureError.setStyleSheet(tempErrorColor)
        self.humidityLabel.setText(f"{round(self.currentHumidity)}")
        self.humidityError.setText(rHumErrorText)
        self.humidityError.setStyleSheet(rHumErrorColor)
        self.graphData()
    
    # Helper Method called when a worker thread ends.
    def workerFinished(self):
        self.logger.info("Worker finished.")

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

# App Setup/Initialization
if __name__ == "__main__":
    app = QApplication([])
    app.setStyleSheet(style)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    window = MainWindow()
    app.exec_()