from tests.support import fixtures
fixtures.global_setup()

from unittest import TestCase
from unittest.mock import patch, MagicMock
from http import cookiejar

import requests

from resources.lib import ipwww_common
from resources.lib import ipwww_video
from tests.support.testutils import save_json, doc_path


setUp = fixtures.setup_web_test()


class TestSignInBBCiD(TestCase):
    def test_signin_while_not_signed_in(self):
        jar = cookiejar.LWPCookieJar()
        result = ipwww_common.SignInBBCiD(jar)
        self.assertTrue(result)

    def test_sign_in_while_already_signed_in(self):
        result = ipwww_common.SignInBBCiD()
        self.assertTrue(result)

    def test_sign_in_with_expired_tokens(self):
        jar = cookiejar.LWPCookieJar(doc_path('cookies/expired.cookies'))
        jar.load()
        # jar.save = MagicMock()
        result = ipwww_common.SignInBBCiD(jar)
        self.assertTrue(result)


class TestStatusBBCiD(TestCase):
    def test_status_while_signed_in(self):
        res = ipwww_common.StatusBBCiD()
        self.assertTrue(res)

    def test_status_while_not_signed_in(self):
        jar = cookiejar.LWPCookieJar()
        res = ipwww_common.StatusBBCiD(jar)
        self.assertFalse(res)

    def test_status_with_expired_tokens(self):
        jar = cookiejar.LWPCookieJar(doc_path('cookies/expired.cookies'))
        jar.load()
        jar.save = MagicMock()
        res = ipwww_common.StatusBBCiD(jar)
        self.assertFalse(res)


class TestOpenUrl(TestCase):
    @patch('resources.lib.ipwww_common.cookie_jar', new=cookiejar.LWPCookieJar())
    def test_open_generic_page_without_credential(self,):
        """A page not requiring login"""
        result = ipwww_common.OpenURL('https://www.bbc.co.uk/iplayer/group/most-popular')
        data = ipwww_video.ScrapeJSON(result)
        self.assertFalse(data['id']['signedIn'])

    def test_open_generic_page_with_credential(self, ):
        """A page not requiring login, but valid credentials provided"""
        result = ipwww_common.OpenURL('https://www.bbc.co.uk/iplayer/most-popular')
        data = ipwww_video.ScrapeJSON(result)
        self.assertTrue(data['id']['signedIn'])

    def test_open_generic_page_with_expired_credential(self):
        """A page not requiring login"""
        jar = cookiejar.LWPCookieJar(doc_path('cookies/expired.cookies'))
        jar.load()
        jar.save = MagicMock()
        with patch('resources.lib.ipwww_common.cookie_jar', new=jar):
            result = ipwww_common.OpenURL('https://www.bbc.co.uk/iplayer/most-popular')
            data = ipwww_video.ScrapeJSON(result)
            self.assertTrue(data['id']['signedIn'])
            jar.save.assert_called_once()
            self.assertTrue(any(c.name=='ckns_atkn' for c in jar))

    @patch('resources.lib.ipwww_common.cookie_jar', new=cookiejar.LWPCookieJar())
    def test_open_authenticated_page_without_credential(self,):
        """A page requiring login"""
        result = ipwww_common.OpenURL('https://www.bbc.co.uk/iplayer/watching')
        data = ipwww_video.ScrapeJSON(result)
        self.assertFalse(data['id']['signedIn'])

    def test_open_authenticated_page_with_credential(self, ):
        """A page requiring login, but valid credentials provided"""
        result = ipwww_common.OpenURL('https://www.bbc.co.uk/iplayer/watching')
        data = ipwww_video.ScrapeJSON(result)
        self.assertTrue(data['id']['signedIn'])

    def test_open_authenticated_page_with_expired_credential(self):
        """A page requiring login, but access token cookie has expired"""
        jar = cookiejar.LWPCookieJar(doc_path('cookies/expired.cookies'))
        jar.load()
        jar.save = MagicMock()
        with patch('resources.lib.ipwww_common.cookie_jar', new=jar):
            result = ipwww_common.OpenURL('https://www.bbc.co.uk/iplayer/watching')
            data = ipwww_video.ScrapeJSON(result)
            self.assertTrue(data['id']['signedIn'])
            jar.save.assert_called_once()
            self.assertTrue(any(c.name=='ckns_atkn' for c in jar))
