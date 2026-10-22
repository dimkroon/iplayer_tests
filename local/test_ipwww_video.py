from support import fixtures
fixtures.global_setup()

from unittest import TestCase
from unittest.mock import patch, MagicMock, call

import xbmcplugin

from resources.lib import ipwww_video

from support.testutils import open_json, open_doc
from support.object_checks import is_li_compatible_dict, has_keys, is_url, is_not_empty


class TestGetJsonDataWithBBCId(TestCase):
    @patch('resources.lib.ipwww_video.OpenURL', new=open_doc('html/iplayer.html'))
    def test_main_page(self):
        data = ipwww_video.GetJsonDataWithBBCid('https://www.bbc.co.uk/iplayer')
        pass


class TestListAtoZPage(fixtures.LocalTestCase):
    def test_list_attoz_all_per_letter(self):
        """Test that ListAtoZPage returns a list of all letters of the alphabet plus '0-9'."""
        self.addon_settings = {'scrape_atoz': 0}
        ipwww_video.ListAtoZ()
        self.assertEqual(27, len(self.li_store))
        self.assertEqual(self.li_store.list_item(0).getLabel(), 'A')
        self.assertEqual(self.li_store.list_item(-1).getLabel(), '0-9')

    @patch('resources.lib.ipwww_common.OpenRequest', return_value=open_doc('html/a_to_z_page_D.html')())
    def test_close_progress_dialog(self, open_page):
        """Get all pages of all letters at once, ensure the progress dialog is closed."""
        self.addon_settings = {'scrape_atoz': 1}
        with patch('xbmcgui.DialogProgressBG.close') as p_close:
            ipwww_video.ListAtoZ()
        # Programmes of letter 'D' are spread over 2 pages, so a total of 27 * 2 requests are expected.
        self.assertEqual(54, open_page.call_count)
        p_close.assert_called_once()

    @patch('resources.lib.ipwww_common.OpenRequest', side_effect=SystemExit)
    def test_close_progress_dialog_on_network_error(self, _):
        self.addon_settings = {'scrape_atoz': 1}

        with patch('xbmcgui.DialogProgressBG.close') as p_close:
            self.assertRaises(SystemExit, ipwww_video.ListAtoZ)
        p_close.assert_called_once()

    @patch('resources.lib.ipwww_common.OpenRequest', new=open_doc('html/a_to_z_page_D.html'))
    @patch('resources.lib.ipwww_video.ParseJSON', side_effect=TypeError)
    def test_close_progress_dialog_on_parse_error(self, _):
        self.addon_settings = {'scrape_atoz': 1}

        with patch('xbmcgui.DialogProgressBG.close') as p_close:
            self.assertRaises(TypeError, ipwww_video.ListAtoZ)
        p_close.assert_called_once()


class ScrapeEpisodes(fixtures.LocalTestCase):
    def setUp(self):
        super().setUp()
        self.num_requested_pages = 0

    def page_feeder(self, *_, **__):
        self.num_requested_pages += 1
        return open_doc('html/bbc-three_az.html')()

    def test_scrape_channel_az_page_paginated(self):
        self.addon_settings['paginate_episodes'] = 0

        with patch('resources.lib.ipwww_common.OpenRequest', new=self.page_feeder):
            ipwww_video.ScrapeEpisodes('bbctwo')
        self.assertEqual(1, self.num_requested_pages)
        self.assertEqual(len(self.li_store), 37)
        self.assertTrue('Next page' in self.li_store.list_item(-1).getLabel())

    def test_scrape_channel_az_page_all_at_once(self):
        self.addon_settings['paginate_episodes'] = 1

        with patch('resources.lib.ipwww_common.OpenRequest', new=self.page_feeder):
            ipwww_video.ScrapeEpisodes('bbctwo')
        self.assertEqual(7, self.num_requested_pages)
        self.assertGreater(len(self.li_store), 100)
        for item in self.li_store.list_items:
            self.assertFalse('Next page' in item.getLabel())


