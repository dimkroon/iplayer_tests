from tests.support import fixtures
fixtures.global_setup()

from unittest import TestCase

import requests

from resources.lib import ipwww_video, ipwww_common
from tests.support.testutils import save_json

setUpModule = fixtures.setup_web_test()


class Watching(TestCase):
    def test_get_watching_data(self):
        page = ipwww_common.OpenURL(url = "https://www.bbc.co.uk/iplayer/watching")
        data = ipwww_video.ScrapeJSON(page)
        # save_json(data, 'html/watching.json')

    def test_watching_plain(self):
        r = ipwww_video.ListWatching(True)
