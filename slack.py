# -*- coding: utf-8 -*-

import os
import time
import datetime
import signal
from slackclient import SlackClient
from functools import partial
import threading
import re
import logging

exit_flag = False

pbjtime_bot = {
    'id': 'UFC5PM47',
    'name': 'pbjtime',
    'real_name': 'pbjtime',
    'slack_token': os.environ["SLACK_API_TOKEN"],
    'channel': 'CFMDNFA58'
}


class SlackNotConnected(Exception):
    pass


class slack_bot:
    """slack_bot class."""
    def __init__(self, slack_bot, SlackClient):
        self.slack_bot = slack_bot
        self.sc = SlackClient(slack_bot['slack_token'])
        self.channel = ''
        self.message = ''

    def start_stream(self):
        return self.sc.rtm_connect()

    def read_stream(self):
        try:
            return self.sc.rtm_read()
        except SlackNotConnected as e:
            print('not connected to slack. {}'.format(e))

    def parse_stream(self, content):
        """takes in content from stream and looks for pbjtime mentions."""
        for item in content:
            if 'type' in item and item['type'] == 'message' and 'text' in item:
                self.message = item['text']
                self.channel = item['channel']

    def send_message(self, channel):
        mess = "it's peanut butter jelly time!"
        self.sc.rtm_send_message(channel, mess)


def exit_logger(logger, app_start_time):
    """Makes ending banner for logging."""
    uptime = datetime.datetime.now() - app_start_time
    logger.info(
        '\n'
        '-------------------------------------------------------------------\n'
        '   Stopped {}\n'
        '   Uptime was {}\n'
        '-------------------------------------------------------------------\n'
        .format(__file__, str(uptime)))


def init_logger(logger, start_time):
    """Makes starting banner for logging."""

    logger.info(
        '\n'
        '-------------------------------------------------------------------\n'
        '    Running {0}\n'
        '    Started on {1}\n'
        '-------------------------------------------------------------------\n'
        .format(__file__, start_time.isoformat())
    )


def create_logger():
    """Creates logger for program."""
    logger = logging.getLogger(os.path.basename(__file__))
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
    return logger


def sig_handler(logger, sig_num, frame):
    """Handles OS signals SIGTERM and SIGINT."""
    global exit_flag
    sigs = dict((k, v) for v, k in reversed(sorted(signal.__dict__.items()))
                if v.startswith('SIG') and not v.startswith('SIG_'))
    logger.warning('Received OS Signal: {}'.format(sigs[sig_num]))

    # only exit if it is a sigterm or sigint
    if sig_num == signal.SIGINT or sig_num == signal.SIGTERM:
        exit_flag = True


def main():

    logger = create_logger()
    # start time
    app_start_time = datetime.datetime.now()
    # make  beginning banner
    init_logger(logger, app_start_time)

    # handlers for SIGINT and SIGTERM
    # partial used to pass in more for parameter
    signal.signal(signal.SIGINT, partial(sig_handler, logger))
    signal.signal(signal.SIGTERM, partial(sig_handler, logger))

    sc = slack_bot(pbjtime_bot, SlackClient)
    sc.start_stream()
    print(sc.sc)

    while sc.sc.server.connected and not exit_flag:
        stream = sc.read_stream()
        sc.parse_stream(stream)
        # print(stream)
        # sc.send_message(sc.slack_bot['channel'])
        # print(self.sc.server.users)
        time.sleep(1)

    exit_logger(logger, app_start_time)


if __name__ == "__main__":
    main()
