
import unittest
import pdfsyntax.docstruct as pdf

class Tokenization(unittest.TestCase):

    def test_value(self):
        self.assertEqual(pdf.next_token(b'74252 ', 0), (0, 5,'VALUE'))

    def test_name(self):
        self.assertEqual(pdf.next_token(b'/aaa ', 0), (0, 4, 'NAME'))
        
class Unicode(unittest.TestCase):

    def test_unicode(self):
        self.assertEqual(pdf.dec_unicode(b'\x00\x41'), 'A')
