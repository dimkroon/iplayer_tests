# ----------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2022-2023 Dimitri Kroon.
#  This file is part of plugin.video.viwx.
#  SPDX-License-Identifier: GPL-2.0-or-later
#  See LICENSE.txt
# ----------------------------------------------------------------------------------------------------------------------

from __future__ import annotations
import os
import sys
import re
from collections.abc import Iterable
from unittest.mock import patch, Mock

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

patch_g = None


def global_setup():
    """Fixture required for all test.
    Ensure this is imported and called in every test module first thing. At least before
    importing any other module from the project or other kodi related module.

    As it is global for all tests there is no need to tear down.

    """
    global patch_g
    if patch_g is None:
        # Ensure that kodi's special://profile refers to a predefined folder. Just in case
        # some code want to write, whether intentional or not.
        profile_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'addon_profile_dir'))
        patch_g = patch('xbmcaddon.Addon.getAddonInfo',
                         new=lambda self, item: profile_dir if item == 'profile' else '')
        patch_g.start()

        xbmcvfs.translatePath = translate_path_mock
        xbmcaddon.Addon.getLocalizedString = localise_mock

        # Define an addon handle
        if len(sys.argv) == 1:
            sys.argv.append('1')
        else:
            sys.argv[1] = '1'

        # Define some settings.
        def addon_setting(self, key):
            import credentials
            if key in ('bbc_id_enabled', 'bbc_id_autologin'):
                return 'true'
            if key == 'bbc_id_username':
                return credentials.uname
            if key == 'bbc_id_password':
                return credentials.passw
            if key in('catchup_source', 'subtitle_source', 'radio_source'):
                return '0'

        xbmcaddon.Addon.getSetting = addon_setting

        # Use an xbmcgui.ListItem that stores the values which have been set.
        patch_listitem()


patch_1 = None


class RealWebRequestMadeError(Exception):
    pass


def setup_local_tests():
    """Module level fixture for all local tests. Ensures that no unintentional real
    web requests can occur.

    """
    global patch_1
    patch_1 = patch('requests.sessions.Session.send', side_effect=RealWebRequestMadeError)
    patch_1.start()


def tear_down_local_tests():
    global patch_1

    if patch_1:
        patch_1.stop()
        patch_1 = None


credentials_set = False

def set_credentials() -> None:
    # IMPORTANT: import here, after global setup has been executed and paths to addon profile_dir are set!!
    from resources.lib import ipwww_common
    ipwww_common.SignInBBCiD()
    global credentials_set
    credentials_set = True


def setup_web_test(*args):
    # Sign in once per test run.
    if not credentials_set:
        set_credentials()


