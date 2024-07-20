
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

    def test_integer_incomplete(self): #Number may have been truncated
        self.assertEqual(pdf.next_token(b'12345'), (0, 5, None))

    def test_integer_minus(self):
        self.assertEqual(pdf.next_token(b'-12345 '), (0, 6,'INTEGER'))

    def test_real(self):
        self.assertEqual(pdf.next_token(b'123.45 '), (0, 6,'REAL'))

    def test_real2(self):
        self.assertEqual(pdf.next_token(b'+123.45 '), (0, 7,'REAL'))

    def test_literal_string(self):
        self.assertEqual(pdf.next_token(b'(abc) '), (0, 5,'STRING'))

    def test_literal_string2(self):
        self.assertEqual(pdf.next_token(b'(abc)'), (0, 5,'STRING'))

    def test_literal_string_with_bracket(self):
        self.assertEqual(pdf.next_token(b'(ab>c)'), (0, 6,'STRING'))

    def test_literal_string_with_parentheses(self):
        self.assertEqual(pdf.next_token(b'(a(b)c)'), (0, 7,'STRING'))

    def test_hexadecimal_string(self):
        self.assertEqual(pdf.next_token(b'<414243> '), (0, 8,'STRING'))

    def test_name(self):
        self.assertEqual(pdf.next_token(b'/abc '), (0, 4, 'NAME'))

    def test_name_incomplete(self): #Name may have been truncated
        self.assertEqual(pdf.next_token(b'/abc'), (0, 4, None))

    def test_name_i(self):
        self.assertEqual(pdf.next_token(b'/abc/def'), (0, 4, 'NAME'))

    def test_array(self):
        self.assertEqual(pdf.next_token(b'[12345 true /abc] '), (0, 17, 'ARRAY'))

    def test_dictionary(self):
        self.assertEqual(pdf.next_token(b'<< /Type /abc >> '), (0, 16, 'DICT'))

    def test_dictionary2(self):
        self.assertEqual(pdf.next_token(b'<< /Type /abc >>'), (0, 16, 'DICT'))

    def test_dictionary3(self):
        self.assertEqual(pdf.next_token(b'<</Type/abc>>'), (0, 13, 'DICT'))

    def test_stream(self):
        self.assertEqual(pdf.next_token(b'stream\n xyz \nendstream '), (0, 22, 'STREAM'))

    def test_comment(self):
        self.assertEqual(pdf.next_token(b' %something\n '), (1, 11, 'COMMENT'))

    def test_line(self):
        self.assertEqual(pdf.next_line(b'\n\rabc\n\rdef\n\r'), (2, 5))

    def test_line2(self):
        self.assertEqual(pdf.next_line(b'\n\rabc\n\rdef\n\r', 6), (7, 10))
