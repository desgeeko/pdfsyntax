
import unittest
import pdfsyntax as pdf

class SimpleFile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = pdf.read_pdf('./samples/simple_text_string.pdf')

    def test_index_length(self):
        self.assertEqual(len(self.doc.index), 1)

    def test_prev(self):
        self.assertEqual('/Prev' in self.doc.cache[0], False)

