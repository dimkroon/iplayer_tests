from support import fixtures
fixtures.global_setup()

from unittest import TestCase
from unittest.mock import patch, MagicMock

import xbmcplugin

from resources.lib import ipwww_video

from support.testutils import open_json
from support.object_checks import is_li_compatible_dict, has_keys, is_url, is_not_empty


setUp = fixtures.setup_local_tests()


class SetSortMethod(TestCase):
    @patch('xbmcplugin.addSortMethod')
    def test_set_default_sort_method(self,p_addsort):
        ipwww_video.SetSortMethods()
        self.assertEqual(3, p_addsort.call_count)

    @patch('xbmcplugin.addSortMethod')
    def test_set_additional_method(self, p_addsort):
        ipwww_video.SetSortMethods(xbmcplugin.SORT_METHOD_DATE)
        self.assertEqual(4, p_addsort.call_count)


class TestSelectSynopsis(TestCase):
    def setUp(self):
        self.synopses = {'editorial': 'editorial plot',
                        'large': 'large plot',
                        'medium': 'medium plot',
                        'small': 'small plot'}

    def test_get_synopsis_presence(self):
        syn = self.synopses
        self.assertEqual('editorial plot', ipwww_video.SelectSynopsis(syn))
        del syn['editorial']
        self.assertEqual('medium plot', ipwww_video.SelectSynopsis(syn))
        del syn['medium']
        self.assertEqual('large plot', ipwww_video.SelectSynopsis(syn))
        del syn['large']
        self.assertEqual('small plot', ipwww_video.SelectSynopsis(syn))
        del syn['small']
        self.assertEqual('', ipwww_video.SelectSynopsis(syn))

    def test_get_synopsis_empty(self):
        syn = self.synopses
        self.assertEqual('editorial plot', ipwww_video.SelectSynopsis(syn))
        syn['editorial'] = ''
        self.assertEqual('medium plot', ipwww_video.SelectSynopsis(syn))
        syn['medium'] = ''
        self.assertEqual('large plot', ipwww_video.SelectSynopsis(syn))
        syn['large'] = ''
        self.assertEqual('small plot', ipwww_video.SelectSynopsis(syn))
        syn['small'] = ''
        self.assertEqual('', ipwww_video.SelectSynopsis(syn))
        self.assertEqual('', ipwww_video.SelectSynopsis(syn))

    def test_get_synopsis_none(self):
        syn = self.synopses
        self.assertEqual('editorial plot', ipwww_video.SelectSynopsis(syn))
        syn['editorial'] = None
        self.assertEqual('medium plot', ipwww_video.SelectSynopsis(syn))
        syn['medium'] = None
        self.assertEqual('large plot', ipwww_video.SelectSynopsis(syn))
        syn['large'] = None
        self.assertEqual('small plot', ipwww_video.SelectSynopsis(syn))
        syn['small'] = None
        self.assertEqual('', ipwww_video.SelectSynopsis(syn))

    def test_empy_dicts(self):
        self.assertEqual('', ipwww_video.SelectSynopsis(None))
        self.assertEqual('', ipwww_video.SelectSynopsis({}))
        self.assertRaises(AttributeError, ipwww_video.SelectSynopsis, '')


class TestParseEpisode(TestCase):
    def test_parse_episode(self):
        data = open_json('html/watching.json')
        for item_data in data['items']['elements']:
            result = ipwww_video.ParseEpisode(item_data['episode'])
            # A mode is to be added by the caller of ParseEpisode, add a fake one to be AddMenuEntry(...) compatible
            result['mode'] = 0
            is_li_compatible_dict(self, result)



class TestListWatching(TestCase):
    @patch('resources.lib.ipwww_video.GetJsonDataWithBBCid', return_value=open_json('html/watching.json'))
    def test_list_watching_authenticated(self, _):
        with patch('resources.lib.ipwww_video.CheckAutoplay') as p_CheckAutoplay:
            ipwww_video.ListWatching()
        self.assertEqual(11, p_CheckAutoplay.call_count)
        for call in p_CheckAutoplay.call_args_list:
            call_kw = call.kwargs
            has_keys(call_kw, 'url','name', 'iconimage','description', 'aired', 'context_mnu')
            self.assertTrue(is_url(call_kw['url']))
            self.assertTrue(is_url(call_kw['iconimage']))
            self.assertTrue(is_not_empty(call_kw['description'], str))
            self.assertTrue(is_not_empty(call_kw['context_mnu'], list))
            if is_not_empty(call_kw.get('resume_time'), str):
                self.assertGreater(float(call_kw['resume_time']), 0)
                self.assertTrue(is_not_empty(call_kw['total_time'], str))
                self.assertGreater(int(call_kw['total_time']), float(call_kw['resume_time']))


class TestListRecommendations(TestCase):
    @patch('resources.lib.ipwww_video.GetJsonDataWithBBCid', return_value=open_json('html/recommendations.json'))
    def test_list_recommendations_authenticated(self, _):
        with patch('xbmcplugin.addDirectoryItem') as p_AddItem:
            ipwww_video.ListRecommendations()
        self.assertEqual(20, p_AddItem.call_count)
