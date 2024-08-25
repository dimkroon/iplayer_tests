from support import fixtures
fixtures.global_setup()

from unittest import TestCase
from unittest.mock import patch, MagicMock

from requests import HTTPError, ConnectionError

from support.testutils import HttpResponse
from resources.lib import ipwww_common


class OpenRequest(TestCase):
    @patch('requests.Session.request',
           side_effect=HTTPError("Not Found", response=HttpResponse(404, content=b"response content")))
    def test_open_with_http_error(self, _):
        with self.assertRaises(ipwww_common.WebRequestError) as raised:
            ipwww_common.OpenRequest('get', 'myurl')
        err = raised.exception
        self.assertEqual("Not Found", str(err))
        self.assertEqual(404, err.status_code)
        self.assertEqual(b'response content', err.content)

    @patch('requests.Session.request', side_effect=ConnectionError("No connection"))
    def test_open_with_other_error(self, _):
        self.assertRaises(ConnectionError, ipwww_common.OpenRequest, 'get', 'myurl')
