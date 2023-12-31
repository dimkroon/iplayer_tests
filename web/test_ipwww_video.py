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
    def test_list_live(self, _):
        ipwww_video.ListLive()

    def test_list_most_popular(self, patched_parse):
        ipwww_video.ListMostPopular()
        patched_parse.assert_called_once()
        data = patched_parse.call_args[0][0]
        self.assertTrue(data['id']['signedIn'])

    def test_list_recommendations(self):
        with patch('xbmcplugin.addDirectoryItem') as p_add_item:
            ipwww_video.ListRecommendations()
            self.assertGreater(p_add_item.call_count, 5)


class TvSchedule(unittest.TestCase):
    channel_list = [
        ('bbc_one_hd',                       'BBC One',                  'bbc_one_london'),
        ('bbc_two_england',                  'BBC Two',                  'bbc_two_england'),
        ('bbc_three_hd',                     'BBC Three',                'bbc_three'),
        ('bbc_four_hd',                      'BBC Four',                 'bbc_four'),
        ('cbbc_hd',                          'CBBC',                     'cbbc'),
        ('cbeebies_hd',                      'CBeebies',                 'cbeebies'),
        ('bbc_news24',                       'BBC News Channel',         'bbc_news24'),
        ('bbc_parliament',                   'BBC Parliament',           'bbc_parliament'),
        ('bbc_alba',                         'Alba',                     'bbc_alba'),
        ('bbc_scotland_hd',                  'BBC Scotland',             'bbc_scotland'),
        ('s4cpbs',                           'S4C',                      's4cpbs'),
        ('bbc_one_london',                   'BBC One London',           'bbc_one_london'),
        ('bbc_one_scotland_hd',              'BBC One Scotland',         'bbc_one_london'),
        ('bbc_one_northern_ireland_hd',      'BBC One Northern Ireland', 'bbc_one_london'),
        ('bbc_one_wales_hd',                 'BBC One Wales',            'bbc_one_london'),
        ('bbc_two_scotland',                 'BBC Two Scotland',         'bbc_two_england'),
        ('bbc_two_northern_ireland_digital', 'BBC Two Northern Ireland', 'bbc_two_northern_ireland_digital'),
        ('bbc_two_wales_digital',            'BBC Two Wales',            'bbc_two_wales_digital'),
        ('bbc_two_england',                  'BBC Two England',          'bbc_two_england'),
        ('bbc_one_cambridge',                'BBC One Cambridge',        'bbc_one_london'),
        ('bbc_one_channel_islands',          'BBC One Channel Islands',  'bbc_one_london'),
        ('bbc_one_east',                     'BBC One East',             'bbc_one_london'),
        ('bbc_one_east_midlands',            'BBC One East Midlands',    'bbc_one_london'),
        ('bbc_one_east_yorkshire',           'BBC One East Yorkshire',   'bbc_one_london'),
        ('bbc_one_north_east',               'BBC One North East',       'bbc_one_london'),
        ('bbc_one_north_west',               'BBC One North West',       'bbc_one_london'),
        ('bbc_one_oxford',                   'BBC One Oxford',           'bbc_one_london'),
        ('bbc_one_south',                    'BBC One South',            'bbc_one_london'),
        ('bbc_one_south_east',               'BBC One South East',       'bbc_one_london'),
        ('bbc_one_south_west',               'BBC One South West',       'bbc_one_london'),
        ('bbc_one_west',                     'BBC One West',             'bbc_one_london'),
        ('bbc_one_west_midlands',            'BBC One West Midlands',    'bbc_one_london'),
        ('bbc_one_yorks',                    'BBC One Yorks',            'bbc_one_london'),
    ]
    def test_tv_schedules(self):
        schedules = ipwww_video.GetSchedules(self.channel_list)
        # bbc_two_england occurs both as BBC Two and BBC TWo England
        self.assertEqual(len(self.channel_list) - 1, len(schedules))