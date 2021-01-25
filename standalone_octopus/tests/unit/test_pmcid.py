import unittest
from standalone_octopus.modules.identifiers import pmcid

class TestPMCID(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_01_normalise_PMCID(self):
        identifier = "123456"
        identifier = pmcid.normalise(identifier)
        assert identifier == "PMC123456", identifier

    def test_02_valid_PMCID(self):
        identifier = "PMC123456"
        identifier = pmcid.normalise(identifier)
        assert identifier == "PMC123456"

    def test_03_invalid_PMCID(self):
        identifier = "ImnotaPMCID"
        self.assertRaises(ValueError, pmcid.normalise, identifier)

if __name__ == '__main__':
    unittest.main()
