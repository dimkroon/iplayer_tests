
from support import fixtures
fixtures.global_setup()

import os.path

from unittest import TestCase
from unittest.mock import patch

from support.fixtures import keyb_mock
from resources.lib import ipwww_search


class TestSearchTermsFile(TestCase):
    def setUp(self):
        # clear file
        f = ipwww_search.SearchHistory('video')
        path = f.full_path
        if os.path.isfile(path):
            os.remove(path)

    def test_append(self):
        f = ipwww_search.SearchHistory('video')
        # Empty list when search file does not exist
        self.assertListEqual([], list(f))
        # Add to empty list
        f.append('blabla')
        self.assertEqual(['blabla'], list(f))
        # Add to non-empty list
        f.append('bibi')
        self.assertEqual(['bibi', 'blabla'], list(f))
        # Add already existing search term
        f.append('blabla')
        self.assertEqual(['bibi', 'blabla'], list(f))
        # Add empty string
        f.append('')
        self.assertEqual(['bibi', 'blabla'], list(f))

        # Terms are saved to disk
        f = ipwww_search.SearchHistory('video')
        self.assertEqual(['bibi', 'blabla'], list(f))

        # Audio has its own list of search terms
        f = ipwww_search.SearchHistory('audio')
        self.assertListEqual([], list(f))
        f.append('zaza')
        self.assertEqual(['zaza'], list(f))

    def test_remove(self):
        f = ipwww_search.SearchHistory('video')
        f.append('term1')
        f.append('term2')
        self.assertListEqual(['term2', 'term1'], list(f))

        # Remove a term
        f.remove('term1')
        self.assertEqual(['term2'], list(f))

        # List is saved to disk
        f = ipwww_search.SearchHistory('video')
        self.assertEqual(['term2'], list(f))

        # Removing a non-existing term should fail silently
        f.remove('term3')
        self.assertEqual(['term2'], list(f))

    def test_replace(self):
        f = ipwww_search.SearchHistory('video')
        f.append('term1')
        f.append('term2')
        self.assertListEqual(['term2', 'term1'], list(f))
        f.replace('term1', 'term3')
        self.assertListEqual(['term2', 'term3'], list(f))
        f = ipwww_search.SearchHistory('video')
        self.assertListEqual(['term2', 'term3'], list(f))
        self.assertRaises(ValueError, f.replace, 'term1', 'new term')

    def test_clear(self):
        fv = ipwww_search.SearchHistory('video')
        fa = ipwww_search.SearchHistory('audio')
        fv.append('vterm1')
        fv.append('vterm2')
        fa.append('aterm1')
        fa.append('aterm2')
        self.assertListEqual(['vterm2', 'vterm1'], list(fv))
        self.assertListEqual(['aterm2', 'aterm1'], list(fa))
        fv.clear()
        self.assertListEqual([], list(fv))
        self.assertListEqual(['aterm2', 'aterm1'], list(fa))
        # re-open file
        fv = ipwww_search.SearchHistory('video')
        fa = ipwww_search.SearchHistory('audio')
        self.assertListEqual([], list(fv))
        self.assertListEqual(['aterm2', 'aterm1'], list(fa))

    def test_invalid_content_type(self):
        self.assertRaises(ValueError, ipwww_search.SearchHistory, 'iplayer')

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


class OpenKeyboard(TestCase):
    def test_open_keyboard(self):
        with patch('xbmc.Keyboard', keyb_mock(text='new text', confirmed=True)):
            self.assertEqual('new text', ipwww_search.open_keyboard('video'))
        with patch('xbmc.Keyboard', keyb_mock(text='', confirmed=True)):
            self.assertEqual('', ipwww_search.open_keyboard('video'))
        with patch('xbmc.Keyboard', keyb_mock(text='', confirmed=False)):
            self.assertEqual('', ipwww_search.open_keyboard('video'))


@patch('resources.lib.ipwww_video.Search')
@patch('resources.lib.ipwww_search.SearchHistory.append')
class TestListSearchItems(TestCase):
    def setUp(self):
        self.li_store = fixtures.ListItemCollector()
        self.p = patch('xbmcplugin.addDirectoryItem', self.li_store)
        self.p.start()

    def tearDown(self):
        self.p.stop()

    @patch('resources.lib.ipwww_search.SearchHistory._read_file', return_value={'video': ['term2', 'term1']})
    def test_list_with_saved_items(self, _, __, ___):
        ipwww_search.list_search_terms('video', 130)
        self.assertEqual(3, len(self.li_store))
        li_new_search = self.li_store.list_item(0)
        self.assertEqual('New Search', li_new_search.getLabel())
        # Check item is not a folder and also not playable.
        self.assertEqual('false', li_new_search.getProperty('isplayable'))
        self.assertFalse(self.li_store[0][2])       # isFolder
        self.assertTrue('mode=190' in self.li_store.path(0))

        self.assertEqual('term2', self.li_store.list_item(1).getLabel())
        self.assertTrue('url=term2' in self.li_store.path(1))
        self.assertTrue('mode=130' in self.li_store.path(1))

        self.assertEqual('term1', self.li_store.list_item(2).getLabel())
        self.assertTrue('url=term1' in self.li_store.path(2))
        self.assertTrue('mode=130' in self.li_store.path(2))


