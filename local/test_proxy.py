from support import fixtures
fixtures.global_setup()

from unittest import TestCase
from unittest.mock import patch, MagicMock, call

import xbmcplugin

from resources.lib import proxy

from support.testutils import open_json, open_doc


setUp = fixtures.setup_local_tests()



class ManifestModification(TestCase):
    def test_modify_base_url(self):
        orig_mpd = open_doc('manifest/manifest_live_from_listing.mpd')().encode('utf-8')
        new_mpd = proxy.modify_manifest(orig_mpd, 'https://my.server.url', 18645).decode('utf-8')
        pass


class ReadInit(TestCase):
    def test_read_caption_init(self):
        data = proxy.read_caption_init()
        self.assertIsInstance(data, bytes)
        self.assertGreater(len(data), 600)