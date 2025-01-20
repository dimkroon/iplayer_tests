
from support import fixtures
fixtures.global_setup()

import os.path

from unittest import TestCase
from unittest.mock import patch

from support.fixtures import keyb_mock
from resources.lib import ipwww_search


def test_history():
    return {
        'video': {
            'term1': {'created': 1234, 'last_used': 1236},
            'term2': {'created': 1235, 'last_used': 1237}
        },
        'audio': {
            'term3': {'created': 1241, 'last_used': 1243},
            'term4': {'created': 1242, 'last_used': 1244}
        }
    }


def clear_history_file(_):
    # clear file
    f = ipwww_search.SearchHistory('video')
    path = f.full_path
    if os.path.isfile(path):
        os.remove(path)


class TestSearchTermsFile(TestCase):
    setUp = clear_history_file

    def test_append(self):
        f = ipwww_search.SearchHistory('video')
        # Empty list when search file does not exist
        self.assertListEqual([], list(f))
        # Add to empty list
        with patch('resources.lib.ipwww_search.time.time', return_value=1234):
            f.append('blabla')
        self.assertEqual([('blabla', {'created': 1234, 'last_used': 1234})], list(f))
        # Add to non-empty list
        with patch('resources.lib.ipwww_search.time.time', return_value=1235):
            f.append('bibi')
        self.assertEqual([('bibi', {'created': 1235, 'last_used': 1235}),
                          ('blabla', {'created': 1234, 'last_used': 1234})
                          ], list(f))
        # Add already existing search term
        with patch('resources.lib.ipwww_search.time.time', return_value=1236):
            f.append('blabla')
        self.assertEqual([('bibi', {'created': 1235, 'last_used': 1235}),
                          ('blabla', {'created': 1234, 'last_used': 1234})
                          ], list(f))
        # Add empty string
        f.append('')
        self.assertEqual([('bibi', {'created': 1235, 'last_used': 1235}),
                          ('blabla', {'created': 1234, 'last_used': 1234})
                          ], list(f))

        # Terms are saved to disk
        f = ipwww_search.SearchHistory('video')
        self.assertEqual([('bibi', {'created': 1235, 'last_used': 1235}),
                          ('blabla', {'created': 1234, 'last_used': 1234})
                          ], list(f))

        # Audio has its own list of search terms
        f = ipwww_search.SearchHistory('audio')
        self.assertListEqual([], list(f))

        with patch('resources.lib.ipwww_search.time.time', return_value=1237):
            f.append('zaza')
        self.assertEqual([('zaza', {'created': 1237, 'last_used': 1237})
                          ], list(f))

    def test_remove(self):
        f = ipwww_search.SearchHistory('video')
        with patch('resources.lib.ipwww_search.time.time', return_value=1234):
            f.append('term1')
        with patch('resources.lib.ipwww_search.time.time', return_value=1235):
            f.append('term2')
        self.assertListEqual([('term2', {'created': 1235, 'last_used': 1235}),
                              ('term1', {'created': 1234, 'last_used': 1234})
                              ], list(f))

        # Remove a term
        f.remove('term1')
        self.assertListEqual([('term2', {'created': 1235, 'last_used': 1235})
                              ], list(f))

        # List is saved to disk
        f = ipwww_search.SearchHistory('video')
        self.assertListEqual([('term2', {'created': 1235, 'last_used': 1235})
                              ], list(f))

        # Removing a non-existing term should fail silently
        f.remove('term3')
        self.assertListEqual([('term2', {'created': 1235, 'last_used': 1235})
                              ], list(f))

    def test_replace(self):
        f = ipwww_search.SearchHistory('video')
        with patch('resources.lib.ipwww_search.time.time', return_value=1234):
            f.append('term1')
        with patch('resources.lib.ipwww_search.time.time', return_value=1235):
            f.append('term2')
        self.assertListEqual([('term2', {'created': 1235, 'last_used': 1235}),
                              ('term1', {'created': 1234, 'last_used': 1234})
                              ], list(f))

        with patch('resources.lib.ipwww_search.time.time', return_value=1236):
            f.replace('term1', 'term3')
        self.assertListEqual([('term2', {'created': 1235, 'last_used': 1235}),
                              ('term3', {'created': 1234, 'last_used': 1234})
                              ], list(f))
        # Change is stored to file
        f = ipwww_search.SearchHistory('video')
        self.assertListEqual([('term2', {'created': 1235, 'last_used': 1235}),
                              ('term3', {'created': 1234, 'last_used': 1234})
                              ], list(f))
        self.assertRaises(ValueError, f.replace, 'term1', 'new term')

    def test_clear(self):
        fv = ipwww_search.SearchHistory('video')
        fa = ipwww_search.SearchHistory('audio')
        with patch('resources.lib.ipwww_search.time.time', return_value=1234):
            fv.append('vterm1')
        with patch('resources.lib.ipwww_search.time.time', return_value=1235):
            fv.append('vterm2')
        with patch('resources.lib.ipwww_search.time.time', return_value=1236):
            fa.append('aterm1')
        with patch('resources.lib.ipwww_search.time.time', return_value=1237):
            fa.append('aterm2')
        self.assertListEqual([('vterm2', {'created': 1235, 'last_used': 1235}),
                              ('vterm1', {'created': 1234, 'last_used': 1234})
                              ], list(fv))
        self.assertListEqual([('aterm2', {'created': 1237, 'last_used': 1237}),
                              ('aterm1', {'created': 1236, 'last_used': 1236})
                              ], list(fa))
        fv.clear()
        self.assertListEqual([], list(fv))
        self.assertListEqual([('aterm2', {'created': 1237, 'last_used': 1237}),
                              ('aterm1', {'created': 1236, 'last_used': 1236})
                              ], list(fa))
        # re-open file
        fv = ipwww_search.SearchHistory('video')
        fa = ipwww_search.SearchHistory('audio')
        self.assertListEqual([], list(fv))
        self.assertListEqual([('aterm2', {'created': 1237, 'last_used': 1237}),
                              ('aterm1', {'created': 1236, 'last_used': 1236})
                              ], list(fa))

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

    def test_update_last_used(self):
        f = ipwww_search.SearchHistory('video')
        with patch('resources.lib.ipwww_search.time.time', return_value=1234):
            f.append('term1')
        with patch('resources.lib.ipwww_search.time.time', return_value=1235):
            f.append('term2')
        with patch('resources.lib.ipwww_search.time.time', return_value=1236):
            f.append('term3')
        self.assertListEqual([('term3', {'created': 1236, 'last_used': 1236}),
                              ('term2', {'created': 1235, 'last_used': 1235}),
                              ('term1', {'created': 1234, 'last_used': 1234})
                              ], list(f))
        with patch('resources.lib.ipwww_search.time.time', return_value=1237):
            f.update_last_used('term2')
        # Term2 is now on top of the list and last_used value is updated
        self.assertListEqual([('term2', {'created': 1235, 'last_used': 1237}),
                              ('term3', {'created': 1236, 'last_used': 1236}),
                              ('term1', {'created': 1234, 'last_used': 1234})
                              ], list(f))

        # Keyword not present
        self.assertRaises(ValueError, f.update_last_used, 'kdjfhrm')

    def test_invalid_file_format(self):
        """Test a partly corrupted file, e.g a file in a format from a previous version
        """

        with patch('resources.lib.ipwww_search.SearchHistory._read_file', return_value={
                'video': ['v1', 'v2'],
                'audio': ['a1, a2']}):
            f = ipwww_search.SearchHistory('video')
        self.assertRaises(RuntimeError, list, f)
        # Check video section is cleared after the error
        f = ipwww_search.SearchHistory('video')
        self.assertEqual(list(f), [])


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
        clear_history_file(self)
        self.li_store = fixtures.ListItemCollector()
        self.p = patch('xbmcplugin.addDirectoryItem', self.li_store)
        self.p.start()

    def tearDown(self):
        self.p.stop()

    @patch('resources.lib.ipwww_search.SearchHistory._read_file', return_value=test_history())
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

    @patch('resources.lib.ipwww_search.SearchHistory._read_file', return_value={'video':{}})
    def test_list_without_saved_items(self, _, p_add_term, p_do_search):
        # Without search term
        with patch('xbmc.Keyboard', new_callable=keyb_mock, text='new term'):
            ipwww_search.list_search_terms('video', 130, keyword=None)
            self.assertEqual(0, len(self.li_store))
            p_do_search.assert_called_once_with('new term')
            p_add_term.assert_called_once_with('new term')

        p_add_term.reset_mock()
        p_do_search.reset_mock()

