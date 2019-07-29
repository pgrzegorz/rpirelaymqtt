import sys
import os
from unittest.mock import Mock
from unittest import TestCase
sys.modules['RPi.GPIO'] = Mock()
import relayboard

def get_fixture(name):
    return os.path.join(os.path.dirname(__file__), 'fixtures', name)


class RelayBoardTestCircular(TestCase):
    def setUp(self):
        self.relayb = relayboard.RelayBoard(filename=get_fixture('circular.json'))
    
    def test_circular_dependency(self):
        result = self.relayb.process("relay1","ON")
        self.assertFalse(result)

class RelayBoardTestDoubled(TestCase):
    def setUp(self):
        self.relayb = relayboard.RelayBoard(filename=get_fixture('doubled.json'))

    def test_doubled_dependency(self):
        result = self.relayb.process("relay1","ON")
        self.assertFalse(result)

class RelayBoardTestState1(TestCase):
    def setUp(self):
        self.relayb = relayboard.RelayBoard(filename=get_fixture('one_up_all_up_1.json'))
      
    def test_dep(self):
        result = self.relayb.process("relay1","ON")
        self.assertTrue(result)
        for name in self.relayb.config:
            self.assertEqual(self.relayb.config[name]["state"],"ON")

class RelayBoardTestState2(TestCase):
    def setUp(self):
        self.relayb = relayboard.RelayBoard(filename=get_fixture('one_up_all_up_2.json'))

    def test_dep(self):
        result = self.relayb.process("relay1","ON")
        self.assertTrue(result)
        for name in self.relayb.config:
            self.assertEqual(self.relayb.config[name]["state"],"ON")


if __name__ == '__main__':
    unittest.main()
