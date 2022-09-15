import unittest
import pdfsyntax as pdf

class Serialization(unittest.TestCase):

    def test_list(self):
        self.assertEqual(pdf.serialize(['/abc', 123]), b'[ /abc 123 ]')

    def test_dict(self):
        self.assertEqual(pdf.serialize({'/abc': 123, '/def': True}), b'<< /abc 123 /def true >>')