def patch_listitem():
    import xbmcgui

    class LI(xbmcgui.ListItem):
        def __init__(self, label: str = "",
                     label2: str = "",
                     path: str = "",
                     offscreen: bool = False) -> None:
            super().__init__()
            assert isinstance(label, str)
            assert isinstance(label2, str)
            assert isinstance(path, str)
            assert isinstance(offscreen, bool)
            self._label = label
            self._label2 = label2
            self._path = path
            self._offscreen = offscreen
            self._is_folder = False
            self._art = {}
            self._info = {}
            self._props = {}

        def getLabel(self) -> str:
            return self._label

        def getLabel2(self) -> str:
            return self._label2

        def setLabel(self, label: str) -> None:
            assert isinstance(label, str), "Argument 'label' must be a string."
            self._label = label

        def setLabel2(self, label: str) -> None:
            assert isinstance(label, str), "Argument 'label' must be a string."
            self._label2 = label

        def setArt(self, dictionary: dict[str, str]) -> None:
            assert isinstance(dictionary, dict), "Argument 'dictionary' must be a dict."
            self._art.update(dictionary)

        def setIsFolder(self, isFolder: bool) -> None:
            assert isinstance(isFolder, bool), "Argument 'isFolder' must be a boolean."
            self._is_folder = isFolder

        def setInfo(self, type: str, infoLabels: dict[str, str]) -> None:
            assert isinstance(type, str), "Argument 'type' must be a string."
            assert isinstance(infoLabels, dict), "Argument 'infoLabels' must be a dict."
            type = type.lower()
            assert type in ('video', 'audio', 'music', 'pictures', 'game')
            info_dict = self._info.setdefault(type, {})
            info_dict.update(infoLabels)

        def setProperty(self, key: str, value: str) -> None:
            assert isinstance(key, str), "Argument 'key' must be a string."
            assert isinstance(value, str), "Argument 'value' must be a string."
            self._props[key.lower()] = value

        def setProperties(self, dictionary: dict[str, str]) -> None:
            assert isinstance(dictionary, dict), "Argument 'dictionary' must be a dict."
            self._props.update(dictionary)

        def getProperty(self, key: str) -> str:
            assert isinstance(key, str), "Argument 'key' must be a string."
            return self._props[key.lower()]

        def setPath(self, path: str) -> None:
            assert isinstance(path, str), "Argument 'path' must be a string."
            self._path = path

        def setMimeType(self, mimetype: str) -> None:
            assert isinstance(mimetype, str), "Argument 'mimetype' must be a string."
            self._mimetype = mimetype

        def setContentLookup(self, enable: bool) -> None:
            assert isinstance(enable, bool), "Argument 'enable' must be a boolean."
            self._content_lookup = enable

        def setSubtitles(self, subtitleFiles: list[str]) -> None:
            assert isinstance(subtitleFiles, (list, tuple)), "Argument 'subtitleFiles' must be a tuple or a list."
            self._subtitles = subtitleFiles

        def getPath(self) -> str:
            return self._path

    xbmcgui.ListItem = LI


class ListItemCollector:
    """Objected intended to patch xbmcplugin.addDirectoryItem, store all calls
    and provide easier access than a standard Mock."""
    def __init__(self):
        self._call_args = []

    @property
    def calls(self) -> list[tuple[str, xbmcgui.ListItem, bool]]:
        return self._call_args

    @property
    def paths(self) -> list[str]:
        return [call[0] for call in self._call_args]

    def path(self, index) -> str:
        return self._call_args[index][0]

    @property
    def list_items(self) -> list[xbmcgui.ListItem]:
        return [call[1] for call in self._call_args]

    def list_item(self, index) -> xbmcgui.ListItem:
        return self._call_args[index][1]

    def __call__(self, handle:int, url: str, listitem=xbmcgui.ListItem, isFolder=bool):
        self._call_args.append((url, listitem, isFolder))

    def __len__(self):
        return len(self._call_args)

    def __iter__(self):
        return iter(self.list_items)

    def __getitem__(self, item):
        return self._call_args[item]


def translate_path_mock(path: str):
    """Translate 'special://' paths to folders in a directory named 'kodifs' in the top
    test directory, assuming this file is in a folder directly under test/.

    It is not accurate enough to reliably translate every possible special path, but it's
    enough to suit our needs right now.
    """
    if not path.startswith('special://'):
        return path
    special_path = path[10:]
    test_base = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'kodifs'))
    special_base_dir = special_path.split('/', 1)[0]
    os.makedirs(os.path.join(test_base, special_base_dir), exist_ok=True)
    local_dir = os.path.join(test_base, special_path)
    return local_dir


def localise_mock(self, str_id):
    """Return the text corresponding to str_id in the original language file.
    Returns only the text of the first line in the file.

    """
    pattern = f'msgctxt "#{str_id}"\nmsgid "([^"]*)"'
    test_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '../'))
    lang_file = os.path.join(
        test_dir,
        '../plugin.video.iplayerwww/resources/language/resource.language.en_gb/strings.po')
    with open(lang_file) as f:
        lang_texts = f.read()
    match = re.search(pattern, lang_texts)
    if match:
        return match[1]
    return ''


