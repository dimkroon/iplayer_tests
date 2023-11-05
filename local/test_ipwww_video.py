from support import fixtures
fixtures.global_setup()

from unittest import TestCase
from unittest.mock import patch, MagicMock

from resources.lib import ipwww_video

setUp = fixtures.setup_local_tests()


class TestGetItemSynopsis(TestCase):
    synopses = {'editorial': 'editorial plot',
                'large': 'large plot',
                'medium': 'medium plot',
                'small': 'small plot'}

    def test_get_synposis_as_string(self):
        item_d = {'synopsis': 'my plot', 'synopses': self.synopses}
        self.assertEqual('my plot', ipwww_video.GetItemSynopsis(item_d))
        item_d = {'synopsis': None, 'synopses': self.synopses}
        self.assertEqual('editorial plot', ipwww_video.GetItemSynopsis(item_d))

    def test_get_synoposis_as_dict(self):
        item_d = {'synopsis': self.synopses}
        self.assertEqual('editorial plot', ipwww_video.GetItemSynopsis(item_d))

    def test_get_empty_synopsis(self):
        item_d = {'synopsis': None}
        self.assertEqual('', ipwww_video.GetItemSynopsis(item_d))
        item_d = {'synopsis': ''}
        self.assertEqual('', ipwww_video.GetItemSynopsis(item_d))
        item_d = {'synopsis': '', 'synopses': self.synopses}
        self.assertEqual('', ipwww_video.GetItemSynopsis(item_d))

    def test_get_synopses(self):
        synopses = self.synopses.copy()
        item_d = {'synopses': synopses}
        self.assertEqual('editorial plot', ipwww_video.GetItemSynopsis(item_d))
        del synopses['editorial']
        self.assertEqual('large plot', ipwww_video.GetItemSynopsis(item_d))
        del synopses['large']
        self.assertEqual('medium plot', ipwww_video.GetItemSynopsis(item_d))
        del synopses['medium']
        self.assertEqual('small plot', ipwww_video.GetItemSynopsis(item_d))
        del synopses['small']
        self.assertEqual('', ipwww_video.GetItemSynopsis(item_d))
        item_d = {'synopses': None}
        self.assertEqual('', ipwww_video.GetItemSynopsis(item_d))
