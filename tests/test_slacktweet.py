import unittest
from twitbot import WatchTwitter


class TestSlack(unittest.TestCase):
    def setUp(self):
        self.tb = WatchTwitter()
        self.tb.start_stream()

    def tearDown(self):
        self.tb.stream.disconnect()
        del self.tb

    def test_stream_created(self):
        self.assertTrue(self.tb.stream)
        # assert self.tb.stream is not None
