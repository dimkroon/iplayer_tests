
from unittest import TestCase
from unittest.mock import patch

import xbmc

from support.fixtures import keyb_mock


class TestKeyboardMock(TestCase):
    def test_keyb_mock_single_value(self):
        with patch('xbmc.Keyboard', new_callable=keyb_mock, text='user entry', confirmed=False):
            kb = xbmc.Keyboard()
            # Returns the same values each call.
            kb.doModal()
            self.assertEqual('user entry', kb.getText())
            self.assertIs(False, kb.isConfirmed())
            kb.doModal()
            self.assertEqual('user entry', kb.getText())
            self.assertIs(False, kb.isConfirmed())

    def test_keyb_mock_multi_value(self):
        with patch('xbmc.Keyboard', new_callable=keyb_mock, text=('1', '2'), confirmed=(True, False)):
            kb = xbmc.Keyboard()
            # Returns the next value each call.
            self.assertNotEquals('1', kb.getText())
            kb.doModal()
            self.assertEqual('1', kb.getText())
            self.assertIs(True, kb.isConfirmed())
            kb.doModal()
            self.assertEqual('2', kb.getText())
            self.assertIs(False, kb.isConfirmed())

    def test_check_instatiation(self):
        with patch('xbmc.Keyboard', new_callable=keyb_mock, text='1') as mkb:
            xbmc.Keyboard('init text', 'heading', True)
            mkb.isConfirmed.assert_called_once_with('init text', 'heading', True)