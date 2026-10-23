from tests.support import fixtures
fixtures.global_setup()

import requests
import unittest
from unittest.mock import patch
from urllib.parse import parse_qsl

from resources.lib import ipwww_video
from support.testutils import NotLoggedInCookieJar


class AuthenticatedPages(fixtures.WebTestCase):
    def test_resume_wathing(self):
        ipwww_video.ListWatching()


class TestAddAvailableStreamItem(fixtures.WebTestCase):
    def test_play_epdisode(self):
        ipwww_video.AddAvailableStreamItem(
            'https://www.bbc.co.uk/iplayer/episode/m001p3q5/who-do-you-think-you-are-series-20-9-lesley-manville',
        )



@patch('xbmcplugin.addDirectoryItem')
class GenericListings(fixtures.WebTestCase):
    def test_list_live(self, p_add_item):
        self.assertRaises(SystemExit, ipwww_video.ListLive)
        self.assertEqual(p_add_item.call_count, 33)

    def test_list_most_popular(self, p_add_item):
        ipwww_video.ListMostPopular()
        self.assertGreater(p_add_item.call_count, 10)

    def test_list_recommendations(self, p_add_item):
        ipwww_video.ListRecommendations()
        self.assertEqual(p_add_item.call_count, 2)
        p_add_item.reset_mock()
        ipwww_video.ListRecommendations('recommendations')
        self.assertEqual(p_add_item.call_count, 12)
        p_add_item.reset_mock()
        ipwww_video.ListRecommendations('if-you-liked')
        self.assertEqual(p_add_item.call_count, 12)

    @patch('resources.lib.ipwww_common.cookie_jar', NotLoggedInCookieJar())
    def test_list_recommendations_not_signed_in(self, p_add_item):
        # The rather unusual situation where auto sign-in succeeds, but iplayer's main page still
        # returns a not signed in status.
        ipwww_video.ListRecommendations()
        self.assertEqual(p_add_item.call_count, 0)
        # The more usual situation where auto sign-in also fails
        with patch('resources.lib.ipwww_video.CheckLogin', return_value=False):
            with patch('resources.lib.ipwww_video.CreateBaseDirectory') as p_create_base:
                ipwww_video.ListRecommendations()
                p_create_base.assert_called_once()


class Categories(fixtures.WebTestCase):
    addon_settings = {'paginate_episodes': 1}

    def test_get_all_categories(self):
        ipwww_video.ListCategories()
        self.assertEqual(len(self.li_store), 21)

    def test_category_drama_and_soaps(self):
        self.addon_settings['paginate_episodes'] = 0
        ipwww_video.GetFilteredCategory(url='/iplayer/categories/drama-and-soaps/featured')
        self.assertGreater(len(self.li_store), 6)

    def test_request_all_category_pages(self):
        ipwww_video.ListCategories()
        for path in self.li_store.paths:
            params = dict(parse_qsl(path.split('?')[-1]))
            ipwww_video.GetFilteredCategory(params['url'])


class Highlights(fixtures.WebTestCase):
    def test_get_home_page(self):
        ipwww_video.ListHighlights(highlights_url='iplayer')
        self.assertGreater(len(self.li_store), 10)

    def test_get_highlights_bbc_four(self):
        ipwww_video.ListHighlights(highlights_url='bbcfour')
        self.assertGreaterEqual(len(self.li_store), 10)


class Collections(fixtures.WebTestCase):
    def test_get_single_page_collection(self):
        ipwww_video.GetGroup('m002kgjz')
        self.assertGreater(len(self.li_store), 10)

    def test_get_multi_page_collection(self):
        ipwww_video.GetGroup('comedy-box-sets')
        self.assertGreater(len(self.li_store), 10)


class MyProgrammes(fixtures.WebTestCase):
    def test_added(self):
        ipwww_video.ListFavourites()

    def test_remove_from_added(self):
        PGM_ID = 'b006ml0g'     # QI's ProgrammeID, will probably be available for a very long time.
        ipwww_video.RemoveFavourite(PGM_ID)

    def test_add_to_added(self):
        PGM_ID = 'b006ml0g'


class TvSchedule(fixtures.WebTestCase):
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


class ScrapeAtoZPage(fixtures.WebTestCase):
    @patch('resources.lib.ipwww_video.AddMenuEntry')
    @patch('xbmcaddon.Addon.getSetting', lambda self, x: '1' if x == 'scrape_atoz' else None)
    def test_scrape_page_d(self, p_add):
        result = ipwww_video.GetAtoZPage('d')
        self.assertGreater(p_add.call_count, 10)


class ParseMediaSelector(fixtures.WebTestCase):
    def test_parse_media_selector_vod(self):
        stream_id = 'm0014l55'      # episode of QI
        result = ipwww_video.ParseMediaselector(stream_id)
        self.assertIsInstance(result, tuple)

    def test_parse_media_selector_live(self):
        stream_id = 'bbc_one_london'
        video_streams, caption_streams = ipwww_video.ParseMediaselector(stream_id)
        self.assertIsInstance(video_streams, list)
