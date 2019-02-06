# -*- coding: utf-8 -*-

import os
import time
import datetime
import signal
from slackclient import SlackClient
from functools import partial
import logging
import twitbot
import pprint

logger = logging.getLogger(os.path.basename(__file__))
pp = pprint.PrettyPrinter(indent=2)

exit_flag = False
started = False
subscr = []

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
    'channels': 'to check all available channels'
}


class slack_bot(SlackClient):
    """slack_bot class."""
    def __init__(self, token, channel, bot_id=None):
        self.sc = SlackClient(token)
        self.channel = channel
        self.start_time = datetime.datetime.now()
        self.bot_id = bot_id
        if not self.bot_id and self.sc.rtm_connect(with_team_state=False):
            response = self.sc.api_call('auth.test')
            self.name = response.get('user')
            self.bot_id = response.get('user_id')
        self.at_bot = '<@' + self.bot_id + '>'

    def __enter__(self):
        """returns slack obj and connects to rtm if not."""
        if self.sc.server.connected:
            logger.info('SlackBot connected to rtm stream')
            return self
        else:
            logger.info('SlackBot connected to rtm stream')
            self.sc.rtm_connect(with_team_state=False)
            return self

    def __exit__(self, type, value, traceback):
        """lets program know that it is exiting slackbot."""
        logger.info('Exiting slack_bot')

    def read_stream(self):
        """reads stream from slack_client connections."""
        return self.sc.rtm_read()

    def parse_stream(self, content):
        """takes in content from stream and looks for pbjtime mentions."""
        # logger.info(content)
        for item in content:
            if 'text' in item and item['text'].startswith(self.at_bot):
                text = item['text'].split(self.at_bot)
                chan = item['channel']
                return (text[1].strip(), chan)
        return (None, None)

    def handle_command(self, text, tb):
        """handles commands that are given and returns message to post."""
        global started
        global subscr
        args = text.lower().split()
        if args:
            cmd = args[0].lower()
            logger.info('{} cmd was issued.')
        else:
            cmd = ''
        args = args[1:]
        if not started and cmd != 'time':
            return 'Peanut? Butter? Jelly?!? Time?!?!? (time cmd to start me)'
        elif cmd not in bot_commands:
            return 'Peanut Butter Jelly Time??? use help for more options.'
        elif cmd == 'help':
            return 'these commands are possible: {}'.format(bot_commands)
        elif cmd == 'time':
            started = True
            return "IT'S PEANUT BUTTER JELLY TIME!! \n(help for more options)"
        elif cmd == 'ping':
            uptime = datetime.datetime.now() - self.start_time
            return 'Peanut Butter Jelly upTime: {}'.format(uptime)
        elif cmd == 'exit':
            started = False
            tb.close_stream()
            subscr = []
            tb.subscriptions = []
            return "peanut butter jelly time :'( (goodbye)"
        elif cmd == 'start':
            subscr = list(set(subscr + args))
            if not subscr:
                return 'Please add subscriptions so I can find tweets.'
            tb.init_stream(subscr)
            if args:
                return 'Added subscriptions: {}'.format(args)
            return 'Started with subcriptions: {}'.format(subscr)
        elif cmd == 'add':
            subscr = list(set(subscr + args))
            if not subscr or not args:
                return 'Please add new subscriptions so I can find tweets.'
            tb.init_stream(subscr)
            return 'Added subscriptions: {}'.format(args)
        elif cmd == 'remove':
            removed = []
            for arg in args:
                if arg in subscr:
                    subscr.remove(arg)
                    removed.append(arg)
            tb.init_stream(subscr)
            return 'removed subcriptions: {} and restarted.'.format(args)
        elif cmd == 'removeall':
            subscr = []
            tb.close_stream()
            tb.subscriptions = []
            return 'all subscriptions removed!'
        elif cmd == 'list':
            return 'current subscriptons: \n {}'.format(subscr)
        elif cmd == 'stop':
            logger.info('Stopping twitter stream')
            tb.close_stream()
            logger.info('stream closed on slack side.')
            return 'Twitter stream has been stopped.'
        elif cmd == 'channels':
            self.channel_list()
        else:
            return None

    def post_command_message(self, message, channel):
        """posts message after command is completed."""
        self.sc.rtm_send_message(channel, message)

    def post_twit_mess(self, message):
        """Posts message from twitter bot to initial channel."""
        self.sc.api_call("chat.postMessage", channel=self.channel, text=message)

    def channel_list(self):
        logger.info('requesting channel list')
        logger.info(pp.pformat(self.sc.api_call("channels.list")))


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

    create_logger()
    # start time
    app_start_time = datetime.datetime.now()
    # make  beginning banner
    init_logger(logger, app_start_time)

    # handlers for SIGINT and SIGTERM
    # partial used to pass in more for parameter
    signal.signal(signal.SIGINT, partial(sig_handler, logger))
    signal.signal(signal.SIGTERM, partial(sig_handler, logger))

    st = os.getenv('SLACK_API_TOKEN')
    ch = os.getenv('CHANNEL')
    bi = os.getenv('BOT_ID')

    with slack_bot(st, ch, bot_id=bi) as sb:
        with twitbot.WatchTwitter() as tb:
            twitbot.init_logger()
            tb.register_slack(sb.post_twit_mess)
            while not exit_flag:
                stream = sb.read_stream()
                text, chan = sb.parse_stream(stream)
                if text is not None and chan:
                    message = sb.handle_command(text, tb)
                    if message:
                        sb.post_command_message(message, chan)
                time.sleep(1)

    exit_logger(logger, app_start_time)
    return 0


if __name__ == "__main__":
    exit(main())
