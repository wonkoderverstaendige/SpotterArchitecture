#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 01 15:53:41 2013
@author: <Ronny Eichler> ronny.eichler@gmail.com

"""
NO_EXIT_CONFIRMATION = True

# buitlin libs
import sys
import os
import platform
import time
import logging

# 3rd party
#import PyQt4 ## forces use of PyQt4 instead of PySide
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import pyqtgraph.ptime as ptime

#Qt user interface files
sys.path.append('./ui')
from mainUi import Ui_MainWindow

# user
sys.path.append('./lib')
from spotter import Spotter

examples = [('media/video/r52r2f107.avi', 200),
            ('media/video/test.avi', 200)]

class Main(QtGui.QMainWindow):
    def __init__(self, *args, **kwargs): #, source, destination, fps, size, gui, serial

        if 'logger' in kwargs:
            self.logger = kwargs['logger']
        if 'app' in kwargs:
            self.app = kwargs['app']

        QtGui.QMainWindow.__init__(self)    
#        mw = QtGui.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.resize(800,800)
        self.show()
        
        self.vb = pg.ViewBox()
        self.ui.graphicsView.setCentralItem(self.vb)
        self.vb.setAspectLocked()
        self.img = pg.ImageItem()
        self.vb.addItem(self.img)
        self.vb.setRange(QtCore.QRectF(0, 0, 512, 512))
#        self.img.setPxMode(True)
        
        self.logger.info('%s starting spotter', self)
        self.spotter = Spotter(*args, **kwargs)    
        self.spotter.gui_grabber.displayTarget = self.img
        self.logger.info('%s spotter instantiated', self)

        self.lastTime = ptime.time()
        self.fps = None

        # main window refresh timer
#        self.timer = QtCore.QTimer()
#        self.timer.timeout.connect(self.update)
#        self.timer.start(0)
        self.update()

    def update(self):
        self.logger.info('%s:Processing Events', self)
        now = ptime.time()
        dt = now - self.lastTime
        self.lastTime = now
        if self.fps is None:
            self.fps = 1.0/dt
        else:
            s = np.clip(dt*3., 0, 1)
            self.fps = self.fps * (1-s) + (1.0/dt) * s
        self.ui.fpsLabel.setText('%0.2f fps' % self.fps)
#        self.app.processEvents()  ## force complete redraw for every plot
        QtCore.QTimer.singleShot(1, self.update)
#        global ui, lastTime, fps, img
#        rv, frame = src.read()
#        # rotate frame if wanted
#        frame = np.rot90(frame, 3)
#        # flip frame
#        #frame = np.fliplr(frame)    


    def closeEvent(self, event):
        """
        Exiting the interface has to kill the spotter class and subclasses
        properly, especially the writer and serial handles, otherwise division
        by zero might be imminent.
        """
        if NO_EXIT_CONFIRMATION:
            reply = QtGui.QMessageBox.Yes
        else:
            reply = QtGui.QMessageBox.question(self,
                                               'Exiting...',
                                               'Are you sure?',
                                               QtGui.QMessageBox.Yes,
                                               QtGui.QMessageBox.No )
        if reply == QtGui.QMessageBox.Yes:
            self.spotter.stop_all()
#            time.sleep(1)
            event.accept()
        else:
            event.ignore()

#def main(*args, **kwargs): #source, destination, fps, size, gui, serial
#        window = Main(*args, **kwargs)
#        window.show()
#        window.raise_() # needed on OSX?

###############################################################################
#        MAIN LOOP
###############################################################################
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

#    app = QtGui.QApplication([])
#    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
#        QtGui.QApplication.instance().exec_()
    QtGui.QApplication.setGraphicsSystem('raster')
    app = QtGui.QApplication([])
    main = Main(logger=logger, app=app)
    rv = app.exec_()
    logger.info('Application return value: %d. Done.', rv)
    sys.exit(rv)