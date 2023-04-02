
import unittest
import pdfsyntax as pdf

class Xref(unittest.TestCase):

    xt =  b'xref\n'
    xt += b'0 2\n'
    xt += b'0000000000 65535 f\n'
    xt += b'0000000123 00001 n\n'
    xt += b'0000000456 00001 n\n'

    def test_xref_table(self):
        self.assertEqual(len(pdf.parse_xref_table(self.xt, 0, 0)), 3)

    def test_xref_table2(self):
        self.assertEqual(pdf.parse_xref_table(self.xt, 0, 0)[1]['o_num'], 1)

    def test_xref_table3(self):
        self.assertEqual(pdf.parse_xref_table(self.xt, 0, 0)[2]['abs_pos'], 456)

