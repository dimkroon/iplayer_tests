
from tests.support import fixtures
fixtures.global_setup()

import time
import string
import requests
import math
from datetime import datetime, timezone, timedelta

from http import cookiejar

from unittest import TestCase, skip
from resources.lib import ipwww_common
from resources.lib import ipwww_video
from tests.support.testutils import save_json, save_doc, open_doc, doc_path, ExpiredCookieJar
from tests.support.object_checks import (has_keys, expect_keys, misses_keys, expect_misses_keys, is_not_empty, is_url,
                                         is_iso_utc_time, iso_duration_2_seconds)

setUpModule = fixtures.setup_web_test()


def check_page_has_json_data(testcase, url):
    resp = requests.get(url, headers=ipwww_common.headers, allow_redirects=False)
    # save_doc(resp.text, 'html/category_drama-and-soaps_az.html')
    testcase.assertTrue(200, resp.status_code)
    testcase.assertTrue(resp.headers['content-type'].startswith('text/html'))
    data = ipwww_video.ScrapeJSON(resp.text)
    testcase.assertIsInstance(data, dict)
    return data


def check_synopses(testcase, synopses):
    testcase.assertIsInstance(synopses, dict)
    testcase.assertTrue(any(key in synopses.keys() for key in ('large', 'small', 'medium', 'editorial')))


def check_images(testcase, images):
    testcase.assertTrue(is_not_empty(images, dict))
    img_types = ('portrait', 'standard', 'default', 'live', 'promotional', 'promotional_with_logo',
                 'promotionalWithLogo', 'character', 'portrait')
    for key in images.keys():
        # Just to flag when an unknown image type comes up.
        assert(key=='type' or key in img_types)
    for key, value in images.items():
        if key == 'type':
            testcase.assertEqual(value, 'image')
        else:
            testcase.assertTrue(is_url(value, ('.jpg', '.png')) or value is None)


def check_large_programme_data(testcase, programme, parent_name):
    obj_name = '.'.join((parent_name, programme['title']))
    has_keys(programme, 'id', 'title', 'type', 'images', 'synopses', 'programme_type', 'count',
             'initial_children', obj_name=obj_name)

    expect_keys(programme, 'live', 'labels', 'tleo_type', 'categories', 'master_brand', 'lexical_sort_letter',
                'status', obj_name=obj_name)

    testcase.assertTrue(is_not_empty(programme['id'], str))
    testcase.assertEqual('programme', programme['type'])
    testcase.assertTrue(programme['tleo_type'] in ('episode', 'brand', 'series'))    # just to flag when other values appear.
    testcase.assertTrue(is_not_empty(programme['title'], str))
    check_images(testcase, programme['images'])
    check_synopses(testcase, programme['synopses'])
    testcase.assertTrue(programme['programme_type'] in ('one-off', 'self-contained', 'narrative', 'sequential', 'unclassified', 'strand'))  # just to flag when other values appear.
    testcase.assertTrue(is_not_empty(programme['count'], int))
    testcase.assertIsInstance(programme['initial_children'], list)
    for child in programme['initial_children']:
        check_large_episode_data(testcase, child, '.'.join((obj_name, 'children')))


def check_large_version_data(testcase, version, parent_name=''):
    """A more comprehensive version on Version data, formally observed in data from Watching and Recommendations.
     Now not used, but kept here for future reference.
     """
    obj_name = '.'.join((parent_name, 'version'))
    has_keys(version, 'id', 'kind', 'duration', 'availability', 'first_broadcast_date_time', obj_name=obj_name)

    expect_keys(version, 'hd', 'uhd', 'type', 'events', 'download', 'first_broadcast', obj_name=obj_name)

    testcase.assertTrue(version['kind'] in ('original', 'audio-described', 'signed', 'technical-replacement', 'editorial', 'pre-watershed'))
    testcase.assertTrue(version['type'] in ('version', 'version_large'))
    testcase.assertIsInstance(version['duration'], dict)
    testcase.assertTrue(is_not_empty(version['duration']['text'], str))
    testcase.assertGreater(iso_duration_2_seconds(version['duration']['value']), 39)   # Allow for short news clips
    testcase.assertTrue(is_not_empty(version['availability']['remaining']['text'], str))
    testcase.assertTrue(is_iso_utc_time(version['first_broadcast_date_time']))


def check_version_data(testcase, version, parent_name=''):
    obj_name = '.'.join((parent_name, 'version'))
    has_keys(version, 'kind', 'duration', obj_name=obj_name)
    expect_keys(version, 'availability', obj_name=obj_name)
    misses_keys(version, 'first_broadcast_date_time', 'hd', 'uhd', 'type', 'events', 'download',
                'first_broadcast', obj_name=obj_name)

    testcase.assertTrue(version['kind'] in ('original', 'audio-described', 'signed', 'technical-replacement', 'editorial'))
    testcase.assertIsInstance(version['duration'], dict)
    testcase.assertTrue(is_not_empty(version['duration']['text'], str))
    # Assert iso duration is absent.
    misses_keys(version['duration'], 'value', obj_name=obj_name + '.duration')
    if 'availability' in version.keys():
        testcase.assertTrue(is_not_empty(version['availability']['remaining'], str))


def base_episode_checks(testcase, episode, obj_name=''):
    """Some checks on fields presents in all types of episode data.

    """
    has_keys(episode, 'id', 'title', 'images', 'tleo_id', obj_name=obj_name)
    expect_keys(episode, 'versions', 'synopses', 'subtitle', obj_name=obj_name)

    check_images(testcase, episode['images'])
    testcase.assertTrue(is_not_empty(episode['tleo_id'], str))  # not always the same is 'id'.
    if 'synopses' in episode.keys():
        # Field 'synopses' is optional, e.g. items from 'Watching' lack synopses.
        check_synopses(testcase, episode['synopses'])
    if 'subtitle' in episode.keys():
        # Field 'subtitles' is optional, in particular films and single episode documentaries may lack a subtitle.
        testcase.assertTrue(is_not_empty(episode['subtitle'], str))
    testcase.assertGreaterEqual(len(episode['versions']), 1)


