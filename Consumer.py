#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 01 17:44:21 2013
@author: <Ronny Eichler> ronny.eichler@gmail.com

"""
import threading
import Queue

class Consumer(threading.Thread):
    """ Threaded consumer class.
    Takes: List of consumers owned by parent

    Returns:
    """

    timeout = 5

    def __init__(self, consumer_list):
        threading.Thread.__init__(self)
        self.consumer_list = consumer_list
        self.input = Queue.Queue()
        self.consumer_list.append(self.input)

    def run(self):
        print self, ' starting up'
        while True:
            try:
                data = self.input.get(timeout=self.timeout)
            except Queue.Empty:
                data = 'timeout'

            if data in ['shutdown', 'timeout']:
                print self, ' ', data
                return
            else:
                self.process(data)

    def process(self, data):
        print self, ' processing data: ', data


    def stop(self):
        self.consumer_list.remove(self.input)
        self.input.put('shutdown')
        self.join()