@patch('resources.lib.ipwww_search.SearchHistory.append')
@patch('xbmc.executebuiltin')
class NewSearch(TestCase):
    setUp = clear_history_file

    @patch('resources.lib.ipwww_search.SearchHistory._read_file', return_value={'video': {}})
    def test_new_search(self, _, p_exec_builtin, p_append):
        with patch('xbmc.Keyboard', keyb_mock(text='new term')):
            ipwww_search.new_search('video', 130)
            p_append.assert_called_once_with('new term')
            p_exec_builtin.assert_called_once()
            self.assertTrue(p_exec_builtin.call_args.args[0].startswith('Container.Update'))

    @patch('resources.lib.ipwww_search.SearchHistory._read_file', return_value=test_history())
    def test_keyboard_canceled(self, _, p_exec_builtin, p_append):
        """On keyboard cancel the saved list of search terms should be shown."""
        with patch('xbmc.Keyboard', keyb_mock(text='new term', confirmed=False)):
            ipwww_search.list_search_terms('video', 130)
            p_append.assert_not_called()
            p_exec_builtin.assert_not_called()

    @patch('resources.lib.ipwww_search.SearchHistory._read_file', return_value=test_history())
    def test_keyboard_empty_string(self, _, p_exec_builtin, p_append):
        """Empty keyboard input should be handled the same as keyboard cancel."""
        with patch('xbmc.Keyboard', keyb_mock(text='')):
            ipwww_search.list_search_terms('video', 130)
            p_append.assert_not_called()
            p_exec_builtin.assert_not_called()


