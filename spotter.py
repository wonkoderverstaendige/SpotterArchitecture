# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 23:48:24 2013

@author: Ronny
"""
# buitlin libs
import sys
import os
import platform
import time
import logging
import threading

sys.path.append('./lib')
from Producer import Producer
from Consumer import Consumer

import cv2

class Spotter:
    active = True
    
    def __init__(self, *args, **kwargs):
        if 'logger' in kwargs:
            self.logger = kwargs['logger']
        else:
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(__name__)

        # list of general consumer queues
        self.consumer_qlist = []
        # list of general producer queues
        self.producer_qlist = []
        # list of consumer queues for rendering
        self.gui_qlist = []

#        fname, num_frames = examples[1]
        fname = './media/video/test.avi'

        self.logger.info('Instantiating thread classes')
        self.threads = []
        self.source_grabber = SourceGrabber(self.consumer_qlist,
                                            self.producer_qlist,
                                            interval=0.001,
                                            mode='buffered',
                                            fname=fname)
        self.threads.append(self.source_grabber)

        self.gui_grabber = GUIGrabber(self.gui_qlist,
                                      self.producer_qlist,
                                      interval=0.03,
                                      timed='timed',
                                      resource=self.consumer_qlist,
                                      bufsize=1)
        self.threads.append(self.gui_grabber)
        
#        self.d = Display(self.gui_qlist)
#        self.threads.append(self.d)
        
        self.tracker = Tracker(self.consumer_qlist)
        self.threads.append(self.tracker)

        self.logger.info('Starting up threads')
        self.start_all()
        
    def start_all(self):
        for t in self.threads:
            t.start()
        
    def stop_all(self):
        self.logger.info(threading.enumerate())        
        for t in self.threads:
            if t.is_alive():
                t.stop()
                time.sleep(0.05)
        self.logger.info(threading.enumerate())
            
#    tstart = time.clock()
#
#    tprev = time.clock()
#    cprev = 0
#    itv = 0

#    while cv2.waitKey(15) < 0 and d.is_alive():
#        if t.count-cprev >= 100:
#            tel = time.clock()-tprev
#            f = t.count-cprev
#            logger.info('fps %.1f', f*1.0/tel)
#            tprev = time.clock()
#            cprev = t.count

        #pass
#    while g.is_alive():
#        time.sleep(0.1)
#        while self.active:
#            time.sleep(0.1)
#
##        self.logger.info('Frames in source: %d', num_frames)
##        self.logger.info('FPS: %d', t.count/(time.clock()-tstart))
#    
#        self.logger.info('Stopping all remaining threads...')
#
#        try:
#            if self.source_grabber.is_alive():
#                self.source_grabber.stop()
#            if self.tracker.is_alive():
#                self.tracker.stop()
#            if self.d.is_alive():
#                self.d.stop()
#            if self.gui_grabber.is_alive():
#                self.gui_grabber.stop()
#            cv2.destroyAllWindows()
#        except:
#            pass
#    
#        self.logger.info('Done.')

    #print threading.enumerate()

class SourceGrabber(Producer):
    """
    Main producer. Grabs frame from resource and adds result to queue of
    consumers.
    """
    def __init__(self, *args, **kwargs):
        Producer.__init__(self, *args, **kwargs)
        if 'fname' in kwargs:
            fname = kwargs['fname']

        self.log.info('Opening frame source %s', fname)
        self.resource = cv2.VideoCapture(fname)

#        self.timer.change_interval(0.001)

    def produce(self):
        if self.resource is not None:
            try:
                rv, frame = self.resource.read()
            except:
                self.log.error('Frame acquisition failed!')
            if rv:
                self.count += 1
                self.log.debug('produced frame: %d', self.count)
                return frame
            else:
                self.log.debug('%s no frame returned!: %d', self,  self.count)
                self.stop()


class GUIGrabber(Producer):
    """
    Hybrid consumer/producer. Attaches itself to the frame producer (Grabber)
    at a selected frame rate and only produces frames for its consumers at the
    specified rate. This allows to decouple frame acquisition and processing
    from rendering.
    """
    displayTarget = None
    def __init__(self, *args, **kwargs):
        Producer.__init__(self, *args, **kwargs)
        self.origin = self.resource
        self.resource = self.q.Queue(maxsize=1)

    def produce(self):
        self.count+=1
        self.log.debug("%s:Q:%1d; producing: %d", self, self.input.qsize(), self.count)

        while not self.resource.empty():
            self.log.debug("Q:%2d; pre-emptying queue", self.resource.qsize())
            self.resource.get_nowait()

        self.origin.append(self.resource)
        self.log.debug("Q:%3d; receiving item: %d", self.input.qsize(), self.count)
        try:
            frame = self.resource.get(timeout=0.5)
        except self.q.Empty:
            frame = None
        
        if frame is not None and self.displayTarget is not None:
            self.displayTarget.setImage(frame)
            
        self.origin.remove(self.resource)

        self.log.debug("Q:%3d; returning frame for display: %d", self.input.qsize(), self.count)
        
        return frame


class Tracker(Consumer):
    displayTarget = None
    def __init__(self, *args, **kwargs):
        Consumer.__init__(self, *args, **kwargs)

    def process(self, data):
        if data is None:
            return
        try:
            self.log.debug("Q:%3d; tracking frame: %d", self.input.qsize(), self.count)
            self.hsv = cv2.cvtColor(data,cv2.COLOR_BGR2HSV)
            if self.displayTarget is not None:
                self.displayTarget.setImage(self.hsv)
            self.count += 1

        except:
            self.log.error('Tracking frame failed on:')
            print data


class Display(Consumer):
    displayTarget = None
    def __init__(self, *args, **kwargs):
        Consumer.__init__(self, *args, **kwargs)

    def process(self, data):
        if data is None:
            return
        try:
            self.log.debug("Q:%3d; displaying frame: %d", self.input.qsize(), self.count)
            #self.log.info(data)
            try:
                if self.displayTarget is not None:
                    self.displayTarget.setImage(data)
                self.count += 1
            except:
                self.log.error('Displaying frame failed!')
        except:
            self.log.error('Displaying frame failed!')


#class Writer(Consumer):
#    def __init__(self, *args, **kwargs):
#        Consumer.__init__(self, *args, **kwargs)
#        self.video_writer = cv2.VideoWriter('test.avi', -1, 30, ())
#
#    def process(self, data):
#        try:
#            self.video_writer.write(data)
#        except:
#            print "Writing frame failed!"