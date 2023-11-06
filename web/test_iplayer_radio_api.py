import json

from support import fixtures
fixtures.global_setup()

import re
import requests
from http import cookiejar

from unittest import TestCase
from resources.lib import ipwww_common
from resources.lib import ipwww_video
from tests.support.testutils import save_json, save_doc, doc_path


setUpModule = fixtures.setup_web_test()


def scrape_sound_data(html):
    match = re.search(r'<script> window.__PRELOADED_STATE__ = (.*?);\s*</script>', html, re.DOTALL)
    if not match:
        return
    data = json.loads(match[1])
    return data


class TestLive(TestCase):
    def test_bbc_one_web_page(self):
        resp = requests.get('https://www.bbc.co.uk/sounds/play/live:bbc_radio_one', allow_redirects=False)
        self.assertEqual(200, resp.status_code)
        data  = scrape_sound_data(resp.text)
        # save_json(data, 'json/sounds-live_radio1.json')
        # save_doc(resp.text, 'html/sounds-live_radio1.html')
        pass

    def test_bbc_one_web_page_authenticated(self):
        resp = requests.get('https://www.bbc.co.uk/sounds/play/live:bbc_radio_one',
                            headers=ipwww_common.headers,
                            cookies=ipwww_common.cookie_jar,
                            allow_redirects=True)
        self.assertEqual(200, resp.status_code)
        data  = scrape_sound_data(resp.text)
        # save_json(data, 'json/sounds-live_radio1_authenticated.json')
        # save_doc(resp.text, 'html/sounds-live_radio1_authenticated.html')
        pass

    def test_media_selector_live_not_authenticated(self):
        """Request media selector with no authentication whatsoever."""
        resp = requests.get('https://open.live.bbc.co.uk/mediaselector/6/select/version/2.0/mediaset/pc/vpid/bbc_radio_one/format/json/jsfunc/JS_callbacks0')
        self.assertEqual(200, resp.status_code)
        content = resp.text
        self.assertFalse(content.startswith('/**/ JS_callbacks0({"media":'))
        self.assertFalse('bitrate' in content)
        self.assertTrue('result":"selectionunavailable' in content)

    def _get_radio_one_data(self):
        # Get data from the radio one website
        resp = requests.get('https://www.bbc.co.uk/sounds/play/live:bbc_radio_one',
                            headers=ipwww_common.headers,
                            cookies=ipwww_common.cookie_jar)
        data = scrape_sound_data(resp.text)
        self.assertTrue(data['userSettings']['isSignedIn'])  # No JWT token when not signed in
        return data

    def test_media_selector_live_authenticated(self):
        data = self._get_radio_one_data()
        # Request media selector with JWT from data
        resp = requests.get('https://open.live.bbc.co.uk/mediaselector/6/select/version/2.0/mediaset/pc/vpid/bbc_radio_one/format/json/jsfunc/JS_callbacks0',
                            headers=ipwww_common.headers,
                            cookies=ipwww_common.cookie_jar,
                            params={'jwt_auth': data['smp']['liveStreamJwt']})
        self.assertEqual(200, resp.status_code)
        content = resp.text
        self.assertTrue(content.startswith('/**/ JS_callbacks0({"media":'))
        self.assertTrue('bitrate' in content)
        self.assertFalse('result":"selectionunavailable' in content)

    def test_media_selector_live_authenticated_without_jwt(self):
        """Check if passing JWT token in the querystring is required if we do a
        request with all authentication cookies.

        """
        # Assert we are signed in
        self._get_radio_one_data()

        # Request media selector WITH all auth cookies, but WITHOUT JWT.
        resp = requests.get('https://open.live.bbc.co.uk/mediaselector/6/select/version/2.0/mediaset/pc/vpid/bbc_radio_one/format/json/jsfunc/JS_callbacks0',
                            cookies=ipwww_common.cookie_jar)
        self.assertEqual(200, resp.status_code)
        content = resp.text
        self.assertFalse(content.startswith('/**/ JS_callbacks0({"media":'))
        self.assertFalse('bitrate' in content)
        self.assertTrue('result":"selectionunavailable' in content)

    def test_media_selector_live_not_authenticated_with_jwt(self):
        """Check if passing auth cookies is required when JWT token is present in the querystring.

        """
        data = self._get_radio_one_data()

        # Request media selector WITHOUT auth cookies, but WITH JWT.
        resp = requests.get('https://open.live.bbc.co.uk/mediaselector/6/select/version/2.0/mediaset/pc/vpid/bbc_radio_one/format/json/jsfunc/JS_callbacks0',
                            params={'jwt_auth': data['smp']['liveStreamJwt']})
        self.assertEqual(200, resp.status_code)
        content = resp.text
        self.assertTrue(content.startswith('/**/ JS_callbacks0({"media":'))
        self.assertTrue('bitrate' in content)
        self.assertFalse('result":"selectionunavailable' in content)


class TestListening(TestCase):
    def test_old_listening_list_page_logged_in(self):
        resp = requests.get(url="http://www.bbc.co.uk/radio/favourites",
                            headers=ipwww_common.headers,
                            cookies=ipwww_common.cookie_jar,
                            allow_redirects=False)
        self.assertTrue(resp.is_permanent_redirect)
        self.assertEqual('https://www.bbc.co.uk/radio/favourites', resp.headers['location'])
        resp = requests.get(url="https://www.bbc.co.uk/radio/favourites",
                            headers=ipwww_common.headers,
                            cookies=ipwww_common.cookie_jar,
                            allow_redirects=False)
        self.assertTrue(resp.is_permanent_redirect)
        self.assertEqual('https://www.bbc.co.uk/sounds/favourites', resp.headers['location'])


    def test_get_listening_list_page_logged_in(self):
        resp = requests.get(url="https://www.bbc.co.uk/sounds/favourites",
                            headers=ipwww_common.headers,
                            cookies=ipwww_common.cookie_jar,
                            allow_redirects=False)
        self.assertEqual(404, resp.status_code)

    def test_get_following_page_logged_in(self):
        """currently not used in the add-on"""
        resp = requests.get(url="https://www.bbc.co.uk/radio/favourites/programmes",
                            headers=ipwww_common.headers,
                            cookies=ipwww_common.cookie_jar,
                            allow_redirects=False)
        self.assertEqual(404, resp.status_code)


class TestBookmarks(TestCase):
    def test_get_bookmarks_signed_in(self):
        resp = requests.get('https://www.bbc.co.uk/sounds/my/bookmarks', cookies=ipwww_common.cookie_jar, allow_redirects=False)
        self.assertEqual(200, resp.status_code)
        # save_doc(resp.text, 'html/sounds-bookmarks.html')
        data = scrape_sound_data(resp.text)
        pass


class TestCategories(TestCase):
    def test_categories_data(self):
        resp = requests.get('https://www.bbc.co.uk/sounds/categories', allow_redirects=False)
        self.assertFalse(resp.is_redirect)
        self.assertTrue(resp.headers['content-type'].startswith('text/html'))
        # save_doc(resp.text, 'html/radio-categories.html')
        data = scrape_sound_data(resp.text)
        pass
