# -*- coding: utf-8 -*-

__author__ = "Travis Anderson, Aaron Jackson"

"""WatchTwitter Class
This is for contacting twitter, and watching a specific user or word.
The tweets found with the word uses a registered function to pass
the data along.
"""
import logging
import tweepy
import os
import datetime
from threading import Thread
import threading

logger = logging.getLogger(os.path.basename(__file__))


def _start(self, is_async):
    """Monkey patch to allow multi threading so twitter can run and
    main program can run"""
    self.running = True
    if is_async:
        logger.warning("Initiating multithread")
        self._thread = Thread(
            target=self._run, name="Tweepy Thread", daemon=True)
        self._thread.start()
    else:
        self._run()


class WatchTwitter(tweepy.StreamListener):
    """Class that subscribes to keywords on twitter """

    def __init__(self):
        logger.info("Creating api")
        consumer_key = os.getenv("API_KEY")
        assert consumer_key is not None
        consumer_secret = os.getenv("API_SECRET")
        access_token = os.getenv("ACCESS_TOKEN")
        access_token_secret = os.getenv("ACCESS_SECRET")
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth)
        tweepy.Stream._start = _start
        self.subscriptions = []
        self._stop_event = threading.Event()
        self.stream_timestamp = 0
        self.master_timestamp = 0
        self.register = None
        self.stream = None

    def __enter__(self):
        """Context manager able to open instance using with"""
        return self

    def __exit__(self, type, value, traceback):
        """Context manager closes stream gracefully"""
        if self.stream is not None and self.stream.running:
            logger.info('shutting down twitbot stream.')
            self.close_stream()

    def close_stream(self):
        """Sets twitter stream running to False"""
        logger.info('Closing Stream')
        self.stream.disconnect()
        self.stream.running = False
        logger.info('Stream Closed')

    def init_stream(self, new_subscriptions):
        """Initiates stream with list of subcscriptions"""
        self.subscriptions = new_subscriptions
        self.start_stream()

    def start_stream(self):
        """Starts new stream connection, closes previous connections"""
        if self.stream:
            self.close_stream()
        logger.info('Subscriptions: {}'.format(self.subscriptions))
        self.stream = tweepy.Stream(auth=self.api.auth, listener=self)
        self.stream.filter(track=self.subscriptions, is_async=True)

    def on_status(self, status):
        """Listens to new stream tweets, register slack function posts slack"""
        if self.register:
            if not status.text.startswith('RT'):
                self.register(status.text)
        else:
            logger.info("not registered yet")

    def register_slack(self, slackfunction):
        """Registers function given from slack"""
        self.register = slackfunction

    def on_connect(self):
        """Listens for connection success, if connected logs time connected"""
        self.stream_timestamp = datetime.datetime.now()
        logger.info('Connected to twitter at: {}'.format(
            datetime.datetime.now()))
        if not self.master_timestamp:
            self.master_timestamp = self.stream_timestamp


def init_logger():
    """Initiate logging to file and terminal"""
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d %(name)-12s \
        %(levelname)-8s [%(threadName)-12s] %(message)s'
    )

    file_handler = logging.FileHandler('slacktweet.log')
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
