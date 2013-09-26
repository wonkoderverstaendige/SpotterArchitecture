#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 01 17:49:37 2013
@author: <Ronny Eichler> ronny.eichler@gmail.com

"""
# sys libs
import threading
import Queue
import logging

# user libs
from RepeatTimer import RepeatTimer

#logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Producer(threading.Thread):
    # time to tolerate an empty input Queue. Thread only stops on timeout when
    # in timed mode
    timeout = 5
    # number of produced items
    count = 0
    # flag if timed loop is already running
    loop_active = False

    def __init__(self, consumers, producers, interval=0.033, mode='timed', resource=None, *args, **kwargs):
        """
        Producers are separate threads that create data objects at regular
        intervals.
        """
        threading.Thread.__init__(self)
        # helper reference to make implementing produce() easier
        self.q = Queue

        self.consumers = self._as_iterable(consumers)
        self.producers = self._as_iterable(producers)

        # attach own input Queue to list of producers
        self.input = Queue.Queue(maxsize=16)
        self.producers.append(self.input)
        self.resource = resource

        self.timer = RepeatTimer(interval, self._timed_callable)
        self.run_mode = mode

        if 'logger' in kwargs:
            self.log = kwargs['logger']
        else:
            self.log = logging.getLogger(__name__)

    def run(self):
        """
        Start the main loop of the thread. Runs until a shutdown command is
        received or the stop() method was called.
        """
        self.log.info('%s starting up ...', self)
        if self.run_mode == 'timed':
            self._run_timed()
        else:
            self._run_buffered()

    def produce(self):
        """
        This dummy function has to be re-implemented for each instance of
        this class.
        """
        pass

    def stop(self):
        """
        Adds shutdown signal to input Queue. When processed, will stop the
        repeating timer and remove the producer from the producer queue list.
        """
        self.log.info('%s stopping...', self)
        self.input.put('shutdown')

    def _run_timed(self):
        """
        Thread loop when running in timed loop, with produce() function
        called once per timer firing every interval.
        """
        self.log.info('%s ready in timed mode', self)
        self.timer.start()
        while True:
            try:
                data = self.input.get(timeout=self.timeout)
            except Queue.Empty:
                data = 'timeout'

            # terminate loop on shutdown signal
            if data in ['shutdown', 'timeout']:
                self._remove()
                self.log.info('%s exiting on %s', self, data)
                self.timer.cancel()
                return

            # append data to all consumer queues
            self._distribute(data)

    def _timed_callable(self):
        """
        Callback function for timer. Calls implemented produce() function
        which returns the data this thread produces.
        """
        if self.loop_active:
            # hitting timer interval when previous call is still active
            self.log.warning("% missed a frame!", self)
            return
        self.loop_active = True
        product = self.produce()
        if product is not None:
            try:
                self.input.put(product, block=True)
            except Queue.Full:
                self.log.warning("% input Queue full.", self)
        self.loop_active = False

    def _run_buffered(self):
        """
        Thread loop when running in buffered mode, with produce() function
        being called as fast as possible as long as no Queue is full.
        """
        self.log.info('%s ready in buffered mode', self)
        while True:
            try:
                if not self.input.empty():
                    self.log.debug('%s item in input', self)
                    data = self.input.get_nowait() #timeout=self.timeout
                    # terminate loop on shutdown signal
                    if data in ['shutdown', 'timeout']:
                        self._remove()
                        self.log.info('%s exiting on %s', self, data)
                        return
            except Queue.Empty:
                self.log.error('%s timed out reading input Queue in buffered mode!!', self)

            while self._can_distribute():
                product = self.produce()
                if product is not None:
                    # append data to all consumer queues
                    self._distribute(product)
                else:
                    break


    def _can_distribute(self):
        """ Check if a) any queues full, or b) a priority queue is full. """
        for c in self.consumers:
            if c.full():
                return False
        return True

    def _distribute(self, data):
        """
        Add data to all consumer queues.
        """
        for c in self.consumers:
            try:
                c.put(data)
            except Queue.Full:
                self.log.info("% a consumer Queue is full.", self)

    def _remove(self):
        """
        Remove self from the linked list of producers.
        """
        if self.input in self.producers:
            self.producers.remove(self.input)

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
