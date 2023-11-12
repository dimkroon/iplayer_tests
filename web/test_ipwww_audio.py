from support import fixtures
fixtures.global_setup()

import requests
import unittest
from unittest.mock import patch

from support import testutils
from resources.lib import ipwww_radio, ipwww_common
from resources.lib import ipwww_video


setUp = fixtures.setup_web_test()



@patch('resources.lib.ipwww_common.AddMenuEntry')
class GenericListings(unittest.TestCase):
    def test_list_listen_list(self, patched_add):
        ipwww_radio.ListListenList(True)
        patched_add.assert_called()


class LiveChannels(unittest.TestCase):
    channels = [('bbc_radio_one', 'BBC Radio 1'),
        ('bbc_radio_one_dance', 'BBC Radio 1 Dance'),
        ('bbc_radio_one_relax', 'BBC Radio 1 Relax'),
        ('bbc_1xtra', 'BBC Radio 1Xtra'),
        ('bbc_radio_two', 'BBC Radio 2'),
        ('bbc_radio_three', 'BBC Radio 3'),
        ('bbc_radio_fourfm', 'BBC Radio 4'),
        ('bbc_radio_fourlw', 'BBC Radio 4 LW'),
        ('bbc_radio_four_extra', 'BBC Radio 4 Extra'),
        ('bbc_radio_five_live', 'BBC Radio 5 Live'),
        ('bbc_radio_five_live_sports_extra', 'BBC Radio 5 Sports Extra'),
        ('bbc_6music', 'BBC Radio 6 Music'),
        ('bbc_asian_network', 'BBC Asian Network'),
        ('bbc_world_service', 'BBC World Service'),
        ('bbc_radio_scotland_fm', 'BBC Radio Scotland'),
        ('bbc_radio_scotland_mw', 'BBC Radio Scotland Extra'),
        ('bbc_radio_orkney', 'BBC Radio Orkney'),
        ('bbc_radio_shetland', 'BBC Radio Shetland'),
        ('bbc_radio_nan_gaidheal', u'BBC Radio nan Gàidheal'),
        ('bbc_radio_ulster', 'BBC Radio Ulster'),
        ('bbc_radio_foyle', 'BBC Radio Foyle'),
        ('bbc_radio_wales_fm', 'BBC Radio Wales'),
        ('bbc_radio_wales_am', 'BBC Radio Wales Extra'),
        ('bbc_radio_cymru', 'BBC Radio Cymru'),
        ('bbc_radio_cymru_2', 'BBC Radio Cymru 2'),
        ('cbeebies_radio', 'CBeebies Radio'),
        ('bbc_radio_berkshire', 'BBC Radio Berkshire'),
        ('bbc_radio_bristol', 'BBC Radio Bristol'),
        ('bbc_radio_cambridge', 'BBC Radio Cambridgeshire'),
        ('bbc_radio_cornwall', 'BBC Radio Cornwall'),
        ('bbc_radio_coventry_warwickshire', 'BBC Coventry & Warwickshire'),
        ('bbc_radio_cumbria', 'BBC Radio Cumbria'),
        ('bbc_radio_derby', 'BBC Radio Derby'),
        ('bbc_radio_devon', 'BBC Radio Devon'),
        ('bbc_radio_essex', 'BBC Essex'),
        ('bbc_radio_gloucestershire', 'BBC Radio Gloucestershire'),
        ('bbc_radio_guernsey', 'BBC Radio Guernsey'),
        ('bbc_radio_hereford_worcester', 'BBC Hereford & Worcester'),
        ('bbc_radio_humberside', 'BBC Radio Humberside'),
        ('bbc_radio_jersey', 'BBC Radio Jersey'),
        ('bbc_radio_kent', 'BBC Radio Kent'),
        ('bbc_radio_lancashire', 'BBC Radio Lancashire'),
        ('bbc_radio_leeds', 'BBC Radio Leeds'),
        ('bbc_radio_leicester', 'BBC Radio Leicester'),
        ('bbc_radio_lincolnshire', 'BBC Radio Lincolnshire'),
        ('bbc_london', 'BBC Radio London'),
        ('bbc_radio_manchester', 'BBC Radio Manchester'),
        ('bbc_radio_merseyside', 'BBC Radio Merseyside'),
        ('bbc_radio_newcastle', 'BBC Newcastle'),
        ('bbc_radio_norfolk', 'BBC Radio Norfolk'),
        ('bbc_radio_northampton', 'BBC Radio Northampton'),
        ('bbc_radio_nottingham', 'BBC Radio Nottingham'),
        ('bbc_radio_oxford', 'BBC Radio Oxford'),
        ('bbc_radio_sheffield', 'BBC Radio Sheffield'),
        ('bbc_radio_shropshire', 'BBC Radio Shropshire'),
        ('bbc_radio_solent', 'BBC Radio Solent'),
        ('bbc_radio_solent_west_dorset', 'BBC Radio Solent Dorset'),
        ('bbc_radio_somerset_sound', 'BBC Somerset'),
        ('bbc_radio_stoke', 'BBC Radio Stoke'),
        ('bbc_radio_suffolk', 'BBC Radio Suffolk'),
        ('bbc_radio_surrey', 'BBC Surrey'),
        ('bbc_radio_sussex', 'BBC Sussex'),
        ('bbc_tees', 'BBC Tees'),
        ('bbc_three_counties_radio', 'BBC Three Counties Radio'),
        ('bbc_radio_wiltshire', 'BBC Wiltshire'),
        ('bbc_wm', 'BBC WM'),
        ('bbc_radio_york', 'BBC Radio York')]

    @patch('xbmcplugin.setResolvedUrl')
    def test_all_live_channels_authenticated(self, patched_set_resolve):
        for chan_path, _ in self.channels:
            ipwww_radio.AddAvailableLiveStreamItem('', chan_path, '')
            patched_set_resolve.assert_called_once()
            patched_set_resolve.reset_mock()

    @patch('xbmcplugin.setResolvedUrl')
    def test_all_live_channels_with_expired_cookies(self, patched_set_resolve):
        for chan_path, _ in self.channels:
            with patch('resources.lib.ipwww_common.cookie_jar', new=testutils.ExpiredCookieJar()):
                ipwww_radio.AddAvailableLiveStreamItem('', chan_path, '')
                patched_set_resolve.assert_called_once()
                patched_set_resolve.reset_mock()

    @patch('xbmcplugin.setResolvedUrl')
    def test_all_live_channels_not_authenticated(self, patched_set_resolve):
        for chan_path, _ in self.channels:
            with patch('resources.lib.ipwww_common.cookie_jar', new=testutils.NotLoggedInCookieJar()):
                ipwww_radio.AddAvailableLiveStreamItem('', chan_path, '')
                patched_set_resolve.called_once()
                patched_set_resolve.reset_mock()
