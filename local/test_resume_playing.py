from tests.support import fixtures
fixtures.global_setup()

import unittest

setUpModule = fixtures.setup_local_tests()
tearDownModule = fixtures.tear_down_local_tests()


from resources.lib import ipwww_resume

from tests.support.testutils import open_json


class ResolveUrn(unittest.TestCase):
    def test_resolve_valid_tv_urn(self):
        url = ipwww_resume.resolve_urn('urn:bbc:tv:episode:m001s8qd')
        self.assertEqual('https://www.bbc.co.uk/iplayer/episode/m001s8qd', url)

    def test_resolve_invalid_tv_url(self):
        self.assertRaises(ValueError, ipwww_resume.resolve_urn, 'urn:bbc:iplayer:some:programme')


class Resume(unittest.TestCase):
    def test_parse_resume(self):
        data = open_json('html/watching.json')
        results = list(ipwww_resume.parse_watching(data))
        pass


class PlayStateEnum(unittest.TestCase):
    def test_instantiate_playstate(self):
        with self.assertRaises(NotImplementedError):
            ps = ipwww_resume.PlayState()

    def test_changes_value(self):
        with self.assertRaises(NotImplementedError):
            ipwww_resume.PlayState.PLAYING = 1
            p = getattr(ipwww_resume.PlayState, 'PLAYING')
            print(p)