def check_episode_data(testcase, episode, parent_name=''):
    obj_name = '.'.join((parent_name, episode['title']))
    base_episode_checks(testcase, episode, obj_name)
    # All keys from the previously available long version of episode.
    misses_keys(episode, 'type', 'programme_type', 'original_title', 'tleo_type', 'signed', 'audio_described',
                'requires_ab', 'lexical_sort_letter', 'release_date', 'guidance', 'type', 'requires_tv_licence',
                'editorial_subtitle', 'live', 'childrens', 'categories', 'release_date_time', 'master_brand',   # childrens is not a typo (at least not mine)
                'has_credits', 'status', 'requires_sign_in', 'labels', 'signed')
    for version in episode['versions']:
        # Check that a version from a small episode does not parse as full version
        testcase.assertRaises(AssertionError, check_large_version_data, testcase, version, parent_name)
        check_version_data(testcase, version, obj_name)


def check_large_episode_data(testcase, episode, parent_name=''):
    obj_name = '.'.join((parent_name, episode['title']))
    has_keys(episode, 'synopses', 'type', 'original_title', 'programme_type', obj_name=obj_name)

    expect_keys(episode, 'live', 'labels', 'signed', 'status', 'guidance', 'versions', 'childrens',       # childrens is not a typo (at least not mine)
                'tleo_type', 'categories', 'has_credits', 'requires_ab', 'master_brand', 'release_date',
                'audio_described', 'requires_sign_in', 'release_date_time', 'editorial_subtitle', 'lexical_sort_letter',
                'requires_tv_licence', obj_name=obj_name)
    base_episode_checks(testcase, episode, parent_name)
    testcase.assertTrue(episode['type'] in ('episode', 'episode_large'))    # even films and documentaries appear to be of the episode.
    testcase.assertTrue(episode['tleo_type'] in ('episode', 'brand', 'series'))   # just to flag when other values appear.
    testcase.assertIsInstance(episode['signed'], bool)
    testcase.assertIsInstance(episode['audio_described'], bool)         # not always the same is 'id'.
    testcase.assertTrue(is_not_empty(episode['release_date'], str))     # format varies from '2007' to '21 May 2018'
    testcase.assertTrue(is_iso_utc_time(episode['release_date_time']))
    for version in episode['versions']:
        check_large_version_data(testcase, version, obj_name)


def check_episode_data_from_bundle(testcase, episode, parent_name=''):
    """Episodes from bundles from the main page provide roughly the same data, but formatted in a different way"""
    obj_name = '.'.join((parent_name, episode['title']['default']))

    has_keys(episode, 'id', 'title', 'tleo', 'image', 'synopsis', 'subtitle', 'versions', obj_name=obj_name)
    # All keys from the previously available long version of episode.
    misses_keys(episode, 'type', 'programme_type', 'original_title', 'tleo_type', 'signed', 'audio_described',
                'requires_ab', 'lexical_sort_letter', 'release_date', 'guidance', 'type', 'requires_tv_licence',
                'editorial_subtitle', 'childrens', 'categories', 'release_date_time', 'master_brand',   # childrens is not a typo (at least not mine)
                'has_credits', 'status', 'requires_sign_in', 'signed', obj_name=obj_name)
    expect_keys(episode, 'labels', 'live', 'previewId', obj_name=obj_name)

    testcase.assertTrue(is_not_empty(episode['id'], str))
    testcase.assertTrue(is_not_empty(episode['title'], dict))
    testcase.assertTrue(is_not_empty(episode['title']['default'], str))
    testcase.assertTrue(is_not_empty(episode['tleo'], dict))
    testcase.assertTrue(is_not_empty(episode['tleo']['id'], str))
    check_images(testcase, episode['image'] )
    check_synopses(testcase, episode['synopsis'])

    if 'subtitle' in episode.keys():
        subtitle = episode['subtitle']
        # Field 'subtitles' is optional, in particular films and single episode documentaries may lack a subtitle.
        testcase.assertTrue(is_not_empty(subtitle, dict) or subtitle is None)
        if isinstance(subtitle, dict):
            testcase.assertTrue('default' in subtitle.keys())   # There may be other keys, but this is the only one currently used.

    for version in episode['versions']:
        # Check that a version from episode does not parse as full version
        check_version_data(testcase, version, obj_name)


class HtmlPages(TestCase):
    def test_page_index_not_signed_in(self):
        data = check_page_has_json_data(self, 'https://www.bbc.co.uk/iplayer')
        self.assertEqual(12, len(data['bundles']))

    def test_page_index_signed_in(self):
        resp = requests.get('https://www.bbc.co.uk/iplayer', headers=ipwww_common.headers,
                            cookies=ipwww_common.cookie_jar, allow_redirects=False)
        self.assertTrue(200, resp.status_code)
        data = ipwww_video.ScrapeJSON(resp.text)
        self.assertIsInstance(data, dict)
        self.assertEqual(15, len(data['bundles']))


class ChannelsAtoZ(TestCase):
    channels = ('bbcone', 'bbctwo', 'tv/bbcthree', 'tv/cbbc', 'tv/cbeebies', 'tv/bbcnews', 'tv/bbcparliament',
                'tv/bbcalba', 'tv/bbcscotland', 'tv/s4c')

    def test_channel_az_page(self):
        for chan in self.channels:
            check_page_has_json_data(self, 'https://www.bbc.co.uk/{}/a-z'.format(chan))


