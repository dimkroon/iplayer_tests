from tests.support import fixtures
fixtures.global_setup()

import unittest

setUpModule = fixtures.setup_local_tests()
tearDownModule = fixtures.tear_down_local_tests()


from resources.lib import ipwww_progress

from tests.support.testutils import open_json


class PlayStateEnum(unittest.TestCase):
    """Somehow PlayState has never become an Enum"""
    def test_instantiate_playstate(self):
        ps = ipwww_progress.PlayState()
        self.assertGreater(ps.UNDEFINED, 10000)
        self.assertGreater(ps.PLAYING, 10000)
        self.assertGreater(ps.STOPPED, 10000)
        self.assertGreater(ps.PAUSED, 10000)
