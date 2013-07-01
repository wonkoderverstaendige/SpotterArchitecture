#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 01 17:49:37 2013
@author: <Ronny Eichler> ronny.eichler@gmail.com

"""
import threading
import Queue
from RepeatTimer import RepeatTimer

class Producer(threading.Thread):
    timeout = 5

    def __init__(self, consumer_list, producer_list, resource=None):
        threading.Thread.__init__(self)
        self.consumer_list = consumer_list
        self.producer_list = producer_list
        self.input = Queue.Queue()
        self.producer_list.append(self.input)

        self.resource = resource
        self.timer = RepeatTimer(0.033, self.produce_callable)

    def run(self):
        print self, ' starting up'
        self.timer.start()
        while True:
            try:
                data = self.input.get(timeout=self.timeout)
            except Queue.Empty:
                data = 'timeout'

            if data in ['shutdown', 'timeout']:
                print self, ' ', data
                self.timer.cancel()
                return
            self.distribute(data)

    def produce(self):
        pass
#        if self.resource is None:
#            return None
#        else:
#            # PRODUCE SOMETHING WITH THE RESOURCE HERE
#            return None

    def produce_callable(self):
        product = self.produce()
        if product is not None:
            self.input.put(product)

    def distribute(self, data):
        for c in self.consumer_list:
            c.put(data)

    def stop(self):
        self.producer_list.remove(self.input)
        self.input.put('shutdown')
        self.join()