class SetSortMethod(fixtures.LocalTestCase):
    @patch('xbmcplugin.addSortMethod')
    def test_set_default_sort_method(self,p_addsort):
        ipwww_video.SetSortMethods()
        self.assertEqual(3, p_addsort.call_count)

    @patch('xbmcplugin.addSortMethod')
    def test_set_additional_method(self, p_addsort):
        ipwww_video.SetSortMethods(xbmcplugin.SORT_METHOD_DATE)
        self.assertEqual(4, p_addsort.call_count)


class TestSelectSynopsisOfPlayable(fixtures.LocalTestCase):
    def setUp(self):
        super().setUp()
        self.synopses = {'editorial': 'editorial plot',
                         'large': 'large plot',
                         'medium': 'medium plot',
                         'small': 'small plot',
                         'programme_small': 'programme small plot',
                         'programmeSmall': 'programmeSmall plot',
                         'live': 'live plot'}

    def test_get_synopsis_presence(self):
        syn = self.synopses
        self.assertEqual('medium plot', ipwww_video.SelectSynopsis(syn))
        del syn['medium']
        self.assertEqual('large plot', ipwww_video.SelectSynopsis(syn))
        del syn['large']
        self.assertEqual('small plot', ipwww_video.SelectSynopsis(syn))
        del syn['small']
        self.assertEqual('editorial plot', ipwww_video.SelectSynopsis(syn))
        del syn['editorial']
        self.assertEqual('programme small plot', ipwww_video.SelectSynopsis(syn))
        del syn['programme_small']
        self.assertEqual('programmeSmall plot', ipwww_video.SelectSynopsis(syn))
        del syn['programmeSmall']
        self.assertEqual('live plot', ipwww_video.SelectSynopsis(syn))
        del syn['live']
        self.assertEqual('', ipwww_video.SelectSynopsis(syn))

    def test_some_types_absent(self):
        syn = {'medium': None, 'small': 'small plot'}
        self.assertEqual('small plot', ipwww_video.SelectSynopsis(syn))

    def test_get_synopsis_empty(self):
        syn = self.synopses
        self.assertEqual('medium plot', ipwww_video.SelectSynopsis(syn))
        syn['medium'] = ''
        self.assertEqual('large plot', ipwww_video.SelectSynopsis(syn))
        syn['large'] = ''
        self.assertEqual('small plot', ipwww_video.SelectSynopsis(syn))
        syn['small'] = ''
        self.assertEqual('editorial plot', ipwww_video.SelectSynopsis(syn))
        syn['editorial'] = ''
        self.assertEqual('programme small plot', ipwww_video.SelectSynopsis(syn))
        syn['programme_small'] = ''
        self.assertEqual('programmeSmall plot', ipwww_video.SelectSynopsis(syn))
        syn['programmeSmall'] = ''
        self.assertEqual('live plot', ipwww_video.SelectSynopsis(syn))
        syn['live'] = ''
        self.assertEqual('', ipwww_video.SelectSynopsis(syn))

    def test_get_synopsis_none(self):
        syn = self.synopses
        self.assertEqual('medium plot', ipwww_video.SelectSynopsis(syn))
        syn['medium'] = None
        self.assertEqual('large plot', ipwww_video.SelectSynopsis(syn))
        syn['large'] = None
        self.assertEqual('small plot', ipwww_video.SelectSynopsis(syn))
        syn['small'] = None
        self.assertEqual('editorial plot', ipwww_video.SelectSynopsis(syn))
        syn['editorial'] = None
        self.assertEqual('programme small plot', ipwww_video.SelectSynopsis(syn))
        syn['programme_small'] = None
        self.assertEqual('programmeSmall plot', ipwww_video.SelectSynopsis(syn))
        syn['programmeSmall'] = None
        self.assertEqual('live plot', ipwww_video.SelectSynopsis(syn))
        syn['live'] = None
        self.assertEqual('', ipwww_video.SelectSynopsis(syn))

    def test_synopsis_all_fields_none(self):
        syn = {k: None for k in self.synopses.keys()}
        self.assertEqual('', ipwww_video.SelectSynopsis(syn))

    def test_empy_dicts(self):
        self.assertEqual('', ipwww_video.SelectSynopsis(None))
        self.assertEqual('', ipwww_video.SelectSynopsis({}))

    def test_synopsis_as_string(self):
        self.assertEqual('description', ipwww_video.SelectSynopsis('description'))


