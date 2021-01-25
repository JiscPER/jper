import unittest
from standalone_octopus.modules.identifiers import doi

class TestDOI(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_01_normalise_DOI(self):
        identifier = "doi:10.1371/journal.pone.0048753"
        identifier = doi.normalise(identifier)
        assert identifier == "10.1371/journal.pone.0048753"

    def test_02_valid_DOI(self):
        identifier = "10.1371/journal.pone.0048753"
        identifier = doi.normalise(identifier)
        assert identifier == "10.1371/journal.pone.0048753"

    def test_03_invalid_DOI(self):
        identifier = "ImnotaDOI"
        self.assertRaises(ValueError, doi.normalise, identifier)

if __name__ == '__main__':
    unittest.main()
