from tests.support import fixtures
fixtures.global_setup()

import requests
import unittest
from unittest.mock import patch
from http import cookiejar

from resources.lib import ipwww_radio
from resources.lib import ipwww_video


setUp = fixtures.setup_web_test()



@patch('resources.lib.ipwww_common.AddMenuEntry')
class GenericListings(unittest.TestCase):
    def test_list_listen_list(self, patched_add):
        ipwww_radio.ListListenList(True)
        patched_add.assert_called()
