import json

from tests.support import fixtures
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