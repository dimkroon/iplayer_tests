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
        ipwww_video.ListWatching()


class TestAddAvailableStreamItem(unittest.TestCase):
    def test_play_epdisode(self):
        ipwww_video.AddAvailableStreamItem(
            'Episode',
            'https://www.bbc.co.uk/iplayer/episode/m001p3q5/who-do-you-think-you-are-series-20-9-lesley-manville',
            None,
            '')


class GenericListings(unittest.TestCase):
    @patch('resources.lib.ipwww_video.ParseJSON')
    def test_list_most_popular(self, patched_parse):
        ipwww_video.ListMostPopular()
        patched_parse.assert_called_once()
        data = patched_parse.call_args[0][0]
        self.assertTrue(data['id']['signedIn'])

    def test_list_recommendations(self):
        with patch('xbmcplugin.addDirectoryItem') as p_add_item:
            ipwww_video.ListRecommendations()
            self.assertGreater(p_add_item.call_count, 5)