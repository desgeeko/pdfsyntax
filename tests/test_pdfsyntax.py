
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

class Parsing(unittest.TestCase):

    def test_dictionary(self):
        self.assertEqual(pdf.parse_obj(b'<< /abc 123 >>'), {b'/abc': 123})

    def test_array(self):
        self.assertEqual(pdf.parse_obj(b'[ /abc 123 ]'), [b'/abc', 123])

    def test_nested_dictionary(self):
        self.assertEqual(pdf.parse_obj(b'<< /abc << /def 123 >> >>'), {b'/abc': {b'/def': 123}})

    def test_nested_dict_array(self):
        self.assertEqual(pdf.parse_obj(b'<< /abc [ /def 123 ] >>'), {b'/abc': [b'/def', 123]})

    def test_compressed(self):
        self.assertEqual(pdf.parse_obj(b'<</abc[/def/ghi]>>'), {b'/abc': [b'/def', b'/ghi']})

class Xref(unittest.TestCase):

    xt =  b'xref\n'
    xt += b'0 2\n'
    xt += b'0000000000 65535 f\n'
    xt += b'0000000123 00001 n\n'
    xt += b'0000000456 00001 n\n'

    def test_xref_table(self):
        self.assertEqual(len(pdf.parse_xref_table(self.xt, 0)), 3)

    def test_xref_table2(self):
        self.assertEqual(pdf.parse_xref_table(self.xt, 0)[1]['o_num'], 1)

    def test_xref_table3(self):
        self.assertEqual(pdf.parse_xref_table(self.xt, 0)[2]['abs_pos'], 456)

class SimpleFile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = pdf.read_pdf('./samples/simple_text_string.pdf')

    def test_index_length(self):
        self.assertEqual(len(self.doc.index), 1)

    def test_prev(self):
        self.assertEqual(b'/Prev' in self.doc.cache[0], False)

class Updating(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = pdf.read_pdf('./samples/add_text_annotation.pdf')

    def test_index_length(self):
        self.assertEqual(len(self.doc.index), 2)

    def test_prev(self):
        self.assertEqual(b'/Prev' in self.doc.cache[0], True)


#class Unicode(unittest.TestCase):
#
#    def test_unicode(self):
#        self.assertEqual(pdf.dec_unicode(b'\x00\x41'), 'A')
