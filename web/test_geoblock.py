from tests.support import fixtures
fixtures.global_setup()

import json
import requests
import unittest
from unittest.mock import patch

from support import testutils

from resources.lib import ipwww_video
from resources.lib import ipwww_common

# raise unittest.SkipTest("Only to be run when located outside of the UK")


class BasicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.headers = {}

    def test_iplayer_main_page(self):
        resp = requests.get('https://www.bbc.co.uk/iplayer', headers=self.headers)
        self.assertEqual(200, resp.status_code)

    def test_media_selector_live(self):
        resp = requests.get('https://open.live.bbc.co.uk/mediaselector/6/select/version/2.0/mediaset/pc/vpid/bbc_one_hd/format/json/cors/1', headers=self.headers)
        self.assertEqual(403, resp.status_code)

    def test_media_selector_catchup(self):
        # ipwww_video.AddAvailableStreamItem('2p4children', 'https://www.bbc.co.uk/iplayer/episode/p0blpxhs', '', '')
        media_selector_url = 'https://open.live.bbc.co.uk/mediaselector/6/select/version/2.0/mediaset/pc/vpid/p0blpyh3/format/json/cors/1'
        resp = requests.get(media_selector_url, headers=self.headers)
        self.assertEqual(404, resp.status_code)
        resp_data = json.loads(resp.content)
        self.assertEqual('selectionunavailable', resp_data['result'])


class TestsAsFireFox(BasicTests):
    @classmethod
    def setUpClass(cls):
        cls.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0'}



class TestGeoBlockedStreamSelector(unittest.TestCase):
    @patch('resources.lib.ipwww_common.OpenRequest',
           side_effect=ipwww_common.GeoBlockedError(testutils.HttpResponse(403)))
    def test_http_err_403(self,_):
        with self.assertRaises(ipwww_common.GeoBlockedError) as cm:
            ipwww_video.PlayStream('some episode', 'some url', 'image url')
        exc = cm.exception
        print(exc)
        pass