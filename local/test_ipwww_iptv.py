from support import fixtures
fixtures.global_setup()

from support.testutils import open_json, open_doc
from support.object_checks import is_not_empty, is_url

from unittest import TestCase
from unittest.mock import patch, MagicMock, call

from resources.lib import ipwww_iptv


setUp = fixtures.setup_local_tests()


class TestEpg(TestCase):
    def check_schedule_item(self, item):
        self.assertTrue(is_not_empty(item['start'], str))
        self.assertTrue(is_not_empty(item['stop'], str))
        self.assertTrue(is_not_empty(item['title'], str))
        self.assertTrue(is_not_empty(item['description'], str))
        for key in ('subtitle', 'image', 'date', 'stream'):
            if item.get('key') is not None:
                self.assertTrue(is_not_empty(item[key], str))
        if item['image']:
            self.assertFalse('recipe' in item['image'])


    @patch('resources.lib.ipwww_iptv.ADDON.getSetting', lambda x: 'bbc_one_london' if x == 'iptv.tv-channels' else '')
    @patch('resources.lib.ipwww_iptv.OpenRequest', open_doc('json/ibl_schedule_bbc_one_hd.json'))
    def test_tv_epg_(self):
        epg = ipwww_iptv.tv_epg()
        self.assertIsInstance(epg, dict)
        for chan, schedule in epg.items():
            self.assertIsInstance(schedule, list)
            for item in schedule:
                self.assertIsInstance(item, dict)
                if item['image']:
                    self.assertTrue(is_url(item['image']))
                    self.assertFalse('recipe' in item['image'])