class TestSelectSynopsisOfProgramme(fixtures.LocalTestCase):
    def setUp(self):
        super().setUp()
        self.synopses = {'editorial': 'editorial plot',
                         'large': 'large plot',
                         'medium': 'medium plot',
                         'small': 'small plot',
                         'programme_small': 'programme small plot',
                         'programmeSmall': 'programmeSmall plot',
                         'live': 'live plot'}

    def test_get_synopsis_presence(self):
        syn = self.synopses
        self.assertEqual('programme small plot', ipwww_video.SelectSynopsis(syn, False))
        del syn['programme_small']
        self.assertEqual('programmeSmall plot', ipwww_video.SelectSynopsis(syn, False))
        del syn['programmeSmall']
        self.assertEqual('editorial plot', ipwww_video.SelectSynopsis(syn, False))
        del syn['editorial']
        self.assertEqual('medium plot', ipwww_video.SelectSynopsis(syn, False))
        del syn['medium']
        self.assertEqual('large plot', ipwww_video.SelectSynopsis(syn, False))
        del syn['large']
        self.assertEqual('small plot', ipwww_video.SelectSynopsis(syn, False))
        del syn['small']
        self.assertEqual('live plot', ipwww_video.SelectSynopsis(syn, False))
        del syn['live']
        self.assertEqual('', ipwww_video.SelectSynopsis(syn, False))

    def test_some_types_absent(self):
        syn = {'programme_small': None, 'small': 'small plot'}
        self.assertEqual('small plot', ipwww_video.SelectSynopsis(syn, False))

    def test_get_synopsis_empty(self):
        syn = self.synopses
        self.assertEqual('programme small plot', ipwww_video.SelectSynopsis(syn, False))
        syn['programme_small'] = ''
        self.assertEqual('programmeSmall plot', ipwww_video.SelectSynopsis(syn, False))
        syn['programmeSmall'] = ''
        self.assertEqual('editorial plot', ipwww_video.SelectSynopsis(syn, False))
        syn['editorial'] = ''
        self.assertEqual('medium plot', ipwww_video.SelectSynopsis(syn, False))
        syn['medium'] = ''
        self.assertEqual('large plot', ipwww_video.SelectSynopsis(syn, False))
        syn['large'] = ''
        self.assertEqual('small plot', ipwww_video.SelectSynopsis(syn, False))
        syn['small'] = ''
        self.assertEqual('live plot', ipwww_video.SelectSynopsis(syn, False))
        syn['live'] = ''
        self.assertEqual('', ipwww_video.SelectSynopsis(syn, False))

    def test_get_synopsis_none(self):
        syn = self.synopses
        self.assertEqual('programme small plot', ipwww_video.SelectSynopsis(syn, False))
        syn['programme_small'] = None
        self.assertEqual('programmeSmall plot', ipwww_video.SelectSynopsis(syn, False))
        syn['programmeSmall'] = None
        self.assertEqual('editorial plot', ipwww_video.SelectSynopsis(syn, False))
        syn['editorial'] = None
        self.assertEqual('medium plot', ipwww_video.SelectSynopsis(syn, False))
        syn['medium'] = None
        self.assertEqual('large plot', ipwww_video.SelectSynopsis(syn, False))
        syn['large'] = None
        self.assertEqual('small plot', ipwww_video.SelectSynopsis(syn, False))
        syn['small'] = None
        self.assertEqual('live plot', ipwww_video.SelectSynopsis(syn, False))
        syn['live'] = None
        self.assertEqual('', ipwww_video.SelectSynopsis(syn, False))

    def test_synopsis_all_fields_none(self):
        syn = {k: None for k in self.synopses.keys()}
        self.assertEqual('', ipwww_video.SelectSynopsis(syn, False))

    def test_empy_dicts(self):
        self.assertEqual('', ipwww_video.SelectSynopsis(None, False))
        self.assertEqual('', ipwww_video.SelectSynopsis({}, False))

    def test_synopsis_as_string(self):
        self.assertEqual('description', ipwww_video.SelectSynopsis('description', False))


