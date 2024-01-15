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


@patch('resources.lib.ipwww_video.ParseJSON')
class GenericListings(unittest.TestCase):
    def test_list_most_popular(self, patched_parse):
        ipwww_video.ListMostPopular()
        patched_parse.assert_called_once()
        data = patched_parse.call_args[0][0]
        self.assertTrue(data['id']['signedIn'])


class MyProgrammes(unittest.TestCase):
    def test_added(self):
        ipwww_video.ListFavourites()

    def test_remove_from_added(self):
        PGM_ID = 'b006ml0g'     # QI's ProgrammeID, will probably be available for a very long time.
        ipwww_video.RemoveFavourite(PGM_ID)

    def test_add_to_added(self):
        PGM_ID = 'b006ml0g'
