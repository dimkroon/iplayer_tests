from tests.support import fixtures
fixtures.global_setup()

import unittest

setUpModule = fixtures.setup_local_tests()
tearDownModule = fixtures.tear_down_local_tests()


from resources.lib import ipwww_progress

from tests.support.testutils import open_json


class PlayStateEnum(unittest.TestCase):
    def test_instantiate_playstate(self):
        with self.assertRaises(NotImplementedError):
            ps = ipwww_progress.PlayState()

    def test_changes_value(self):
        ipwww_progress.PlayState.PLAYING = 1
        p = getattr(ipwww_progress.PlayState, 'PLAYING')
        print(p)