# noinspection PyMethodMayBeStatic
@patch('resources.lib.ipwww_search.SearchHistory.update_last_used')
@patch('resources.lib.ipwww_search.SearchHistory._read_file', return_value=test_history())
class DoSearch(TestCase):
    setUp = clear_history_file

    def test_search_video(self, _, p_update_last_used):
        # check the last entered keyword is on top of the list.
        with patch('resources.lib.ipwww_video.Search') as p_video_search:
            ipwww_search.do_search('video', 'term2')
        p_update_last_used.assert_called_once_with('term2')
        p_video_search.assert_called_once_with('term2')

    def test_search_audio(self, _, p_update_last_used):
        # check the last entered keyword is on top of the list.
        with patch('resources.lib.ipwww_radio.Search') as p_radio_search:
            ipwww_search.do_search('audio', 'term3')
        p_update_last_used.assert_called_once_with('term3')
        p_radio_search.assert_called_once_with('term3')


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

    @patch('resources.lib.ipwww_search.SearchHistory.replace')
    @patch('resources.lib.ipwww_search.SearchHistory.remove')
    @patch('resources.lib.ipwww_search.SearchHistory.clear')
    def test_invalid_action(self, p_clear, p_remove, p_replace, p_exec_builtin):
        """Fail silently on an unknown action."""
        ipwww_search.context_menu('video', 'notAnAction')
        p_replace.assert_not_called()
        p_remove.assert_not_called()
        p_clear.assert_not_called()
        self.assertEqual('Container.Refresh', p_exec_builtin.call_args.args[0])

    @patch('resources.lib.ipwww_search.SearchHistory._read_file', return_value={'video': []})
    @patch('resources.lib.ipwww_radio.Search')
    def test_search_radio_when_content_type_is_audio(self, p_do_radio_search, _, __, p_do_search):
        """When keyboard entry is requested on radio search, assert the correct
        search function is being called
        """
        with patch('xbmc.Keyboard', new_callable=keyb_mock, text='blabla'):
            ipwww_search.list_search_terms('audio', 140)
            p_do_search.assert_not_called()
            p_do_radio_search.assert_called_once_with('blabla')