
import unittest
import pdfsyntax as pdf

class Parsing(unittest.TestCase):

    def test_dictionary(self):
        self.assertEqual(pdf.parse_obj(b'<</abc 123>>'), {'/abc': 123})

    def test_dictionary2(self):
        self.assertEqual(pdf.parse_obj(b'<< /abc 123 >>'), {'/abc': 123})

    def test_ref(self):
        self.assertEqual(pdf.parse_obj(b'<< /abc 6 0 R >>'), {'/abc': {'_REF': 6}})

    def test_ref_list(self):
        self.assertEqual(pdf.parse_obj(b'[ 2 0 R 42 0 R ]'), [{'_REF': 2}, {'_REF': 42}])

    def test_array(self):
        self.assertEqual(pdf.parse_obj(b'[/abc 123]'), ['/abc', 123])

    def test_array2(self):
        self.assertEqual(pdf.parse_obj(b'[ /abc 123 ]'), ['/abc', 123])

    def test_array3(self):
        self.assertEqual(pdf.parse_obj(b'[/abc/def]'), ['/abc', '/def'])

    def test_bool_array(self):
        self.assertEqual(pdf.parse_obj(b'[true false]'), [True, False])

    def test_nested_dictionary(self):
        self.assertEqual(pdf.parse_obj(b'<< /abc << /def 123 >> >>'), {'/abc': {'/def': 123}})

    def test_nested_dict_array(self):
        self.assertEqual(pdf.parse_obj(b'<< /abc [ /def 123 ] >>'), {'/abc': ['/def', 123]})

    def test_compressed(self):
        self.assertEqual(pdf.parse_obj(b'<</abc[/def/ghi]>>'), {'/abc': ['/def', '/ghi']})

