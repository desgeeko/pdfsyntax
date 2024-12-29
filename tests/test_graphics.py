import unittest
import pdfsyntax as pdf


class Unicode(unittest.TestCase):

    def test_stream_parsing(self):
        self.assertEqual(pdf.parse_stream_content(b'BT (abc) Tj ET'), [['BT'], [b'(abc)', 'Tj'] ,['ET']])



