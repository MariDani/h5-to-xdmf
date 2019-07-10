import os, re, h5py
import ipywidgets as widgets
from hdfviewer.widgets.HDFViewer import HDFViewerWidget
from hdfviewer.widgets.PathSelector import PathSelector
import matplotlib.pyplot as plt
import ipympl
from IPython.display import display


# define global variables
h5PreviewSelectedFile: PathSelector

def getFile(inputDir):
    global h5PreviewSelectedFile
    h5PreviewSelectedFile = PathSelector(startingPath=inputDir,extensions=[".hdf",".h5"])
    pathWidget = h5PreviewSelectedFile.widget    
    display(pathWidget)

def showFile():
    global h5PreviewSelectedFile
    if h5PreviewSelectedFile.path:
        widget = HDFViewerWidget(h5PreviewSelectedFile.path)
        display(widget)
    else:
        print("Error: .h5 file not selected")