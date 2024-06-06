from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import time
import traceback, sys

# Adapted from https://www.pythonguis.com/tutorials/multithreading-pyqt-applications-qthreadpool/
class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    """
    print("WorkerSignals instantiated.")
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

class Worker (QRunnable):
    """
    Worker Thread

    Inherits from QRunnable to handler worker thread setup, signals, and 
    wrap-up.

    :param callback: The function callback to run on this worker thread. 
                     Supplied args and kwargs will be passed through to the
                     runner.
    :type callback:  function
    :param args:     Arguments to pass to the callback function
    :param kwargs:   Keywords to pass to the callback function
    """

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        print("--- Worker initializing")
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progressCallback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        """
        Initialise the runner funtion with passed args, kwargs.
        """

        print("--- Worker.run started")
        # Retrieve args/kwargs here; and fire processing using them
        try:
            print(f"Worker trying to call {self.fn}")
            result = self.fn(*self.args,**self.kwargs)
        except:
            print("Worker exception encountered")
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            print(f"Worker emitting result :: {result}")
            self.signals.result.emit(result) # Return the result of the processing
        finally:
            print(f"Worker done, emitting finished signal")
            self.signals.finished.emit() # Done