@patch('resources.lib.ipwww_search.SearchHistory.append')
@patch('xbmc.executebuiltin')
class NewSearch(TestCase):
    @patch('resources.lib.ipwww_search.SearchHistory._read_file', return_value={'video': []})
    def test_new_search(self, _, p_exec_builtin, p_append):
        with patch('xbmc.Keyboard', keyb_mock(text='new term')):
            ipwww_search.new_search('video', 130)
            p_append.assert_called_once_with('new term')
            p_exec_builtin.assert_called_once()
            self.assertTrue(p_exec_builtin.call_args.args[0].startswith('Container.Update'))

    @patch('resources.lib.ipwww_search.SearchHistory._read_file', return_value={'video': ['term1', 'term2']})
    def test_keyboard_canceled(self, _, p_exec_builtin, p_append):
        """On keyboard cancel the saved list of search terms should be shown."""
        with patch('xbmc.Keyboard', keyb_mock(text='new term', confirmed=False)):
            ipwww_search.list_search_terms('video', 130)
            p_append.assert_not_called()
            p_exec_builtin.assert_not_called()

    @patch('resources.lib.ipwww_search.SearchHistory._read_file', return_value={'video': ['term1', 'term2']})
    def test_keyboard_empty_string(self, _, p_exec_builtin, p_append):
        """Empty keyboard input should be handled the same as keyboard cancel."""
        with patch('xbmc.Keyboard', keyb_mock(text='')) as kb:
            ipwww_search.list_search_terms('video', 130)
            p_append.assert_not_called()
            p_exec_builtin.assert_not_called()


@patch('xbmc.executebuiltin')
class TestContextMenu(TestCase):
    @patch('resources.lib.ipwww_search.SearchHistory.remove')
    def test_remove_existing_term(self, p_remove, p_exec_builtin):
        ipwww_search.context_menu('video', 'remove', 'term1')
        p_remove.assert_called_once_with('term1')
        self.assertEqual('Container.Refresh', p_exec_builtin.call_args.args[0])

    @patch('resources.lib.ipwww_search.SearchHistory.replace')
    @patch('xbmc.Keyboard', keyb_mock(text='new-text'))
    def test_edit_search_term_with_new_text(self, p_replace, p_exec_builtin):
        ipwww_search.context_menu('video', 'edit', 'term1')
        p_replace.assert_called_once_with('term1', 'new-text')
        self.assertEqual('Container.Refresh', p_exec_builtin.call_args.args[0])

    @patch('resources.lib.ipwww_search.SearchHistory.replace')
    @patch('xbmc.Keyboard', keyb_mock(text='', confirmed=True))
    @patch('resources.lib.ipwww_search.SearchHistory.remove')
    def test_edit_search_term_with_empty_string(self, p_remove, p_replace, p_exec_builtin):
        """Replacing with an empty string is the same as remove."""
        ipwww_search.context_menu('video', 'edit', 'term1')
        p_remove.assert_called_once_with('term1')
        p_replace.assert_not_called()
        self.assertEqual('Container.Refresh', p_exec_builtin.call_args.args[0])

    @patch('resources.lib.ipwww_search.SearchHistory.replace')
    @patch('xbmc.Keyboard', keyb_mock(text='', confirmed=False))
    @patch('resources.lib.ipwww_search.SearchHistory.remove')
    def test_edit_search_term_with_canceled_keyboard(self, p_remove, p_replace, p_exec_builtin):
        """Canceling keyboard entry results in doing absolutely nothing."""
        ipwww_search.context_menu('video', 'edit', 'term1')
        p_remove.assert_not_called()
        p_replace.assert_not_called()
        p_exec_builtin.assert_not_called()

    @patch('resources.lib.ipwww_search.SearchHistory.clear')
    def test_clear_history(self, p_clear, p_exec_builtin):
        ipwww_search.context_menu('video', 'clear')
        p_clear.assert_called_once()
        self.assertEqual('Container.Refresh', p_exec_builtin.call_args.args[0])
