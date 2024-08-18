import unittest
import pdfsyntax as pdf


class Unicode(unittest.TestCase):

    def test_literal_pdfdocencoded_basic(self):
        self.assertEqual(pdf.text_string(b'(Martin D.)'), 'Martin D.')

    def test_literal_pdfdocencoded_backslash(self):
        self.assertEqual(pdf.text_string(b'(a\\\\b)'), 'a\\b')

    def test_literal_pdfdocencoded_parenthesis(self):
        self.assertEqual(pdf.text_string(b'(page\\(s\\))'), 'page(s)')

    def test_literal_pdfdocencoded_special(self): # Euro sign does not exist in latin-1
        self.assertEqual(pdf.text_string(b'(10\xa0!)'), '10€!')

    def test_literal_utf16be(self):
        self.assertEqual(pdf.text_string(b'(\xfe\xff\x00M\x00a\x00r\x00t\x00i\x00n\x00 \x00D\x00.)'), 'Martin D.')

    def test_literal_utf16be_octal(self):
        self.assertEqual(pdf.text_string(b'(\376\377\000M\000\040\000D)'), 'M D')

    def test_hexa_pdfdocencoded(self):
        self.assertEqual(pdf.text_string(b'<414243>'), 'ABC')

    def test_hexa_utf16be(self):
        self.assertEqual(pdf.text_string(b'<FEFF004100420043>'), 'ABC')

#    def test_unicode(self):
#        self.assertEqual(pdf.dec_unicode(b'\x00\x41'), 'A')