class TestSelectImage(fixtures.LocalTestCase):
    def setUp(self):
        super().setUp()
        self.images = {'standard': 'standard image',
                       'default': 'default image',
                       'portrait': 'portrait image',
                       'promotional': 'promotional image',
                       'promotional_with_logo': 'promotional_with_logo image'
                       }

    def test_get_images_presence(self):
        images = self.images
        while images:
            key, value = list(images.items())[0]
            self.assertEqual(value, ipwww_video.SelectImage(images))
            images.pop(key)
        self.assertEqual('DefaultFolder.png', ipwww_video.SelectImage(images))

    def test_some_image_types_absent(self):
        images = {'standard': None,
                  'promotional_with_logo': 'promotional_with_logo image',}
        self.assertEqual('promotional_with_logo image', ipwww_video.SelectImage(images))

    def test_get_images_empty(self):
        images = self.images
        for i in range(len(images)):
            key, value = list(images.items())[i]
            self.assertEqual(value, ipwww_video.SelectImage(images))
            images[key] = ''
        self.assertEqual('DefaultFolder.png', ipwww_video.SelectImage(images))

    def test_get_images_none(self):
        images = self.images
        for i in range(len(images)):
            key, value = list(images.items())[i]
            self.assertEqual(value, ipwww_video.SelectImage(images))
            images[key] = None
        self.assertEqual('DefaultFolder.png', ipwww_video.SelectImage(images))

    def test_empy_dicts(self):
        self.assertEqual('DefaultFolder.png', ipwww_video.SelectImage(None))
        self.assertEqual('DefaultFolder.png', ipwww_video.SelectImage({}))
        self.assertRaises(AttributeError, ipwww_video.SelectImage, 'DefaultFolder.png')


class TestParseProgramme(fixtures.LocalTestCase):
    def test_parse_programma(self):
        data = open_json('video_programmes.json')
        for progr_data in data:
            result = ipwww_video.ParseProgramme(progr_data)
            # A mode is to be added by the caller of ParseProgramme, add a fake one to be AddMenuEntry compatible
            result['mode'] = 0
            is_li_compatible_dict(self, result)


class TestParseEpisode(fixtures.LocalTestCase):
    def test_parse_episode(self):
        data = open_json('html/watching.json')
        for item_data in data['items']['elements']:
            result = ipwww_video.ParseEpisode(item_data['episode'])
            # A mode is to be added by the caller of ParseEpisode, add a fake one to be AddMenuEntry(...) compatible
            result['mode'] = 0
            is_li_compatible_dict(self, result)


class Categories(fixtures.LocalTestCase):
    addon_settings = {'paginate_episodes': 0}

    @patch('resources.lib.ipwww_video.OpenURL', open_doc('html/homepage.html'))
    def test_get_all_categories(self):
        ipwww_video.ListCategories()
        self.assertEqual(len(self.li_store), 21)

    @patch('resources.lib.ipwww_video.OpenURL', open_doc('html/category_drama-and-soaps.html'))
    def test_category_drama_and_soaps(self):
        "This category redirects to /browse/drama-and-soaps and returns a page in the format."
        ipwww_video.GetFilteredCategory(url='dma and soaps')
        self.assertGreater(len(self.li_store), 6)

    @patch('resources.lib.ipwww_video.OpenURL', open_doc('html/category_comedy.html'))
    def test_category_comedy(self):
        "This category page in the classic format."
        ipwww_video.GetFilteredCategory(url='comedy')
        self.assertGreater(len(self.li_store), 6)


