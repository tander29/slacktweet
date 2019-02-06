# -*- coding: utf-8 -*-

__author__ = "Travis Anderson"

"""
This is for contacting twitter, and watching a specific user or word

"""
import logging
import tweepy
import time
import os
import datetime
from threading import Thread
import threading

logger = logging.getLogger(os.path.basename(__file__))
exit_flag = False


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
        return self

    def __exit__(self, type, value, traceback):
        if self.stream is not None and self.stream.running:
            self.close_stream()

    def add_subscription(self, subscribe_to):
        """If stream is running adds new subscription, restarts stream"""
        if subscribe_to not in self.subscriptions:
            logger.info('Adding subscription: {}'.format(subscribe_to))
            self.subscriptions.append(subscribe_to)
            logger.info(self.subscriptions)
            self.stream.running = False
            self.start_stream()
        else:
            logger.info("Already subscribed: {}" .format(self.subscriptions))

    def remove_subscription(self, unsubscribe_from):
        logger.info("Attempting to remove {}".format(unsubscribe_from))
        if unsubscribe_from in self.subscriptions:
            logger.info(
                'Removing from subscriptions: {}'.format(unsubscribe_from))
            self.subscriptions.remove(unsubscribe_from)
            self.stream.running = False
            self.start_stream()

    def pause_stream(self):
        if self.stream.running:
            logger.info("Pausing all subscriptions: {}".format(
                self.subscriptions))
            self.stream.running = False

    def restart_stream(self):
        if not self.stream.running:
            logger.info("Restarting stream")
            self.start_stream()

    def close_stream(self):
        logger.info('Closing Stream')
        self.stream.disconnect()
        self.stream.running = False
        logger.info('Stream Closed')

    def init_stream(self, new_subscriptions):
        self.subscriptions = new_subscriptions
        self.start_stream()

    def start_stream(self):
        global exit_flag
        exit_flag = False
        if self.stream:
            self.close_stream()
        logger.info('Subscriptions: {}'.format(self.subscriptions))
        self.stream = tweepy.Stream(auth=self.api.auth, listener=self)
        self.stream.filter(track=self.subscriptions, is_async=True)

    def on_status(self, status):
        # need a stream handler, if not none run the stream handler and
        # send the status to slack, else return not exit flag
        if self.register:
            if not status.text.startswith('RT'):
                # logger.info(status.text)
                self.register(status.text)
        else:
            logger.info("not registered yet")

    def register_slack(self, slackfunction):
        self.register = slackfunction

    def on_connect(self):
        self.stream_timestamp = datetime.datetime.now()
        logger.info('Connected to twitter at: {}'.format(
            datetime.datetime.now()))
        if not self.master_timestamp:
            self.master_timestamp = self.stream_timestamp


# def log_config():
#     """Adjusts how info is displayed in log"""
#     return logging.basicConfig(
#         format=(
#             '%(asctime)s.%(msecs)03d %(name)-12s %(levelname)-8s '
#             '[%(threadName) -12s] %(message)s'),
#         datefmt='%Y-%m-%d %H:%M:%S')


# def log_set_level():
#     """Sets defaulf log level"""
#     logger.setLevel(logging.DEBUG)


def init_logger():
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


# def main():
#     global exit_flag
#     log_config()
#     log_set_level()

#     tb = WatchTwitter()
#     tb.init_stream('python')
#     while not exit_flag:
#         time.sleep(5)
#         tb.pause_stream()
#         time.sleep(5)
#         tb.add_subscription('Trump')
#         time.sleep(5)
#         tb.remove_subscription('Trump')


# if __name__ == "__main__":
#     main()
#     pass
