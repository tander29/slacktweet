# -*- coding: utf-8 -*-

__author__ = "Aaron Jackson, Travis Anderson"

"""Slackbot Class and SlackTweet Runner.
A Slackbot Class is set up to communicate with slack to post messages and to
take in commands. The commands allows the slackbot to add and remove
subsriptions from a connected twitter bot.
"""

import os
import argparse
import time
import datetime
import signal
from slackclient import SlackClient
from functools import partial
import logging
from logging.handlers import RotatingFileHandler
from twitbot import WatchTwitter
import pprint

logger = logging.getLogger(os.path.basename(__file__))
pp = pprint.PrettyPrinter(indent=2)

exit_flag = False
subscr = []
stats = {}

# commands for slack. posted to slack when help is used.
bot_commands = {
    'help': 'returns list of commands that can be used',
    'add': 'adds subscription to search for on twitter',
    'ping': 'shows uptime of bot',
    'exit': 'stops twitter and slack bots.',
    'start': 'starts twitter bot subscription list(ex: start python piero)',
    'time': 'starts slack bot.',
    'remove': 'removes subscription from list',
    'removeall': 'removes all subscriptions',
    'list': 'shows current subscriptions',
    'stop': 'stops current twitter stream (subscriptions not deleted)',
    'channels': 'to check all available channels',
    'stats': 'shows number of tweets for current subscriptions'
}


class TestException(Exception):
    pass


class Slack_bot(SlackClient):
    """slack_bot class."""
    def __init__(self, token, twit_channel, home_channel, bot_id=None):
        self.sc = SlackClient(token)
        self.channel = twit_channel
        self.home = home_channel
        self.start_time = datetime.datetime.now()
        self.bot_id = bot_id
        if not self.bot_id and self.sc.rtm_connect(with_team_state=False):
            response = self.sc.api_call('auth.test')
            self.name = response.get('user')
            self.bot_id = response.get('user_id')
        self.at_bot = '<@' + self.bot_id + '>'

    def __enter__(self):
        """returns slack obj and connects to rtm if not."""
        mess = "PBJTIME is ONLINE!!!! (with a baseball bat)"
        if self.sc.server.connected:
            logger.info('SlackBot connected to rtm stream')
        else:
            logger.info('SlackBot connected to rtm stream')
            self.sc.rtm_connect(with_team_state=False)
        self.post_command_message(mess, self.home)
        return self

    def __exit__(self, type, value, traceback):
        """lets program know that it is exiting slackbot."""
        logger.info('Exiting slack_bot')

    def read_stream(self):
        """reads stream from slack_client connections."""
        return self.sc.rtm_read()

    def parse_stream(self, content):
        """takes in content from stream and looks for pbjtime mentions."""
        for item in content:
            if 'text' in item and item['text'].startswith(self.at_bot):
                text = item['text'].split(self.at_bot)
                chan = item['channel']
                return (text[1].strip(), chan)
        return (None, None)

    def handle_command(self, text, tb):
        """handles commands that are given and returns message to post."""
        global subscr
        global stats
        args = text.lower().split()
        if args:
            cmd = args[0].lower()
            logger.info('{} cmd was issued.'.format(cmd))
        else:
            cmd = ''
        args = args[1:]
        if cmd == 'raise':
            logger.info('raise test exception')
            raise TestException
        elif cmd == 'help':
            return 'these commands are possible:\n\
                {}'.format(pp.pformat(bot_commands))
        elif cmd == 'time':
            logger.info('bot initialized in slack.')
            return "IT'S PEANUT BUTTER JELLY TIME!! \n(help for more options)"
        elif cmd == 'ping':
            uptime = datetime.datetime.now() - self.start_time
            logger.info('current uptime: {}'.format(uptime))
            return 'Peanut Butter Jelly upTime: {}'.format(uptime)
        elif cmd == 'exit':
            tb.close_stream()
            subscr = []
            tb.subscriptions = []
            stats = {}
            logger.info('pbjtime leaving slack.')
            return "peanut butter jelly time :'( (goodbye)"
        elif cmd == 'start':
            subscr = list(set(subscr + args))
            if not subscr:
                logger.info('no subscr. ignoring and not starting stream.')
                return 'Please add subscriptions so I can find tweets.'
            tb.init_stream(subscr)
            logger.info('started stream with subscriptions: {}'.format(subscr))
            for subs in subscr:
                if subs not in stats:
                    stats[subs] = 0
            if args:
                return 'Added subscriptions: {}'.format(args)
            return 'Started with subcriptions: {}'.format(subscr)
        elif cmd == 'add':
            subscr = list(set(subscr + args))
            if not subscr or not args:
                logger.info('no new subscriptions. ignoring')
                return 'Please add new subscriptions so I can find tweets.'
            tb.init_stream(subscr)
            for subs in subscr:
                if subs not in stats:
                    stats[subs] = 0
            logger.info('added new subcriptions; restarting stream.')
            return 'Added subscriptions: {}'.format(args)
        elif cmd == 'remove':
            removed = []
            for arg in args:
                if arg in subscr:
                    subscr.remove(arg)
                    removed.append(arg)
                    if arg in stats:
                        del stats[arg]
            if removed:
                logger.info('removed subcriptions: {}'.format(arg))
                tb.init_stream(subscr)
                logger.info('restarted twitter stream.')
                return 'removed subcriptions: {} and restarted.'.format(arg)
            else:
                logger.info('no subscriptions matching input. ignoring')
                return 'No subscriptions removed. use list to see current.'

        elif cmd == 'removeall':
            subscr = []
            tb.close_stream()
            tb.subscriptions = []
            stats = {}
            logger.info('All subscriptions removed')
            return 'all subscriptions removed!'
        elif cmd == 'list':
            logger.info('channel list: {}'.format(subscr))
            return 'current subscriptons: \n {}'.format(subscr)
        elif cmd == 'stop':
            logger.info('Stopping twitter stream')
            tb.close_stream()
            logger.info('stream closed on slack side.')
            return 'Twitter stream has been stopped.'
        elif cmd == 'channels':
            self.channel_list()
        elif cmd == 'stats':
            logger.info('stats: {}'.format(pp.pformat(stats)))
            return 'subscription stats: {}'.format(pp.pformat(stats))
        elif cmd not in bot_commands:
            logger.info('unknown command issued')
            return 'Peanut Butter Jelly Time??? use help for more options.'
        else:
            logger.warning('made it through if else block: {}'.format(cmd))
            return None

    def post_command_message(self, mess, channel):
        """posts message after command is completed."""
        logger.info('Sent response to channel: {}'.format(channel))
        self.sc.rtm_send_message(channel, mess)

    def post_twit_mess(self, mess):
        """Posts message from twitter bot to initial channel."""
        global stats
        global subscr
        for scr in subscr:
            if mess.lower().find(scr) >= -1:
                stats[scr] += 1
        self.sc.api_call("chat.postMessage", channel=self.channel, text=mess)

    def channel_list(self):
        logger.info('requesting channel list')
        logger.info(pp.pformat(self.sc.api_call("channels.list")))