def keyb_mock(text: str | Iterable[str], confirmed: bool | Iterable[bool] = True):
    """Return a Mock object to replace xbmc.Keyboards that, when called, returns instance
    of KeybMock. KeybMock acts as mocked instances of xbmc.Keyboard that returns text and
    isConfirmed as defined by parameters `text` and `confirmed`.
    KeybMock derives from unittest's Mock and as such all methods, like isConfirmed() and
    getText(), are Mocks themselves and their calls can be examined like any other Mock.

    Like Kodi's keyboard, each new instance of the mocked keyboard must first be opened
    with `doModal()` before `isConfirmed()` and `getText()` will return the specified values.

    When `text` and/or `confirmed` are sequences of values, each time after a keyboard is
    opened with `doModal()` the next value in the sequence will be returned, regardless of
    whether it is on the same keyboard object, or a new instance.
    When a sequence is exhausted, each subsequent call will return the last value.

    When testing code that uses keyboard entry you can patch xbmc.Keybaord by either pass the
    return value of `keyb_mock(...)` to parameter `new`, or pass `keyb_mock` to `new_callable`.
    Use the latter if patch is used as a decorator and you want to inspect the instantiation
    of keyboards.

    example::

        @patch('xbmc.Keyboard', new=fixtures.keyb_mock(text='1234'))
        def test_log_in(self):
            log_in()    # Function that opens a keyboard with heading 'Enter password'.

        @patch('xbmc.Keyboard', new_callable=fixtures.keyb_mock, text='1234')
        def test_log_in(self, patched_keyboard):
            log_in()        # Function that opens a keyboard with heading 'Enter password'.
            patched_keyboard.assert_called_once_with(heading="Enter password")

        def test_log_in(self):
            with patch('xbmc.Keyboard', keyb_mock(text='1234')) as patched_keyb:
                log_in()       # Function that opens a keyboard with heading 'Enter password'.
                patched_keyboard.assert_called_once_with(heading="Enter password")


    :param text: The text, or sequence of texts Keyboard.getText() is to return.
    :param confirmed: [Opt] The status, or sequence of statuses Keyboard.isConfirmed()
        will return. Default is True.

    """
    orig_keyboard = xbmc.Keyboard

    if isinstance(text, str):
        _text_iter = iter((text,))
    else:
        try:
            _text_iter = iter(text)
        except TypeError:
            raise TypeError('Mock Error: Keyboard texts must be either a single string, or a sequence of strings')

    if isinstance(confirmed, bool):
        _confirmed_iter = iter((confirmed,))
    else:
        try:
            _confirmed_iter = iter(confirmed)
        except TypeError:
            raise TypeError(
                "Mock Error: Keyboard 'confirmed' value must be either a single bool, or a sequence of bools")
    _last_text = None
    _last_confirm = None

    class KeybMock(Mock):
        def __init__(self, line, heading, hidden, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.init_line = line
            self.heading = heading
            self.hidden = hidden
            # Create as instance attributes to ensure each KeybMock instance
            # has its own return_value.
            self.getText = Mock(return_value='')
            self.isConfirmed = Mock(return_value=False)

        def doModal(self, _: int = 0):
            """Load new return values."""
            nonlocal _last_text
            nonlocal _last_confirm

            try:
                new_txt = next(_text_iter)
                if not isinstance(new_txt, str):
                    raise ValueError(f"Mock Error: All keyboard texts must be of "
                                     f"type str, not '{type(new_txt).__name__}'")
                self.getText.return_value = _last_text = new_txt
            except StopIteration:
                if _last_text is None:
                    raise ValueError('Mock Error: Keyboard has an empty sequence of texts')
                self.getText.return_value = _last_text

            try:
                new_conf = next(_confirmed_iter)
                if not isinstance(new_conf, bool):
                    raise ValueError(f"Mock Error: All 'isConfirmed' values must be of "
                                     f"type bool, not '{type(new_conf).__name__}'")
                self.isConfirmed.return_value = _last_confirm = new_conf
            except StopIteration:
                if _last_confirm is None:
                    raise ValueError("Mock Error: Keyboard has an empty sequence of 'isConfirmed' values")
                self.isConfirmed.return_value = _last_confirm

    return Mock(side_effect=lambda line='', heading='', hidden=False: KeybMock(line=line,
                                                                               heading=heading,
                                                                               hidden=hidden,
                                                                               spec=orig_keyboard))
