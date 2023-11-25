from tests.support import fixtures
fixtures.global_setup()

import requests
import unittest
from unittest.mock import patch
from http import cookiejar

from resources.lib import ipwww_video


setUp = fixtures.setup_web_test()


class AuthenticatedPages(unittest.TestCase):
    def test_resume_wathing(self):
        with patch('resources.lib.ipwww_common.cookie_jar', new=cookiejar.LWPCookieJar()):
            ipwww_video.ListWatching(logged_in=True)



class TestAddAvailableStreamItem(unittest.TestCase):
    def test_play_epdisode(self):
        ipwww_video.AddAvailableStreamItem(
            'Episode',
            'https://www.bbc.co.uk/iplayer/episode/m001p3q5/who-do-you-think-you-are-series-20-9-lesley-manville',
            None,
            '')


@patch('resources.lib.ipwww_video.ParseJSON')
class GenericListings(unittest.TestCase):
    def test_list_live(self, _):
        ipwww_video.ListLive()

    def test_list_most_popular(self, patched_parse):
        ipwww_video.ListMostPopular()
        patched_parse.assert_called_once()
        data = patched_parse.call_args[0][0]
        self.assertTrue(data['id']['signedIn'])


class TvSchedule(unittest.TestCase):
    def test_tv_schedules(self):
        schedules = ipwww_video.GetSchedules()
        self.assertEqual(4, len(schedules))