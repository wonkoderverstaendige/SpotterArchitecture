#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 01 15:53:41 2013
@author: <Ronny Eichler> ronny.eichler@gmail.com

"""

import cv2

from Producer import Producer
from Consumer import Consumer

consumer_queues = []
producer_queues = []

class Grabber(Producer):
    def __init__(self, *args, **kwargs):
        Producer.__init__(self, *args, **kwargs)
        self.resource = cv2.VideoCapture('../example.wmv')
        self.timer.change_interval(0.001)

    def produce(self):
        if self.resource is not None:
            rv, frame = self.resource.read()
            if rv:
                return frame


class Display(Consumer):
    def __init__(self, *args, **kwargs):
        Consumer.__init__(self, *args, **kwargs)
        self.timeout = 1

    def process(self, data):
        try:
            cv2.imshow('example', data)
        except:
            print 'Displaying frame failed!'


class Tracker(Consumer):
    def __init__(self, *args, **kwargs):
        Consumer.__init__(self, *args, **kwargs)
        self.timeout = 1

    def process(self, data):
        try:
            hsv = cv2.cvtColor(data,cv2.COLOR_BGR2HSV)
            cv2.imshow('hsv', hsv)
        except:
            print 'Tracking frame failed!'


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
    cv2.namedWindow('example')
    cv2.namedWindow('hsv')
    g = Grabber(consumer_queues, producer_queues)
    d = Display(consumer_queues)
    t = Tracker(consumer_queues)

    d.start()
    t.start()
    g.start()

    while cv2.waitKey(15) < 0 and d.is_alive():
        pass

    g.stop()
    t.stop()
    d.stop()

    #print threading.enumerate()
