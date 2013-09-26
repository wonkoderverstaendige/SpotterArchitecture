#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 01 17:44:21 2013
@author: <Ronny Eichler> ronny.eichler@gmail.com

"""
import threading
import Queue
import logging

#logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Consumer(threading.Thread):
    """ Threaded consumer class.
    Takes: List of consumers owned by parent

    Returns:
    """
    # tolerated time without input. After that, die
    timeout = 5
    # number of received items
    count = 0

    def __init__(self, consumers, *args, **kwargs):
        threading.Thread.__init__(self)
        self.consumers = self._as_iterable(consumers)
        self.input = Queue.Queue(maxsize=16)
        self.consumers.append(self.input)

        if 'logger' in kwargs:
            self.log = kwargs['logger']
        else:
            self.log = logging.getLogger(__name__)

    def run(self):
        self.log.info('%s starting up', self)
        while True:
            try:
                data = self.input.get(timeout=self.timeout)
            except Queue.Empty:
                data = 'timeout'

            if data in ['shutdown', 'timeout']:
                self.log.info('%s exiting on %s', self, data)
                return
            else:
                self.process(data)

    def process(self, data):
        self.log.debug('Q: %d; %s processing data:', self.input.qsize(), self, data)


    def stop(self):
        self.consumers.remove(self.input)
        self.input.put('shutdown')
        self.join()

    def _as_iterable(self, maybe_iterable):
        """
        Check if iterable. If not, wrap in list.

        !!! Does not work on strings
        """
        try:
            iter(maybe_iterable)
        except TypeError:
            # not iterable, wrap
            return [maybe_iterable]
        else:
            # is iterable, return as is
            return maybe_iterable
