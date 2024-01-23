from tests.support import fixtures
fixtures.global_setup()

import time
import string
import requests
from http import cookiejar

from unittest import TestCase
from resources.lib import ipwww_common
from resources.lib import ipwww_video
from tests.support.testutils import save_json, save_doc, doc_path, ExpiredCookieJar
from tests.support.object_checks import (has_keys, expect_keys, is_not_empty, is_url, is_iso_utc_time,
                                         iso_duration_2_seconds)

setUpModule = fixtures.setup_web_test()


def check_page_has_json_data(testcase, url):
    resp = requests.get(url, headers=ipwww_common.headers, allow_redirects=False)
    testcase.assertTrue(200, resp.status_code)
    testcase.assertTrue(resp.headers['content-type'].startswith('text/html'))
    data = ipwww_video.ScrapeJSON(resp.text)
    testcase.assertIsInstance(data, dict)
    return data


def check_synopses(testcase, synopses):
    testcase.assertIsInstance(synopses, dict)
    testcase.assertTrue(any(key in synopses.keys() for key in ('large', 'small', 'medium', 'editorial')))


def check_programme_data(testcase, programme, parent_name):
    obj_name = '.'.join((parent_name, programme['title']))
    has_keys(programme, 'id', 'title', 'type', 'images', 'synopses', 'programme_type', 'count',
             'initial_children', obj_name=obj_name)

    expect_keys(programme, 'labels', 'tleo_type', 'categories', 'master_brand', 'lexical_sort_letter',
                'status', obj_name=obj_name)

    testcase.assertTrue(is_not_empty(programme['id'], str))
    testcase.assertEqual('programme', programme['type'])
    testcase.assertTrue(programme['tleo_type'] in ('episode', 'brand', 'series'))    # just to flag when other values appear.
    testcase.assertTrue(is_not_empty(programme['title'], str))
    testcase.assertIsInstance(programme['images'], dict)
    testcase.assertTrue(is_url(programme['images']['standard'], ('.jpg', '.png')))
    check_synopses(testcase, programme['synopses'])
    testcase.assertTrue(programme['programme_type'] in ('one-off', 'self-contained', 'narrative', 'sequential', 'unclassified', 'strand'))  # just to flag when other values appear.
    testcase.assertTrue(is_not_empty(programme['count'], int))
    testcase.assertIsInstance(programme['initial_children'], list)
    for child in programme['initial_children']:
        check_episode_data(testcase, child, '.'.join((obj_name, 'children')))


def check_version_data(testcase, version, parent_name=''):
    obj_name = '.'.join((parent_name, 'version'))
    has_keys(version, 'id', 'kind', 'duration', 'availability', 'first_broadcast_date_time', obj_name=obj_name)

    expect_keys(version, 'hd', 'uhd', 'type', 'events', 'download', 'first_broadcast', obj_name=obj_name)

    testcase.assertTrue(version['kind'] in ('original', 'audio-described', 'signed', 'technical-replacement', 'editorial', 'pre-watershed'))
    testcase.assertEqual('version', version['type'])
    testcase.assertIsInstance(version['duration'], dict)
    testcase.assertTrue(is_not_empty(version['duration']['text'], str))
    testcase.assertGreater(iso_duration_2_seconds(version['duration']['value']), 39)   # Allow for short news clips
    testcase.assertTrue(is_not_empty(version['availability']['remaining']['text'], str))
    testcase.assertTrue(is_iso_utc_time(version['first_broadcast_date_time']))


def check_episode_data(testcase, episode, parent_name=''):
    obj_name = '.'.join((parent_name, episode['title']))
    has_keys(episode, 'title', 'images', 'tleo_id', 'synopses', 'original_title', 'programme_type', obj_name=obj_name)

    expect_keys(episode, 'id', 'live', 'type', 'labels', 'signed', 'status', 'guidance', 'versions', 'childrens',       # childrens is not a typo (at least not mine)
                'tleo_type', 'categories', 'has_credits', 'requires_ab', 'master_brand', 'release_date',
                'audio_described', 'requires_sign_in', 'release_date_time', 'editorial_subtitle', 'lexical_sort_letter',
                'requires_tv_licence', obj_name=obj_name)

    testcase.assertEqual('episode', episode['type'])    # even films and documentaries appear to be of the episode.
    testcase.assertTrue(episode['tleo_type'] in ('episode', 'brand', 'series'))   # just to flag when other values appear.
    testcase.assertIsInstance(episode['images'], dict)
    testcase.assertTrue(is_url(episode['images']['standard'], ('.jpg', '.png')))
    testcase.assertIsInstance(episode['signed'], bool)
    testcase.assertIsInstance(episode['audio_described'], bool)
    testcase.assertTrue(is_not_empty(episode['tleo_id'], str))  # not always the same is 'id'.
    check_synopses(testcase, episode['synopses'])
    testcase.assertTrue(is_not_empty(episode['release_date'], str))     # format varies from '2007' to '21 May 2018'
    testcase.assertTrue(is_iso_utc_time(episode['release_date_time']))
    for version in episode['versions']:
        check_version_data(testcase, version, obj_name)


