from support import fixtures
fixtures.global_setup()

from support.testutils import open_json, open_doc
from support.object_checks import is_not_empty, is_url

from unittest import TestCase
from unittest.mock import patch, MagicMock, call

from resources.lib import ipwww_iptv


setUp = fixtures.setup_local_tests()


@patch('resources.lib.ipwww_iptv.ADDON.getSetting', lambda x: 'bbc_one_london' if x == 'iptv.tv-channels' else '')
class TestTvEpg(TestCase):
    @patch('resources.lib.ipwww_video.OpenRequest', return_value=open_doc('json/ibl_schedule_bbc_one_hd.json')())
    def test_get_epg_default_channels(self, _):
        epg = ipwww_iptv.get_tv_epg()
    @patch('resources.lib.ipwww_iptv.OpenRequest', open_doc('json/ibl_schedule_bbc_one_hd.json'))
    def test_get_epg_default_channels(self):
        self.assertIsInstance(epg, dict)
        self.assertEqual(1, epg['version'])
        self.assertIsInstance(epg['epg'], dict)
        for chan, schedule in epg['epg'].items():
            self.assertIsInstance(schedule, list)
            for item in schedule:
                self.assertIsInstance(item, dict)
                if item['image']:
                    self.assertTrue(is_url(item['image']))
                    self.assertFalse('recipe' in item['image'])