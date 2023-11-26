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
        ('bbc_one_hd',                       'BBC One',                  'bbcone',        ''),
        ('bbc_two_england',                  'BBC Two',                  'bbctwo',        ''),
        ('bbc_three_hd',                     'BBC Three',                'bbcthree',      ''),
        ('bbc_four_hd',                      'BBC Four',                 'bbcfour',       ''),
        ('cbbc_hd',                          'CBBC',                     'cbbc',          ''),
        ('cbeebies_hd',                      'CBeebies',                 'cbeebies',      ''),
        ('bbc_news24',                       'BBC News Channel',         'bbcnews',       ''),
        ('bbc_parliament',                   'BBC Parliament',           'bbcparliament', ''),
        ('bbc_alba',                         'Alba',                     'bbcalba',       ''),
        ('bbc_scotland_hd',                  'BBC Scotland',             'bbcscotland',   ''),
        ('s4cpbs',                           'S4C',                      's4c',           ''),
        ('bbc_one_london',                   'BBC One London',           'bbcone',        'lo'),
        ('bbc_one_scotland_hd',              'BBC One Scotland',         'bbcone',        'sc'),
        ('bbc_one_northern_ireland_hd',      'BBC One Northern Ireland', 'bbcone',        'ni'),
        ('bbc_one_wales_hd',                 'BBC One Wales',            'bbcone',        'wa'),
        ('bbc_two_scotland',                 'BBC Two Scotland',         'bbctwo',        'sc'),
        ('bbc_two_northern_ireland_digital', 'BBC Two Northern Ireland', 'bbctwo',        'ni'),
        ('bbc_two_wales_digital',            'BBC Two Wales',            'bbctwo',        'wa'),
        ('bbc_two_england',                  'BBC Two England',          'bbctwo',        ''),
        ('bbc_one_cambridge',                'BBC One Cambridge',        'bbcone',        ''),
        ('bbc_one_channel_islands',          'BBC One Channel Islands',  'bbcone',        'ci'),
        ('bbc_one_east',                     'BBC One East',             'bbcone',        'ea'),
        ('bbc_one_east_midlands',            'BBC One East Midlands',    'bbcone',        'em'),
        ('bbc_one_east_yorkshire',           'BBC One East Yorkshire',   'bbcone',        'ey'),
        ('bbc_one_north_east',               'BBC One North East',       'bbcone',        'ne'),
        ('bbc_one_north_west',               'BBC One North West',       'bbcone',        'nw'),
        ('bbc_one_oxford',                   'BBC One Oxford',           'bbcone',        ''),
        ('bbc_one_south',                    'BBC One South',            'bbcone',        'so'),
        ('bbc_one_south_east',               'BBC One South East',       'bbcone',        'se'),
        ('bbc_one_south_west',               'BBC One South West',       'bbcone',        'sw'),
        ('bbc_one_west',                     'BBC One West',             'bbcone',        'we'),
        ('bbc_one_west_midlands',            'BBC One West Midlands',    'bbcone',        'wm'),
        ('bbc_one_yorks',                    'BBC One Yorks',            'bbcone',        'yo'),
    ]
    def test_tv_schedules(self):
        schedules = ipwww_video.GetSchedules(self.channel_list)
        # bbc_two_england occurs both as BBC Two and BBC TWo England
        self.assertEqual(len(self.channel_list) - 1, len(schedules))