def sig_handler(logger, sig_num, frame):
    """Handles OS signals SIGTERM and SIGINT."""
    global exit_flag
    sigs = dict((k, v) for v, k in reversed(sorted(signal.__dict__.items()))
                if v.startswith('SIG') and not v.startswith('SIG_'))
    logger.warning('Received OS Signal: {}'.format(sigs[sig_num]))

    # only exit if it is a sigterm or sigint
    if sig_num == signal.SIGINT or sig_num == signal.SIGTERM:
        exit_flag = True


def exit_logger(app_start_time):
    """Makes ending banner for logging."""
    uptime = datetime.datetime.now() - app_start_time
    logger.info(
        '\n'
        '-------------------------------------------------------------------\n'
        '   Stopped {}\n'
        '   Uptime was {}\n'
        '-------------------------------------------------------------------\n'
        .format(__file__, str(uptime)))


def init_logger(start_time):
    """Makes starting banner for logging."""

    logger.info(
        '\n'
        '-------------------------------------------------------------------\n'
        '    Running {0}\n'
        '    Started on {1}\n'
        '-------------------------------------------------------------------\n'
        .format(__file__, start_time.isoformat())
    )


def create_logger(logging_level):
    """Creates logger for program."""

    logger.setLevel(logging_level)

    formatter = logging.Formatter(
        fmt='%(asctime)s.%(msecs)03d %(name)-12s '
        '%(levelname)-8s [%(threadName)-12s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    file_handler = RotatingFileHandler("slacktweet.log", maxBytes=10000,
                                       backupCount=10)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logging.basicConfig(
        format=(
            '%(asctime)s.%(msecs)03d %(name)-12s %(levelname)-8s '
            '[%(threadName) -12s] %(message)s'),
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging_level,
        handlers=[file_handler, console_handler]
    )


def determine_level(log_level):
    """returns value for log level given. default INFO"""
    levels_dict = {
        'critical': 50,
        'error': 40,
        'warning': 30,
        'info': 20,
        'debug': 10,
    }

    if log_level.lower() in levels_dict:
        return levels_dict[log_level.lower()]
    else:
        return 20


def create_parser():
    """Creates Parser to pull in log level provided."""
    parser = argparse.ArgumentParser(description='SlackTweet Arguments')
    parser.add_argument(
        '-l', '--log',
        help='Log Level for logging. (Default=INFO)',
        type=str,
        default='INFO',
    )
    return parser


def main():
    parser = create_parser().parse_args()
    log_level_value = determine_level(parser.log)
    create_logger(log_level_value)
    # start time
    app_start_time = datetime.datetime.now()
    # make  beginning banner
    init_logger(app_start_time)

    # handlers for SIGINT and SIGTERM
    # partial used to pass in more for parameter
    signal.signal(signal.SIGINT, partial(sig_handler, logger))
    signal.signal(signal.SIGTERM, partial(sig_handler, logger))

    st = os.getenv('SLACK_API_TOKEN')
    ch = os.getenv('CHANNEL')
    bi = os.getenv('BOT_ID')
    home = os.getenv('HOME_CHANNEL')
    # handles exit outside of main function
    while not exit_flag:
        try:
            with Slack_bot(st, ch, home, bot_id=bi) as sb:
                with WatchTwitter() as tb:
                    tb.register_slack(sb.post_twit_mess)
                    while not exit_flag:
                            stream = sb.read_stream()
                            text, chan = sb.parse_stream(stream)
                            if text is not None and chan:
                                message = sb.handle_command(text, tb)
                                if message:
                                    sb.post_command_message(message, chan)
                            time.sleep(1)
        except Exception as e:
            logger.error('UnCaught exception: {}: {}'
                         .format(type(e).__name__, e))
            logger.info('restarting after error')
            sb.post_command_message('restarting PBJTIME', home)
            time.sleep(1)

    exit_logger(app_start_time)
    return 0


if __name__ == "__main__":
    exit(main())