class Groups(fixtures.LocalTestCase):
    @patch('resources.lib.ipwww_video.OpenURL', open_doc('html/group.html'))
    def test_single_page_group(self):
        ipwww_video.GetGroup(url='bsfkgkj')
        self.assertEqual(len(self.li_store), 16)

    @patch('resources.lib.ipwww_video.OpenURL', open_doc('html/group_page-1-of-3.html'))
    def test_multipage_page_group(self):
        ipwww_video.GetGroup(url='bsfkgkj')
        self.assertEqual(len(self.li_store), 108)


class TestListWatching(fixtures.LocalTestCase):
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
                self.assertGreaterEqual(float(call_kw['resume_time']), 0)
                self.assertTrue(is_not_empty(call_kw['total_time'], str))
                self.assertGreater(int(call_kw['total_time']), float(call_kw['resume_time']))


@patch('resources.lib.ipwww_video.GetJsonDataWithBBCid', return_value=open_json('html/watchlist.json'))
class TestListFavourites(fixtures.LocalTestCase):
    def test_list_favourites_authenticated(self, _):
        with patch('resources.lib.ipwww_video.AddMenuEntry') as p_AddMenuEntry:
            ipwww_video.ListFavourites()
        self.assertEqual(10, p_AddMenuEntry.call_count)


@patch('resources.lib.ipwww_video.GetJsonDataWithBBCid', return_value=open_json('json/iplayer.json'))
class TestListRecommendations(fixtures.LocalTestCase):
    def test_list_recommendations_authenticated(self, _):
        with patch('xbmcplugin.addDirectoryItem') as p_AddItem:
            ipwww_video.ListRecommendations()
        self.assertEqual(2, p_AddItem.call_count)

    def test_list_if_you_liked_content(self, _):
        with patch('xbmcplugin.addDirectoryItem') as p_AddItem:
            ipwww_video.ListRecommendations('if-you-liked')
        self.assertEqual(12, p_AddItem.call_count)

    def test_recommended_content(self, _):
        with patch('xbmcplugin.addDirectoryItem') as p_AddItem:
            ipwww_video.ListRecommendations('recommendations')
        self.assertEqual(12, p_AddItem.call_count)


class TestScrapeAvailableStream(fixtures.LocalTestCase):
    """Play an item from a listing

    """
    @patch('resources.lib.ipwww_video.OpenURL', new=open_doc('html/snooker_uk_sportstream_item.html'))
    def test_scrape_webcast_item(self):
        strm_ids = ipwww_video.ScrapeAvailableStreams('some url')
        self.assertEqual(strm_ids['stream_id_st'], 'l0056v5z')

    @patch('resources.lib.ipwww_video.OpenURL', new=open_doc('html/snooker_uk_live_item.html'))
    def test_scrape_bbc_two_item(self):
        strm_ids = ipwww_video.ScrapeAvailableStreams('some url')
        self.assertEqual(strm_ids['stream_id_st'], 'bbc_two_hd')


    @patch('resources.lib.ipwww_video.OpenURL', side_effect=(open_doc('html/snooker_uk_live_item.html')(),
                                                             open_doc('json/media_selector_snooker_uk_live.json')()))
    def test_play_bbc_two_item(self, _):
        with patch('resources.lib.ipwww_video.PlayStream') as p_play_stream:
            ipwww_video.AddAvailableStreamItem('https://bbc.co.uk/bbctwo')
        p_play_stream.assert_called_once()
        url, subtitles_url, *other_args = p_play_stream.call_args.args
        self.assertTrue(url.endswith('.mpd'))
        self.assertEqual('', subtitles_url)                    # Live subtitles must have been disregarded.


    @patch('resources.lib.ipwww_video.OpenURL', new=open_doc('html/snooker_uk_rb_item.html'))
    def test_scrape_red_button_item(self):
        strm_ids = ipwww_video.ScrapeAvailableStreams('some url')
        self.assertEqual(strm_ids['stream_id_st'], 'red_button_one')
