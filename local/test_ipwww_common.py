from support import fixtures
fixtures.global_setup()

from unittest import TestCase
from unittest.mock import patch, MagicMock, call

import xbmcgui

from resources.lib import ipwww_common


class TestProgressDialog(TestCase):
    def test_create_dlg(self):
        dlg = ipwww_common.ProgressDlg("My Heading")
        self.assertIsInstance(dlg, xbmcgui.DialogProgressBG)

    @patch('xbmcgui.DialogProgressBG.create')
    @patch('xbmcgui.DialogProgressBG.close')
    def test_context_manager(self, p_close, p_create):
        with ipwww_common.ProgressDlg("My Heading"):
            p_create.assert_called_once()
            p_close.assert_not_called()
        p_close.assert_called_once()