class CategoriesAtoZ(TestCase):
    categories = ('drama-and-soaps', 'films', 'comedy', 'documentaries', 'sport', 'news', 'entertainment', 'music',
                  'food', 'lifestyle', 'history', 'science-and-nature', 'arts', 'archive', 'audio-described', 'signed',
                  'northern-ireland', 'scotland', 'wales', 'cbeebies', 'cbbc')

    def test_category_az_page(self):
        for cat in self.categories:
            if cat  == 'drama-and-soaps':
                check_page_has_json_data(self, 'https://www.bbc.co.uk/iplayer/categories/{}/a-z'.format(cat))


class ProgrammesAtoZ(TestCase):
    letters = list(string.ascii_lowercase.replace('x','')) + ['0-9']

    def test_a_to_z_pages(self):
        for letter in self.letters:
            data = check_page_has_json_data(self, 'https://www.bbc.co.uk/iplayer/a-z/' + letter)
            pass


class MostPopular(TestCase):
    def test_most_popular_not_signed_in(self):
        resp = requests.get('https://www.bbc.co.uk/iplayer/most-popular', allow_redirects=False)
        self.assertEqual(200, resp.status_code)
        data = ipwww_video.ScrapeJSON(resp.text)
        self.assertFalse(data['id']['signedIn'])

    def test_get_most_popular_permanent_redirect(self):
        resp = requests.get('https://www.bbc.co.uk/iplayer/group/most-popular', allow_redirects=False)
        self.assertTrue(resp.is_permanent_redirect)
        self.assertEqual('https://www.bbc.co.uk/iplayer/most-popular', resp.headers['location'])


class Search(TestCase):
    def test_search(self):
        search_term = 'george'
        url = 'https://www.bbc.co.uk/iplayer/search?q=' + search_term
        data = check_page_has_json_data(self, url)
        # save_json(data, 'html/search-george.json')
        ipwww_video.ParseJSON(data, url)


