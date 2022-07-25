
import unittest
import pdfsyntax as pdf

class Tokenization(unittest.TestCase):

    def test_boolean_true(self):
        self.assertEqual(pdf.next_token(b'true '), (0, 4,'TRUE'))

    def test_boolean_false(self):
        self.assertEqual(pdf.next_token(b'false '), (0, 5,'FALSE'))

    def test_keyword(self):
        self.assertEqual(pdf.next_token(b'trueblue '), (0, 8,'KEYWORD'))

    def test_integer(self):
        self.assertEqual(pdf.next_token(b'12345 '), (0, 5,'INTEGER'))

    def test_integer2(self):
        self.assertEqual(pdf.next_token(b'-12345 '), (0, 6,'INTEGER'))

    def test_real(self):
        self.assertEqual(pdf.next_token(b'123.45 '), (0, 6,'REAL'))

    def test_real2(self):
        self.assertEqual(pdf.next_token(b'+123.45 '), (0, 7,'REAL'))

    def test_literal_string(self):
        self.assertEqual(pdf.next_token(b'(abc) '), (0, 5,'TEXT'))

    def test_hexadecimal_string(self):
        self.assertEqual(pdf.next_token(b'<414243> '), (0, 8,'TEXT'))

    def test_name(self):
        self.assertEqual(pdf.next_token(b'/abc '), (0, 4, 'NAME'))

    def test_array(self):
        self.assertEqual(pdf.next_token(b'[12345 true /abc] '), (0, 17, 'ARRAY'))

    def test_dictionary(self):
        self.assertEqual(pdf.next_token(b'<< /Type /abc >> '), (0, 16, 'DICT'))

    def test_stream(self):
        self.assertEqual(pdf.next_token(b'stream\n xyz \nendstream '), (7, 12, 'STREAM'))

#class Unicode(unittest.TestCase):
#
#    def test_unicode(self):
#        self.assertEqual(pdf.dec_unicode(b'\x00\x41'), 'A')
