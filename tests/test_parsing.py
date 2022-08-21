
import unittest
import pdfsyntax as pdf

class Parsing(unittest.TestCase):

    def test_dictionary(self):
        self.assertEqual(pdf.parse_obj(b'<< /abc 123 >>'), {'/abc': 123})

    def test_array(self):
        self.assertEqual(pdf.parse_obj(b'[ /abc 123 ]'), ['/abc', 123])

    def test_nested_dictionary(self):
        self.assertEqual(pdf.parse_obj(b'<< /abc << /def 123 >> >>'), {'/abc': {'/def': 123}})

    def test_nested_dict_array(self):
        self.assertEqual(pdf.parse_obj(b'<< /abc [ /def 123 ] >>'), {'/abc': ['/def', 123]})

    def test_compressed(self):
        self.assertEqual(pdf.parse_obj(b'<</abc[/def/ghi]>>'), {'/abc': ['/def', '/ghi']})

