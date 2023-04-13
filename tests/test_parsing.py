
import unittest
import pdfsyntax as pdf

class Parsing(unittest.TestCase):

    def test_dictionary(self):
        self.assertEqual(pdf.parse_obj(b'<</abc 123>>'), {'/abc': 123})

    def test_dictionary2(self):
        self.assertEqual(pdf.parse_obj(b'<< /abc 123 >>'), {'/abc': 123})

    def test_ref(self):
        self.assertEqual(pdf.parse_obj(b'<< /abc 6 0 R >>'), {'/abc': 6j})

    def test_ref_list(self):
        self.assertEqual(pdf.parse_obj(b'[ 2 0 R 42 0 R ]'), [2j, 42j])

    def test_array(self):
        self.assertEqual(pdf.parse_obj(b'[/abc 123]'), ['/abc', 123])

    def test_array2(self):
        self.assertEqual(pdf.parse_obj(b'[ /abc 123 ]'), ['/abc', 123])

    def test_array3(self):
        self.assertEqual(pdf.parse_obj(b'[ /abc 123 ]\nendobj'), ['/abc', 123])

    def test_array4(self):
        self.assertEqual(pdf.parse_obj(b'[/abc/def]'), ['/abc', '/def'])

    def test_bool_array(self):
        self.assertEqual(pdf.parse_obj(b'[true false]'), [True, False])

    def test_nested_dictionary(self):
        self.assertEqual(pdf.parse_obj(b'<< /abc << /def 123 >> >>'), {'/abc': {'/def': 123}})

    def test_nested_dict_array(self):
        self.assertEqual(pdf.parse_obj(b'<< /abc [ /def 123 ] >>'), {'/abc': ['/def', 123]})

    def test_compressed(self):
        self.assertEqual(pdf.parse_obj(b'<</abc[/def/ghi]>>'), {'/abc': ['/def', '/ghi']})

    def test_simple_comment(self):
        self.assertEqual(pdf.parse_obj(b'[/abc %inner comment\n 123]'), ['/abc', 123])

    def test_multiple_comments(self):
        self.assertEqual(pdf.parse_obj(b'[%a\n/abc %b %c \n 123%d\n]'), ['/abc', 123])

    def test_stream_dict(self):
        self.assertEqual(pdf.parse_obj(b'<< /a 1 >>stream\ncontent\rendstream').entries, {'/a': 1})

    def test_n_stream(self):
        self.assertEqual(pdf.parse_obj(b'<< /a 1 >>stream\ncontent\rendstream').stream, b'content')
    
    def test_rn_stream(self):
        self.assertEqual(pdf.parse_obj(b'<< /a 1 >>stream\r\ncontent\rendstream').stream, b'content')
