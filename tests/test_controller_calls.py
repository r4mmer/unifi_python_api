import json
import sys
from os.path import isfile, dirname, join as pjoin
import unittest

from unifi_client import UnifiClient

config_file = pjoin(dirname(__file__), 'config.json')
if not isfile(config_file):
    print('Need configuration file (tests/config.json)')
    sys.exit(1)

config = None
with open(config_file, 'r') as fh:
    config = json.load(fh)

class TestAbstractUnifiSession(unittest.TestCase):
    def test_login(self):
        client = UnifiClient(**config)
        client.login()
        self.assertEqual(True, client.logged_in)

if __name__ == '__main__':
    unittest.main()
