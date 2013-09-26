#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 01 15:53:41 2013
@author: <Ronny Eichler> ronny.eichler@gmail.com

"""
# sys libs

import time
import logging

# 3rd party
import cv2
#import glumpy as gp


# user
from Producer import Producer
from Consumer import Consumer

examples = [('../ladies.mp4', 7338),
            ('../example.wmv', 1996)]

class Grabber(Producer):
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
                self.stop()


class GUIFrameGrabber(Producer):
    """
    Hybrid consumer/producer. Attaches itself to the frame producer (Grabber)
    at a selected frame rate and only produces frames for its consumers at the
    specified rate. This allows to decouple frame acquisition and processing
    from rendering.
    """
    def __init__(self, *args, **kwargs):
        Producer.__init__(self, *args, **kwargs)
        self.origin = self.resource
        self.resource = self.q.Queue(maxsize=16)

    def produce(self):
        self.count+=1
        self.log.debug("Q:%3d; producing: %d", self.input.qsize(), self.count)

        while not self.resource.empty():
            self.log.debug("Q:%2d; pre-emptying queue", self.resource.qsize())
            self.resource.get_nowait()

        self.origin.append(self.resource)
        self.log.debug("Q:%3d; receiving item: %d", self.input.qsize(), self.count)
        try:
            frame = self.resource.get(timeout=1)
        except self.q.Empty:
            frame = None

        self.origin.remove(self.resource)

        self.log.debug("Q:%3d; returning frame for display: %d", self.input.qsize(), self.count)
        return frame


class Tracker(Consumer):
    def __init__(self, *args, **kwargs):
        Consumer.__init__(self, *args, **kwargs)

    def process(self, data):
        if data is None:
            return
        try:
            self.log.debug("Q:%3d; tracking frame: %d", self.input.qsize(), self.count)
#            hsv = cv2.cvtColor(data,cv2.COLOR_BGR2HSV)
#            cv2.imshow('hsv', hsv)
            self.count += 1
        except:
            self.log.error('Tracking frame failed on:')
            print data


class Display(Consumer):
    def __init__(self, *args, **kwargs):
        Consumer.__init__(self, *args, **kwargs)

    def process(self, data):
        if data is None:
            return
        try:
            self.log.debug("Q:%3d; displaying frame: %d", self.input.qsize(), self.count)
            cv2.imshow('example', data)
            self.count += 1
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


###############################################################################
#        MAIN LOOP
###############################################################################
if __name__ == '__main__':

    # list of general consumer queues
    consumer_qlist = []
    # list of general producer queues
    producer_qlist = []
    # list of consumers queues for rendering
    gui_qlist = []

    fname, num_frames = examples[1]

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    cv2.namedWindow('example')
#    cv2.namedWindow('hsv')

    logger.info('Instantiating threads')
    g = Grabber(consumer_qlist,
                producer_qlist,
                interval=0.001,
                mode='buffered',
                fname=fname)

    gui_frame_grabber = GUIFrameGrabber(gui_qlist,
                                       producer_qlist,
                                       interval=0.03,
                                       timed='timed',
                                       resource=consumer_qlist)

    d = Display(gui_qlist)
    t = Tracker(consumer_qlist)

    logger.info('Starting up threads')
    d.start()
    gui_frame_grabber.start()
    t.start()
    g.start()
    tstart = time.clock()

    tprev = time.clock()
    cprev = 0
    itv = 0

    while cv2.waitKey(15) < 0 and d.is_alive():
        if t.count-cprev >= 100:
            tel = time.clock()-tprev
            f = t.count-cprev
            logger.info('fps %.1f', f*1.0/tel)
            tprev = time.clock()
            cprev = t.count

        #pass
#    while g.is_alive():
#        time.sleep(0.1)

    logger.info('Frames in source: %d', num_frames)
    logger.info('FPS: %d', num_frames/(time.clock()-tstart))

    logger.info('Stopping all remaining threads...')

    try:
        if g.is_alive():
            g.stop()
        if t.is_alive():
            t.stop()
        if d.is_alive():
            d.stop()
        if gui_frame_grabber.is_alive():
            gui_frame_grabber.stop()
    except:
        pass

    #print threading.enumerate()
