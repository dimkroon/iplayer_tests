import os.path

import xbmc

from support import fixtures
fixtures.global_setup()

from unittest import TestCase
from unittest.mock import patch, Mock, MagicMock, call

from resources.lib import ipwww_search


class TestSearchTermsFile(TestCase):
    def setUp(self):
        # clear file
        f = ipwww_search.SearchHistory('video')
        path = f.full_path
        if os.path.isfile(path):
            os.remove(path)

    def test_file(self):
        f = ipwww_search.SearchHistory('video')
        # Empty list when search file does not exist
        self.assertListEqual([], list(f))
        # Add to empty list
        f.append('blabla')
        self.assertEqual(['blabla'], list(f))
        # Add to non-empty list
        f.append('bibi')
        self.assertEqual(['blabla', 'bibi'], list(f))
        # Add already existing search term
        f.append('blabla')
        self.assertEqual(['blabla', 'bibi'], list(f))
        # Add empty string
        f.append('')
        self.assertEqual(['blabla', 'bibi'], list(f))

        # Terms are actually saved
        f = ipwww_search.SearchHistory('video')
        self.assertEqual(['blabla', 'bibi'], list(f))

        # Remove a term
        f.remove('blabla')
        self.assertEqual(['bibi'], list(f))

        # Terms are again actually saved
        f = ipwww_search.SearchHistory('video')
        self.assertEqual(['bibi'], list(f))

        # Audio has its own list of search terms
        f = ipwww_search.SearchHistory('audio')
        self.assertListEqual([], list(f))
        f.append('zaza')
        self.assertEqual(['zaza'], list(f))

    def test_invalid_content_type(self):
        self.assertRaises(ValueError, ipwww_search.SearchHistory, 'iplayer')
        ipwww_search.SearchHistory('a;klj')

    def test_iterator(self):
        f = ipwww_search.SearchHistory('video')
        f.append('blabla')
        f.append('bibi')
        terms = list(t for t in f)
        self.assertListEqual(terms, list(f))

    def test_bool(self):
        f = ipwww_search.SearchHistory('video')
        self.assertIs(bool(f), False)
        f.append('blabla')
        self.assertIs(bool(f), True)


