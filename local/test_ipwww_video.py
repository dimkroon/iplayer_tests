from support import fixtures
fixtures.global_setup()

from unittest import TestCase
from unittest.mock import patch, MagicMock

from resources.lib import ipwww_video

from support.testutils import open_json
from support.object_checks import is_li_compatible_dict


setUp = fixtures.setup_local_tests()


class TestSelectSynopsis(TestCase):
    synopses = {'editorial': 'editorial plot',
                'large': 'large plot',
                'medium': 'medium plot',
                'small': 'small plot'}

    def test_get_synposis_as_string(self):
        item_d = {'synopsis': 'my plot', 'synopses': self.synopses}
        self.assertEqual('my plot', ipwww_video.SelectSynopsis(item_d))
        item_d = {'synopsis': None, 'synopses': self.synopses}
        self.assertEqual('editorial plot', ipwww_video.SelectSynopsis(item_d))

    def test_get_synoposis_as_dict(self):
        item_d = {'synopsis': self.synopses}
        self.assertEqual('editorial plot', ipwww_video.SelectSynopsis(item_d))

    def test_get_empty_synopsis(self):
        item_d = {'synopsis': None}
        self.assertEqual('', ipwww_video.SelectSynopsis(item_d))
        item_d = {'synopsis': ''}
        self.assertEqual('', ipwww_video.SelectSynopsis(item_d))
        item_d = {'synopsis': '', 'synopses': self.synopses}
        self.assertEqual('', ipwww_video.SelectSynopsis(item_d))

    def test_get_synopses(self):
        synopses = self.synopses.copy()
        item_d = {'synopses': synopses}
        self.assertEqual('editorial plot', ipwww_video.SelectSynopsis(item_d))
        del synopses['editorial']
        self.assertEqual('large plot', ipwww_video.SelectSynopsis(item_d))
        del synopses['large']
        self.assertEqual('medium plot', ipwww_video.SelectSynopsis(item_d))
        del synopses['medium']
        self.assertEqual('small plot', ipwww_video.SelectSynopsis(item_d))
        del synopses['small']
        self.assertEqual('', ipwww_video.SelectSynopsis(item_d))
        item_d = {'synopses': None}
        self.assertEqual('', ipwww_video.SelectSynopsis(item_d))


class TestParseEpisode(TestCase):
    def test_parse_episode(self):
        data = open_json('html/watching.json')
        for item_data in data['items']['elements']:
            result = ipwww_video.ParseEpisode(item_data['episode'])
            # A mode is to be added by the caller of ParseEpisode, add a fake one to be AddMenuEntry compatible
            result['mode'] = 0
            is_li_compatible_dict(self, result)


@patch('resources.lib.ipwww_video.GetJsonDataWithBBCid', return_value=open_json('html/watching.json'))
class TestListWatching(TestCase):
    def test_list_watching_authenticated(self, _):
        with patch('resources.lib.ipwww_video.AddMenuEntry') as p_AddMenuEntry:
            ipwww_video.ListWatching()
        self.assertEqual(11, p_AddMenuEntry.call_count)