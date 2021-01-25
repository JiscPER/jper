import unittest
from standalone_octopus.modules.identifiers import pmid

class TestPMID(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_01_normalise_PMID(self):
        identifier_1 = "PMID12345"
        identifier_2 = "PMID:12345"
        identifier_1 = pmid.normalise(identifier_1)
        identifier_2 = pmid.normalise(identifier_2)
        assert identifier_1 == "12345", identifier_1
        assert identifier_2 == "12345", identifier_2

    def test_02_valid_PMID(self):
        identifier = "12345"
        identifier = pmid.normalise(identifier)
        assert identifier == "12345"

    def test_03_invalid_PMID(self):
        identifier = "ImnotavalidPMID"
        self.assertRaises(ValueError, pmid.normalise, identifier)

if __name__ == '__main__':
    unittest.main()


