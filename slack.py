# -*- coding: utf-8 -*-

import os
import time
import datetime
import signal
from slackclient import SlackClient
from functools import partial
import logging

exit_flag = False
started = False

bot_commands = {
    'help': 'returns list of commands that can be used',
    'add': 'adds topic to search for on twitter',
    'ping': 'shows uptime of bot',
    'exit': 'stops twitter and slack bots.',
    'start': 'starts twitter bot listening to topic list',
    'time': 'starts slack bot.'
}


class slack_bot(SlackClient):
    """slack_bot class."""
    def __init__(self, token, channel, logger, start_time, bot_id=None):
        self.sc = SlackClient(token)
        self.channel = channel
        self.logger = logger
        self.start_time = start_time
        self.bot_id = bot_id
        if not self.bot_id and self.sc.rtm_connect(with_team_state=False):
            response = self.sc.api_call('auth.test')
            self.name = response.get('user')
            self.bot_id = response.get('user_id')
        self.at_bot = '<@' + self.bot_id + '>'

    def __enter__(self):
        """returns slack obj and connects to rtm if not."""
        if self.sc.server.connected:
            return self
        else:
            self.sc.rtm_connect(with_team_state=False)
            return self

    def __exit__(self, type, value, traceback):
        """lets program know that it is exiting slackbot."""
        self.logger.info('Exiting slack_bot')

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

    def handle_command(self, text):
        """handles commands that are given and returns message to post."""
        global started
        args = text.split()
        if args:
            cmd = args[0].lower()
        else:
            cmd = ''
        if not started and cmd != 'time':
            return 'Peanut? Butter? Jelly?!? Time?!?!?!?!?!? (use time cmd to start pbjtime)'
        if cmd not in bot_commands:
            return 'Peanut Butter Jelly Time??? use help for more options.'
        if cmd == 'help':
            return 'these commands are possible: {}'.format(bot_commands)
        if cmd == 'time':
            started = True
            return "IT'S PEANUT BUTTER JELLY TIME!!!!!!!!!! \n (help for more options)"
        if cmd == 'ping':
            uptime = datetime.datetime.now() - self.start_time
            return 'Peanut Butter Jelly upTime: {}'.format(uptime)
        if cmd == 'exit':
            started = False
            return "peanut butter jelly time :'( (goodbye)"
        if cmd == 'start':
            return 'command does not work yet'
        if cmd == 'add':
            return 'command does not work yet'
        return None

    def post_command_message(self, message, channel):
        """posts message after command is completed."""
        self.sc.rtm_send_message(channel, message)

    def post_twit_mess(self, message):
        """Posts message from twitter bot to initial channel."""
        self.sc.rtm_send_message(self.channel, message)


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

    st = os.getenv('SLACK_API_TOKEN')
    ch = os.getenv('CHANNEL')
    bi = os.getenv('BOT_ID')

    with slack_bot(st, ch, logger, app_start_time, bot_id=bi) as sb:
        while not exit_flag:
            stream = sb.read_stream()
            text, chan = sb.parse_stream(stream)
            if text is not None and chan:
                message = sb.handle_command(text)
                if message:
                    sb.post_command_message(message, chan)
            time.sleep(1)

    exit_logger(logger, app_start_time)
    return 0


if __name__ == "__main__":
    exit(main())