@patch('resources.lib.ipwww_video.Search')
@patch('resources.lib.ipwww_search.SearchHistory.append')
class test_list_search_items(TestCase):
    def setUp(self):
        self.li_store = fixtures.ListItemCollector()
        self.p = patch('xbmcplugin.addDirectoryItem', self.li_store)
        self.p.start()

    def tearDown(self):
        self.p.stop()

    def keyb_mock(self, text, confirm=True):
        class KeybMock(Mock):
            isConfirmed = Mock(return_value=confirm)
            getText = Mock(return_value=text)
        return KeybMock()

    @patch('resources.lib.ipwww_search.SearchHistory._read_file', return_value={'video':['term1', 'term2']})
    def test_list_with_saved_items(self, _, __, ___):
        ipwww_search.list_search_terms('video', 130, keyword=None)
        self.assertEqual(3, len(self.li_store))
        self.assertEqual('New Search', self.li_store.list_item(0).getLabel())
        self.assertEqual('term1', self.li_store.list_item(1).getLabel())
        self.assertEqual('term2', self.li_store.list_item(2).getLabel())
        self.assertTrue('keyword=new_search' in self.li_store.path(0))
        self.assertTrue('mode=104' in self.li_store.path(0))
        self.assertTrue('keyword=term1' in self.li_store.path(1))
        self.assertTrue('mode=130' in self.li_store.path(1))
        self.assertTrue('keyword=term2' in self.li_store.path(2))
        self.assertTrue('mode=130' in self.li_store.path(2))

    @patch('resources.lib.ipwww_search.SearchHistory._read_file', return_value={'video':[]})
    def test_list_without_saved_items(self, _, p_add_term, p_do_search):
        # Without search term
        with patch('xbmc.Keyboard', new_callable=self.keyb_mock, text='new term'):
            ipwww_search.list_search_terms('video', 130, keyword=None)
            self.assertEqual(0, len(self.li_store))
            p_do_search.assert_called_once_with('new term')
            p_add_term.assert_called_once_with('new term')

        p_add_term.reset_mock()
        p_do_search.reset_mock()

        # With a random search term
        with patch('xbmc.Keyboard', new_callable=self.keyb_mock, text='new term'):
            ipwww_search.list_search_terms('video', 130, keyword='Some search term')
            self.assertEqual(0, len(self.li_store))
            p_do_search.assert_called_once_with('new term')
            p_add_term.assert_called_once_with('new term')

    @patch('resources.lib.ipwww_search.SearchHistory._read_file', return_value={'video': ['term1', 'term2']})
    def test_explicit_new_search_with_saved_terms(self, _, p_add_term, p_do_search):
        """A new search has been requested by setting keyword to 'new_search'"""
        with patch('xbmc.Keyboard', new_callable=self.keyb_mock, text='new term'):
            ipwww_search.list_search_terms('video', 130, keyword='new_search')
            self.assertEqual(0, len(self.li_store))
            p_do_search.assert_called_once_with('new term')
            p_add_term.assert_called_once_with('new term')

    @patch('resources.lib.ipwww_search.SearchHistory._read_file', return_value={'video': ['term1', 'term2']})
    def test_saved_terms_with_random_keyword(self, p_get_terms, p_add_term, p_do_search):
        """Only keyword 'new_search' should trigger a keyboard entry."""
        with patch('xbmc.Keyboard', new_callable=self.keyb_mock, text='new term') as kb:
            ipwww_search.list_search_terms('video', 130, keyword='random term')
            p_get_terms.assert_called_once()
            self.assertEqual(3, len(self.li_store))
            p_do_search.assert_not_called()
            p_add_term.assert_not_called()
            kb.getText.assert_not_called()

    @patch('resources.lib.ipwww_search.SearchHistory._read_file', return_value={'video': ['term1', 'term2']})
    def test_keyboard_canceled_with_saved_terms(self, p_get_terms, p_add_term, p_do_search):
        """On keyboard cancel the saved list of search terms should be shown."""
        with patch('xbmc.Keyboard', new_callable=self.keyb_mock, text='new term', confirm=False) as kb:
            ipwww_search.list_search_terms('video', 130, keyword='new_search')
            p_get_terms.assert_called_once()
            self.assertEqual(3, len(self.li_store))
            p_do_search.assert_not_called()
            p_add_term.assert_not_called()

    @patch('resources.lib.ipwww_search.SearchHistory._read_file', return_value={'video': ['term1', 'term2']})
    def test_keyboard_empty_string_with_saved_terms(self, p_get_terms, p_add_term, p_do_search):
        """Empty keyboard input should be handled the same as keyboard cancel."""
        with patch('xbmc.Keyboard', new_callable=self.keyb_mock, text='') as kb:
            ipwww_search.list_search_terms('video', 130, keyword='new_search')
            p_get_terms.assert_called_once()
            self.assertEqual(3, len(self.li_store))
            p_do_search.assert_not_called()
            p_add_term.assert_not_called()
            kb.getText.assert_called_once()

    @patch('resources.lib.ipwww_search.SearchHistory._read_file', return_value={'video': []})
    @patch('resources.lib.ipwww_search.CreateBaseDirectory')
    def test_keyboard_canceled_NO_saved_terms(self, p_create_base, p_get_terms, p_add_term, p_do_search):
        """Show the main menu when input is canceled and there are no saved search terms."""
        with patch('xbmc.Keyboard', new_callable=self.keyb_mock, text='new term', confirm=False) as kb:
            ipwww_search.list_search_terms('video', 130, keyword='new_search')
            p_get_terms.assert_called_once()
            self.assertEqual(0, len(self.li_store))
            p_do_search.assert_not_called()
            p_add_term.assert_not_called()
            p_create_base.assert_called_once()

    @patch('resources.lib.ipwww_search.SearchHistory._read_file', return_value={'video': []})
    @patch('resources.lib.ipwww_search.CreateBaseDirectory')
    def test_keyboard_canceled_NO_saved_terms(self, p_create_base, p_get_terms, p_add_term, p_do_search):
        """Empty keyboard input should be handled the same as keyboard cancel."""
        with patch('xbmc.Keyboard', new_callable=self.keyb_mock, text='') as kb:
            ipwww_search.list_search_terms('video', 130, keyword='new_search')
            p_get_terms.assert_called_once()
            self.assertEqual(0, len(self.li_store))
            p_do_search.assert_not_called()
            p_add_term.assert_not_called()
            p_create_base.assert_called_once()
            kb.getText.assert_called_once()

    @patch('resources.lib.ipwww_search.SearchHistory._read_file', return_value={'video': []})
    @patch('resources.lib.ipwww_radio.Search')
    def test_search_radio_when_content_type_is_audio(self, p_do_radio_search, _, __, p_do_search):
        """When keyboard entry is requested on radio search, assert the correct
        search function is being called
        """
        with patch('xbmc.Keyboard', new_callable=self.keyb_mock, text='blabla'):
            ipwww_search.list_search_terms('audio', 140)
            p_do_search.assert_not_called()
            p_do_radio_search.assert_called_once_with('blabla')