class ChannelsAtoZ(TestCase):
    channels = ('bbcone', 'bbctwo', 'tv/bbcthree', 'tv/cbbc', 'tv/cbeebies', 'tv/bbcnews', 'tv/bbcparliament',
                'tv/bbcalba', 'tv/bbcscotland', 'tv/s4c')

    def test_channel_az_page(self):
        for chan in self.channels:
            check_page_has_json_data(self, 'https://www.bbc.co.uk/{}/a-z'.format(chan))


class CategoriesAtoZ(TestCase):
    categories = ('bbcone', 'bbctwo', 'tv/bbcthree', 'tv/cbbc', 'tv/cbeebies', 'tv/bbcnews', 'tv/bbcparliament',
                'tv/bbcalba', 'tv/bbcscotland', 'tv/s4c')

    def test_channel_az_page(self):
        for chan in self.categories:
            check_page_has_json_data(self, 'https://www.bbc.co.uk/{}/a-z'.format(chan))


class ProgrammesAtoZ(TestCase):
    letters = list(string.ascii_lowercase.replace('x','')) + ['0-9']

    def test_a_to_z_pages(self):
        for letter in self.letters:
            page_data = check_page_has_json_data(self, 'https://www.bbc.co.uk/iplayer/a-z/' + letter)
            # save_json(page_data, f'json/programmes_az/{letter}.json')


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
        search_term = 'paradise'
        url = 'https://www.bbc.co.uk/iplayer/search?q=' + search_term
        data = check_page_has_json_data(self, url)
        ipwww_video.ParseJSON(data, url)


class Watching(TestCase):
    def test_get_watching_data(self):
        resp = requests.get(url = "https://www.bbc.co.uk/iplayer/watching",
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
            has_keys(item, 'type', 'urn', 'status', 'episode', 'programme', 'has_next', 'version', obj_name='Watching')
            self.assertTrue(item['status'] in ('current', 'next'))
            if item['status'] == 'current':
                has_keys(item, 'offset', 'remaining', 'progress', obj_name='Watching')

            # This is the data of the episode (Next, or Watching)
            check_episode_data(self, item['episode'], 'Watching.episode')
            check_version_data(self, item['version'], 'Watching.version')

            programme = item['programme']
            check_programme_data(self, programme, 'Watching.programme')
            if programme['programme_type'] == 'one-off':
                self.assertEqual(programme['count'], 1)
            else:
                self.assertGreater(programme['count'], 1)
            # Just a quick check on consistency
            # Children of programme are not used by the parser for Watching; it's not always the same as field
            # episode and episode contains the data needed for Watching.
            self.assertEqual(1, len(programme['initial_children']))

    def test_get_watching_without_signed_in(self):
        """This just return a normal HTML page with a button to sign in or register."""
        page_url = "https://www.bbc.co.uk/iplayer/watching"
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

            resp = session.get(url="https://www.bbc.co.uk/iplayer/watching", allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            new_url = resp.headers['location']
            self.assertTrue(new_url.startswith('https://session.bbc.co.uk/session?'))

            resp = session.get(new_url, allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            self.assertTrue('ckns_id' in resp.cookies)
            self.assertTrue('ckns_atkn' in resp.cookies)
            self.assertTrue('ckns_idtkn' in resp.cookies)
            new_url = resp.headers['location']
            self.assertTrue(new_url.startswith('https://www.bbc.co.uk/iplayer/watching'))

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


class TestAdded(TestCase):
        """User's own favourites"""
        def test_get_added_signed_in(self):
            resp = requests.get('https://www.bbc.co.uk/iplayer/added',
                                headers=ipwww_common.headers,
                                cookies=ipwww_common.cookie_jar,
                                allow_redirects=False)
            self.assertEqual(200, resp.status_code)
            self.assertEqual('text/html; charset=utf-8', resp.headers['content-type'])
            page = resp.text
            data = ipwww_video.ScrapeJSON(page)
            # save_json(data, 'html/added.json')
            self.assertTrue(data['id']['signedIn'])
            items_list = data['items']['elements']
            for item in items_list:
                has_keys(item, 'urn', 'type', 'programme', obj_name='Added.items')
                self.assertTrue(is_not_empty(item['urn'], str))
                self.assertEqual('added', item['type'])
                check_programme_data(self, item['programme'], 'Added.items')
                self.assertEqual(1, len(item['programme']['initial_children']))  # Like watching, there is only one child

        def test_get_added_by_ibl_api(self):
            resp = requests.get('https://user.ibl.api.bbc.co.uk/ibl/v1/user/added',
                                headers= ipwww_common.headers,
                                cookies=ipwww_common.cookie_jar,
                                allow_redirects=False)
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
                check_programme_data(self, item['programme'], 'iblAdded.added.elements')
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
            for i in range(50):
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