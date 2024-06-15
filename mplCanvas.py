# Class for displaying the sparkline graphs in PyQt5
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

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