class Watching(TestCase):
    def test_get_watching_data(self):
        resp = requests.get(url = "https://www.bbc.co.uk/iplayer/continue-watching",
                            headers=ipwww_common.headers,
                            cookies=ipwww_common.cookie_jar,
                            allow_redirects=False)
        self.assertEqual(200, resp.status_code)
        self.assertEqual('text/html; charset=utf-8', resp.headers['content-type'])
        page = resp.text
        data = ipwww_video.ScrapeJSON(page)
        self.assertTrue(data['id']['signedIn'])
        # save_json(data, 'html/watching.json')
        self.assertTrue(data['id']['signedIn'])
        items_list = data['items']['elements']
        for item in items_list:
            has_keys(item, 'status', 'episode', 'programme', obj_name='Watching')
            misses_keys(item, 'version')
            self.assertTrue(item['status'] in ('current', 'next'))
            if item['status'] == 'current':
                has_keys(item, 'remaining', 'progress', obj_name='Watching')
            else:
                misses_keys(item, 'remaining', 'progress', obj_name='Watching')

            # This is the data of the episode (Next, or Watching)
            check_episode_data(self, item['episode'], 'Watching.episode')

            programme = item['programme']
            # Programme data in watching now only contains the programmeID
            self.assertEqual(1, len(programme))
            self.assertTrue(is_not_empty(programme['id'], str))


    def test_get_watching_without_signed_in(self):
        """This just return a normal HTML page with a button to sign in or register."""
        page_url = "https://www.bbc.co.uk/iplayer/continue-watching"
        resp = requests.get(page_url, headers=ipwww_common.headers, allow_redirects=False)
        self.assertEqual(200, resp.status_code)
        self.assertEqual('text/html; charset=utf-8', resp.headers['content-type'])
        data = ipwww_video.ScrapeJSON(resp.text)
        self.assertFalse(data['id']['signedIn'])
        self.assertEqual(0, len(data['items']['elements']))
        # save_doc(resp.text, 'html/watching_not_signed_in.html')

    def test_get_watching_with_signed_in_expired(self):
        """This just return a normal HTML page with a button to sign in or register."""
        with requests.Session() as session:
            session.headers = ipwww_common.headers
            session.cookies = jar = cookiejar.LWPCookieJar()
            jar.load(doc_path('cookies/expired.cookies'), ignore_discard=True)

            resp = session.get(url="https://www.bbc.co.uk/iplayer/continue-watching", allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            new_url = resp.headers['location']
            self.assertTrue(new_url.startswith('https://session.bbc.co.uk/session?'))

            resp = session.get(new_url, allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            self.assertTrue('ckns_id' in resp.cookies)
            self.assertTrue('ckns_atkn' in resp.cookies)
            self.assertTrue('ckns_idtkn' in resp.cookies)
            new_url = resp.headers['location']
            self.assertTrue(new_url.startswith('https://www.bbc.co.uk/iplayer/continue-watching'))

            resp = session.get(new_url, allow_redirects=False)
            self.assertEqual('text/html; charset=utf-8', resp.headers['content-type'])
            data = ipwww_video.ScrapeJSON(resp.text)
            self.assertTrue(data['id']['signedIn'])


class RemoveWatching(TestCase):
    def setUp(self):
        self.headers = ipwww_common.headers.copy()
        self.headers['content-type'] = 'application/json'

    def test_remove_non_existing_item(self):
        """Remove an item that is not on the watching list and may even not exist at all."""
        json_data = {'id': "m021b6v5"}
        resp = requests.post('https://user.ibl.api.bbc.co.uk/ibl/v1/user/hides',
                             headers=self.headers,
                             cookies=ipwww_common.cookie_jar,
                             json=json_data, )
        self.assertEqual(202, resp.status_code)
        self.assertEqual(json_data, resp.json())

    def test_remove_watching_item_unauthenticated(self):
        resp = requests.post('https://user.ibl.api.bbc.co.uk/ibl/v1/user/hides',
                             headers=self.headers,
                             json={'id': "m001b6v5"}, )
        self.assertEqual(401, resp.status_code)
        data = resp.json()
        self.assertEqual('Missing authorization header', data['error']['details'])


class TestWatchlist(TestCase):
        """User's own favourites"""
        def test_get_watchlist_signed_in(self):
            resp = requests.get('https://www.bbc.co.uk/iplayer/watchlist',
                                headers=ipwww_common.headers,
                                cookies=ipwww_common.cookie_jar,
                                allow_redirects=False)
            self.assertEqual(200, resp.status_code)
            self.assertEqual('text/html; charset=utf-8', resp.headers['content-type'])
            page = resp.text
            data = ipwww_video.ScrapeJSON(page)
            # save_json(data, 'html/watchlist.json')
            self.assertTrue(data['id']['signedIn'])
            self.assertEqual('watchlist', data['items']['pageType'])
            items_list = data['items']['elements']
            for item in items_list:
                # item is a dict with only a single key: 'programme'
                self.assertEqual(1, len(item))      # to flag if that changes.
                pgm_item = item['programme']
                has_keys(pgm_item, 'id', 'title', 'images', 'initial_children', 'synopses', 'status', 'count',
                         obj_name=f'watchlist.{pgm_item["title"]}')
                self.assertEqual(7, len(pgm_item))  # just to flag when more data becomes available.
                self.assertTrue(is_not_empty(pgm_item['id'], str))
                self.assertTrue(is_not_empty(pgm_item['title'], str))
                check_images(self, pgm_item['images'])
                check_synopses(self, pgm_item['synopses'])
                self.assertEqual('available', pgm_item['status'])
                self.assertGreater(pgm_item['count'], 0)
                self.assertEqual(1, len(item['programme']['initial_children']))  # Like watching, there is only one child

        def test_get_watchlist_by_ibl_api(self):
            resp = requests.get('https://user.ibl.api.bbc.co.uk/ibl/v1/user/added',
                                headers= ipwww_common.headers,
                                cookies=ipwww_common.cookie_jar,
                                allow_redirects=False
                                )
            self.assertEqual(200, resp.status_code)
            data = resp.json()
            has_keys(data, 'version', 'schema', 'added', obj_name='iblAdded')
            has_keys(data['added'], 'count', 'count_all', 'elements')
            items_list = data['added']['elements']
            for item in items_list:
                # Exactly the dame as the data on the HTML page.
                has_keys(item, 'urn', 'type', 'programme', obj_name='iblAdded.added.elements')
                self.assertTrue(is_not_empty(item['urn'], str))
                self.assertEqual('added', item['type'])
                check_large_programme_data(self, item['programme'], 'iblAdded.added.elements')
                self.assertEqual(1, len(item['programme']['initial_children']))  # Like watching, there is only one child

        def test_compare_html_and_ibl(self):
            """Somewhat surprisingly, HTML pages seem to complete much faster than API requests."""
            req_kwargs = {'headers': ipwww_common.headers,'cookies': ipwww_common.cookie_jar, 'allow_redirects':False}
            resp_html = requests.get('https://www.bbc.co.uk/iplayer/added', **req_kwargs)
            resp_ibl = requests.get('https://user.ibl.api.bbc.co.uk/ibl/v1/user/added', **req_kwargs)
            self.assertLess(resp_html.elapsed, resp_ibl.elapsed)
            self.assertAlmostEqual(resp_html.elapsed.microseconds, resp_ibl.elapsed.microseconds/2, delta=60000)

        def test_add_multiple_times(self):
            PGM_ID = 'b006ml0g'      # QI
            # Ensure it's not on the Added list.
            resp = requests.delete('https://user.ibl.api.bbc.co.uk/ibl/v1/user/adds/' + PGM_ID,
                                   cookies=ipwww_common.cookie_jar)
            # Check if add succeeds and that adding an already added item succeeds without issues.
            for i in range(10):
                resp = requests.post('https://user.ibl.api.bbc.co.uk/ibl/v1/user/adds',
                                    cookies=ipwww_common.cookie_jar,
                                    json={"id": PGM_ID})
                self.assertEqual(202, resp.status_code)
                if i == 0:
                    body = resp.content
                else:
                    self.assertEqual(body, resp.content)
                time.sleep(0.05)

        def test_add_episode_id(self):
            PGM_ID = 'b006ml0g'  # QI
            EPISODE_ID = 'm001v65j'  # QI, series U, episode 3
            # ensure QI is not on the list
            requests.delete('https://user.ibl.api.bbc.co.uk/ibl/v1/user/adds/' + PGM_ID,
                            cookies=ipwww_common.cookie_jar)
            resp = requests.post('https://user.ibl.api.bbc.co.uk/ibl/v1/user/adds',
                                 cookies=ipwww_common.cookie_jar,
                                 json={"id": EPISODE_ID})
            self.assertEqual(404, resp.status_code)
            data = resp.json()
            self.assertDictEqual(data['error'], {"details":"Not Found","http_response_code":404})

        def test_add_non_existing_programme(self):
            PGM_ID = 'zkdsfn8esdfc'  # a totally made up programme ID
            resp = requests.post('https://user.ibl.api.bbc.co.uk/ibl/v1/user/adds',
                                 cookies=ipwww_common.cookie_jar,
                                 json={"id": PGM_ID})
            self.assertEqual(404, resp.status_code)
            data = resp.json()
            self.assertDictEqual(data['error'], {"details":"Not Found","http_response_code":404})

        def test_add_to_added_not_signed_in(self):
            PGM_ID = 'b006ml0g'  # QI
            # Not signed in at all
            resp = requests.post('https://user.ibl.api.bbc.co.uk/ibl/v1/user/adds',
                                 json={"id": PGM_ID})
            self.assertEqual(401, resp.status_code)
            self.assertDictEqual(resp.json()['error'], {"details":"Missing authorization header","http_response_code":401})

            # Expired cookies
            resp = requests.post('https://user.ibl.api.bbc.co.uk/ibl/v1/user/adds',
                                 cookies=ExpiredCookieJar(),
                                 json={"id": PGM_ID})
            self.assertEqual(401, resp.status_code)
            self.assertDictEqual(resp.json()['error'],
                                 {"details": "Missing authorization header", "http_response_code": 401})
            self.assertEqual(0, len(resp.history))      # No redirects to refresh cookies.

        def test_remove_from_added_list(self):
            PGM_ID = 'b006ml0g'  # QI
            # ensure the programmes is on the list
            resp = requests.post('https://user.ibl.api.bbc.co.uk/ibl/v1/user/adds',
                                 cookies=ipwww_common.cookie_jar,
                                 json={"id": PGM_ID})
            # now remove from the list
            for i in range(2):
                resp = requests.delete('https://user.ibl.api.bbc.co.uk/ibl/v1/user/adds/' + PGM_ID,
                                    cookies=ipwww_common.cookie_jar)
                self.assertEqual(202, resp.status_code)
                self.assertEqual(resp.text, '{"id":"' + PGM_ID + '"}')

        def test_remove_from_added_not_signed_in(self):
            PGM_ID = 'b006ml0g'  # QI
            # Not signed in at all
            resp = requests.delete('https://user.ibl.api.bbc.co.uk/ibl/v1/user/adds/' + PGM_ID)
            self.assertEqual(401, resp.status_code)
            self.assertDictEqual(resp.json()['error'], {"details":"Missing authorization header","http_response_code":401})

        def test_remove_a_non_existing_programme(self):
            """Totally bogus programme IDs are accepted just as well."""
            PGM_ID = 'zldkjfghapoer9'
            resp = requests.delete('https://user.ibl.api.bbc.co.uk/ibl/v1/user/adds/' + PGM_ID,
                                cookies=ipwww_common.cookie_jar)
            self.assertEqual(202, resp.status_code)
            self.assertEqual(resp.text, '{"id":"' + PGM_ID + '"}')

        def test_added_server_side_cache(self):
            resp = requests.get('https://www.bbc.co.uk/iplayer/added',
                                headers=ipwww_common.headers,
                                cookies=ipwww_common.cookie_jar,
                                allow_redirects=False)


class Recommendations(TestCase):
    def test_get_recommendations_signed_in(self):
        resp = requests.get('https://www.bbc.co.uk/iplayer',
                            headers=ipwww_common.headers,
                            cookies=ipwww_common.cookie_jar,
                            allow_redirects=False,
                            timeout=10)
        self.assertEqual(200, resp.status_code)
        self.assertEqual('text/html; charset=utf-8', resp.headers['content-type'])
        page = resp.text
        # save_doc(page, 'html/iplayer.html')
        data = ipwww_video.ScrapeJSON(page)
        # save_json(data, 'json/iplayer.json')
        self.assertTrue('signedIn' in data['identity'])
        # find recommendations:
        bundles = [b for b in data['bundles'] if b['id'] in ('recommendations', 'if-you-liked')]
        self.assertEqual(2, len(bundles))
        for bundle in bundles:
            for item in bundle['entities']:
                check_episode_data_from_bundle(self, item['episode'], bundle['id'])


class SchedulesFromHtml(TestCase):
    def test_get_guide_unauthenticated(self):
        """Produces a schedule of BBC one of today from 05:00 AM to 05:00 AM the next day."""
        resp = requests.get('https://www.bbc.co.uk/iplayer/guide', allow_redirects=-False)
        self.assertEqual(200, resp.status_code)
        self.assertEqual('text/html; charset=utf-8', resp.headers['content-type'])
        data = ipwww_video.ScrapeJSON(resp.text)
        # save_json(data, 'json/tv-schedules-bbcone-london.json')
        schedule = data['schedule']
        has_keys(schedule, 'channelKey','title', 'bbcDate', 'ukDate', 'daysFromBBCToday', 'items' )
        self.assertEqual('bbcone', schedule['channelKey'])
        self.assertEqual('BBC One', schedule['title'])
        self.assertEqual(0, schedule['daysFromBBCToday'])
        self.assertTrue(is_not_empty(schedule['items'], list))
        items_list = schedule['items']
        for i in  range(len(items_list)):
            obj_name = 'BBCOneSchedule.item-{}.meta'.format(i)
            item = items_list[i]
            self.assertTrue(item['type'] in ('LIVE', 'AVAILABLE', 'UNAVAILABLE_FUTURE'))
            has_keys(item['meta'], 'scheduledEnd','scheduledStart', obj_name=obj_name)
            has_keys(item['props'], 'href', 'imageTemplate', 'title', 'synopsis', obj_name=obj_name)
            expect_keys(item['props'], 'subtitle', obj_name='BBCOneSchedule.item-{}.props'.format(i))  # subtitle may be absent in one-off programmes.
            if item['type'] == 'LIVE':
                has_keys(item['props'], 'progressPercent', 'label', obj_name=obj_name)
            elif item['type'] == 'AVAILABLE':
                has_keys(item['props'], 'durationSubLabel', 'secondarySubLabel', obj_name=obj_name)
                expect_keys(item['props'], 'label')

    def test_guide_other_regions(self):
        region_cookies = {
            'Wales': 'wa',
            'Scotland': 'sc',
            'Northern Ireland': 'ni',
            'Channel Islands': 'ci',
            'East': 'ea',
            'East Midlands': 'em',
            'East Yorks & Lincs': 'ey',
            'London': 'lo',
            'North East & Cumbria': 'ne',
            'North West': 'nw',
            'South': 'so',
            'South East': 'se',
            'South West': 'sw',
            'West': 'we',
            'West Midlands': 'wm',
            'Yorkshire': 'yo'
        }

    def test_guide_bbc_alba(self):
        resp = requests.get('https://www.bbc.co.uk/iplayer/guide/bbcalba', allow_redirects=-False)
        self.assertEqual(200, resp.status_code)
        self.assertEqual('text/html; charset=utf-8', resp.headers['content-type'])
        data = ipwww_video.ScrapeJSON(resp.text)
        pass


class SchedulesByIblAPi(TestCase):
    channels = ('bbc_two_england', 'bbc_two_northern_ireland_digital', 'bbc_two_wales_digital',

                'bbc_one_hd', 'bbc_one_northern_ireland', 'bbc_one_scotland', 'bbc_one_wales',
                'bbc_one_east_midlands', 'bbc_one_east_midlands', 'bbc_one_east', 'bbc_one_east_midlands',
                'bbc_one_east_yorkshire', 'bbc_one_london', 'bbc_one_north_east', 'bbc_one_north_west',
                'bbc_one_south', 'bbc_one_south_east', 'bbc_one_south_west', 'bbc_one_west',
                'bbc_one_west_midlands', 'bbc_one_yorks',

                'bbc_three', 'bbc_four', 'cbbc', 'cbeebies', 'bbc_news24',
                'bbc_parliament', 'bbc_alba', 'bbc_scotland', 's4cpbs'
                )
    def check_broadcast_item(self, bc_data):
        """Check the data structure that represents a broadcasts.

        """
        now = datetime.now(tz=timezone.utc)
        has_keys(bc_data, 'id', 'scheduled_start', 'scheduled_end', 'duration', 'blanked', 'repeat', 'episode',
                 'episode_id', 'version_id', 'service_id', 'channel_title', 'type', 'events')

        trans_start = bc_data.get('transmission_start')
        # Only items that have already started have a field transmission_start
        if trans_start:
            trans_t = datetime.strptime(trans_start,'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
            self.assertGreater(now, trans_t)

        self.assertTrue(is_iso_utc_time(bc_data['scheduled_start']))
        self.assertTrue(is_iso_utc_time(bc_data['scheduled_end']))
        has_keys(bc_data['duration'], 'text', 'value')
        self.assertEqual('broadcast', bc_data['type'])                   # Just to flag when another value comes up.
        # check_episode_data(self, bc_data['episode'], 'schedule-' + bc_data['channel_title'])
        #Episode data differs slighte from episodes in listings
        episode = bc_data['episode']
        has_keys(episode, 'id', 'live', 'type', 'title', 'images', 'signed', 'status', 'tleo_id', 'guidance',
                 'synopses', 'versions', 'childrens', 'tleo_type', 'categories', 'has_credits', 'requires_ab',
                 'master_brand', 'release_date', 'related_links', 'original_title', 'audio_described',
                 'requires_sign_in', 'release_date_time', 'lexical_sort_letter', 'requires_tv_licence')
        self.assertIsInstance(episode['categories'], list)
        self.assertIsInstance(episode['synopses'], dict)
        self.assertIsInstance(episode['images'], dict)
        self.assertTrue('standard' in episode['images'])
        self.assertTrue(is_not_empty(episode['title'], str))
        self.assertTrue(is_iso_utc_time(episode['release_date_time']))

    def test_guide_by_ibl_api(self):
        t = datetime.now(timezone.utc) - timedelta(hours=1)
        t_str = t.strftime('%Y-%m-%dT%H:%M')
        for channel in self.channels:
            url = 'https://ibl.api.bbc.co.uk/ibl/v1/channels/{}/broadcasts?per_page=8&from_date={}'.format(
                  channel, t_str)
            resp = requests.get(url, allow_redirects=False)
            self.assertEqual(200, resp.status_code)
            broadcasts_data = resp.json()
            if channel == 'bbc_one_hd':
                # save_json(broadcasts_data, 'json/ibl_schedule_bbc_one_hd.json')
                pass
            schedule = broadcasts_data['broadcasts']['elements']
            for item in schedule:
                self.check_broadcast_item(item)

    def test_get_all_available_channels(self):
        resp = requests.get('https://ibl.api.bbc.co.uk/ibl/v1/channels')
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        for chan in data:
            pass

    def test_guide_by_ibl_api_unavailable_channels(self):
        """These are all channel ID's used for live streams in the addon, but cannot be used directly to obtain schedules.
        Apart from bbc_one, all HD type of channels fail, but schedules are available as non-HD channel.
        """
        failing_channels = ('bbc_one', 'bbc_two', 'bbc_three_hd', 'bbc_four_hd', 'cbbc_hd', 'cbeebies_hd',
                            'bbc_scotland_hd', 'bbc_one_scotland_hd', 'bbc_one_northern_ireland_hd', 'bbc_one_wales_hd')

        for chan in failing_channels:
            url = ('https://ibl.api.bbc.co.uk/ibl/v1/channels/' + chan + '/broadcasts?per_page=8&from_date=' +
                   datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M'))
            resp = requests.get(url, allow_redirects=False)
            self.assertEqual(400, resp.status_code)

    def test_guide_by_ibl_api_with_end_time(self):
        """Query string argument end_date or to_date are ignored.
        The API just returns the default 20 items.
        """
        t = datetime.now(timezone.utc)
        end_t = t + timedelta(hours=4)
        url_fmt = ('https://ibl.api.bbc.co.uk/ibl/v1/channels/bbc_one_london/broadcasts?from_date=' +
               t.strftime('%Y-%m-%dT%H:%M') + '&{}=' + end_t.strftime('%Y-%m-%dT%H:%M'))
        for key in ('end_date', 'to_date'):
            url = url_fmt.format(key)
            resp = requests.get(url, allow_redirects=False)
            self.assertEqual(200, resp.status_code)
            schedule = resp.json()['broadcasts']['elements']
            self.assertEqual(20, len(schedule))     # API defaults to 20 items per page when not specified
            last_programme = datetime.strptime(schedule[-1]['scheduled_start'],'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
            self.assertGreater(last_programme, end_t)

    def test_guide_by_ibl_api_page_length(self):
        now = datetime.now(timezone.utc)
        url = ('https://ibl.api.bbc.co.uk/ibl/v1/channels/bbc_one_london/broadcasts?per_page=201&from_date=' +
               now.strftime('%Y-%m-%dT%H:%M'))
        resp = requests.get(url, allow_redirects=False)
        self.assertEqual(400, resp.status_code)
        data = resp.json()
        self.assertEqual('"per_page" must be less than or equal to 200', data['error']['details'])

    def test_guide_by_ibl_api_from_the_past(self):
        """Check from how far in the past schedule data can be obtained.

        There seems to be no limit to the allowed from_data, but the actual data returned is never more than
        8 days old.
        """
        now = datetime.now(timezone.utc)
        start_t = now - timedelta(days=14)
        url = ('https://ibl.api.bbc.co.uk/ibl/v1/channels/bbc_one_london/broadcasts?per_page=200&from_date=' +
               start_t.strftime('%Y-%m-%dT%H:%M'))
        resp = requests.get(url, allow_redirects=False)
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        schedule = data['broadcasts']['elements']
        first_programme = datetime.strptime(schedule[0]['scheduled_start'],'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
        # Check that the first programme in the list is appr. 8 days ago.
        self.assertGreaterEqual(first_programme, now - timedelta(days=8, hours=3))
        self.assertLessEqual(first_programme, now - timedelta(days=8))
        # Check there is more data than the maximum of 200 items on this page.
        self.assertGreater(data['broadcasts']['count'], 200)

    def test_guide_by_ibl_api_in_the_future(self):
        """Check from how far in the future schedule data can be obtained.

        There seems to be no limit to the allowed from_data, but the actual data returned is never more than
        8 days old.
        """
        now = datetime.now(timezone.utc)
        start_t = now + timedelta(days=8)
        url = ('https://ibl.api.bbc.co.uk/ibl/v1/channels/bbc_one_london/broadcasts?per_page=200&from_date=' +
               start_t.strftime('%Y-%m-%dT%H:%M'))
        resp = requests.get(url, allow_redirects=False)
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        schedule = data['broadcasts']['elements']
        first_programme = datetime.strptime(schedule[0]['scheduled_start'],'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
        # Check that the start of the first programme in the list is just before from_date.
        self.assertLessEqual(first_programme, start_t)
        self.assertGreater(first_programme, start_t - timedelta(hours=3))
        # Check that the last programme is roughly 10 days from now.
        last_programme = datetime.strptime(schedule[-1]['scheduled_start'],'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
        self.assertLessEqual(last_programme, now + timedelta(days=10))
        self.assertGreater(last_programme, now + timedelta(days=9))
        # Check there is no more data than the maximum of 200 items on this page.
        self.assertLess(data['broadcasts']['count'], 200)

    def test_guide_by_ibl_api_pages(self):
        """Test obtaining consecutive pages by defining page in the querystring"""
        now = datetime.now(timezone.utc)
        start_t = now - timedelta(days=8)
        last_programme_start = start_t
        pagenr = 0
        while True:
            pagenr += 1
            url = ''.join((
                    'https://ibl.api.bbc.co.uk/ibl/v1/channels/bbc_one_london/broadcasts?per_page=200&page=',
                    str(pagenr),
                    '&from_date=',
                    start_t.strftime('%Y-%m-%dT%H:%M')
            ))
            resp = requests.get(url, allow_redirects=False)
            self.assertEqual(200, resp.status_code)
            data = resp.json()
            self.assertEqual(pagenr, data['broadcasts']['page'])
            schedule = data['broadcasts']['elements']
            first_programme_end = datetime.strptime(schedule[0]['scheduled_end'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(
                tzinfo=timezone.utc)
            self.assertGreater(first_programme_end, last_programme_start)
            last_programme_start = datetime.strptime(schedule[-1]['scheduled_end'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(
                tzinfo=timezone.utc)
            total_num_programmes = data['broadcasts']['count']
            if pagenr >= math.ceil(total_num_programmes / 200):
                return



class SchedulesByEssApi(TestCase):
    def check_ess_programme(self, sc_data, channel_id):
        has_keys(sc_data, 'id', 'service', 'version', 'episode', 'brand', 'masterbrand', 'published_time')
        self.assertEqual(sc_data['service']['id'], channel_id)
        self.assertTrue(is_not_empty(sc_data['episode']['title'], str))
        if sc_data['brand']:
            self.assertTrue(is_not_empty(sc_data['brand']['title'], str))
        self.assertTrue(is_iso_utc_time(sc_data['published_time']['start']))
        self.assertTrue(is_iso_utc_time(sc_data['published_time']['end']))

    def test_available_channels(self):
        channels = ('bbc_two_england', 'bbc_two_scotland',
                    'bbc_two_northern_ireland_digital', 'bbc_two_wales_digital',

                    'bbc_one_hd', 'bbc_one_northern_ireland', 'bbc_one_scotland', 'bbc_one_wales',
                    'bbc_one_east_yorkshire', 'bbc_one_london', 'bbc_one_north_east', 'bbc_one_south_east',
                    'bbc_one_south_west', 'bbc_one_west', 'bbc_one_yorks',
                    'bbc_one_east_midlands', 'bbc_one_east_midlands', 'bbc_one_east', 'bbc_one_east_midlands',
                    'bbc_one_north_west', 'bbc_one_south', 'bbc_one_west_midlands',

                    'bbc_three_hd', 'bbc_four_hd', 'cbbc_hd', 'cbeebies_hd', 'bbc_news24', 'bbc_parliament',
                    'bbc_alba', 'bbc_scotland_hd', 's4cpbs')
        # channels = ('bbc_one_hd',)
        for chan in channels:
            url = 'https://ess.api.bbci.co.uk/schedules?serviceId=' + chan
            resp = requests.get(url, allow_redirects=False)
            self.assertEqual(200, resp.status_code)
            data = resp.json()
            for item in data['items']:
                self.check_ess_programme(item, chan)

        # for chan in fails:
        #     url = 'https://ess.api.bbci.co.uk/schedules?serviceId=' + chan
        #     resp = requests.get(url, allow_redirects=False)
        #     self.assertEqual(404, resp.status_code)

    def test_get_all_channels_in_one_go(self):
        """Cannot get all channels in one go
        Filter by querystring seems to be a requirement

        """
        url = 'https://ess.api.bbci.co.uk/schedules'
        resp = requests.get(url, allow_redirects=False)
        self.assertEqual(404, resp.status_code)


@skip("Run only when the live event is being broadcast and url's are properly set.")
class LiveListItem(TestCase):
    """Test items representing a live broadcast in normal listings, like categories, etc.

    These test are all specific to a particular event and are only to be run when the
    event has actual live broadcasts. URL's most like need to be adjusted for each live
    broadcast.

    """
    def _check_gen_live_version(self, version_data):
        """Check version data of a live item.
        Is quite different to version data in catchup items.

        """
        has_keys(version_data, 'id', 'kind', 'hd', 'guidance', 'rrc', 'events', 'duration', 'startTime', 'endTime',
                 'isoStartTime', 'isoEndTime')
        self.assertTrue(version_data['kind'] in ('simulcast', 'webcast'))
        self.assertTrue(is_iso_utc_time(version_data['isoStartTime']))
        self.assertTrue(is_iso_utc_time(version_data['isoEndTime']))
        self.assertTrue(is_not_empty(version_data['startTime'], int))
        self.assertTrue(is_not_empty(version_data['endTime'], int))
        if version_data['kind'] == 'simulcast':
            self.assertTrue(is_not_empty(version_data['serviceId'], str))
            self.assertTrue(is_not_empty(version_data['regionalServices'], dict))
        else:
            self.assertFalse('serviceId' in version_data)

    def test_snooker_uk_championships_listing(self):
        # A page with several types of live items.
        url = 'https://www.bbc.co.uk/iplayer/episodes/b00g92ch/snooker-uk-championship?seriesId=b00g92ch-live-now'
        resp = requests.get(url, allow_redirects=False)
        self.assertEqual(200, resp.status_code)
        # save_doc(resp.text, 'html/snooker_uk_listing_with_live.html')
        data = ipwww_video.ScrapeJSON(resp.text)
        self._check_gen_live_version(data['version'][0])

    def test_red_button_episode(self):
        """A page item representing a red-button live stream"""
        url = 'https://www.bbc.co.uk/iplayer/episode/m0025kpd/snooker-uk-championship-2024-live-day-5-part-1'
        resp = requests.get(url, allow_redirects=False)
        self.assertEqual(200, resp.status_code)
        # save_doc(resp.text, 'html/snooker_uk_rb_item.html')
        data = ipwww_video.ScrapeJSON(resp.text)
        version = data['versions'][0]
        self.assertEqual('simulcast', version['kind'])
        self._check_gen_live_version(version)

    def test_main_live_episode(self):
        """A page item representing a stream on one of BBC's main channels"""
        url = 'https://www.bbc.co.uk/iplayer/episode/m0025f6k/snooker-uk-championship-2024-day-5-afternoon'
        resp = requests.get(url, allow_redirects=False)
        self.assertEqual(200, resp.status_code)
        # save_doc(resp.text, 'html/snooker_uk_live_item.html')
        data = ipwww_video.ScrapeJSON(resp.text)
        version = data['versions'][0]
        self.assertEqual('simulcast', version['kind'])
        self._check_gen_live_version(version)

    def test_sportstream_episode(self):
        """A page item representing a 'sport stream', i.e. a stream only available on iplayer."""
        url = 'https://www.bbc.co.uk/iplayer/episode/l0056v5y/snooker-uk-championship-2024-live-shaun-murphy-v-ding-junhui-table-one'
        resp = requests.get(url, allow_redirects=False)
        self.assertEqual(200, resp.status_code)
        # save_doc(resp.text, 'html/snooker_uk_sportstream_item.html')
        data = ipwww_video.ScrapeJSON(resp.text)
        version = data['versions'][0]
        self.assertEqual('webcast', version['kind'])
        self._check_gen_live_version(version)