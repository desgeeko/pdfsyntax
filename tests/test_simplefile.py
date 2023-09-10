
import unittest
import pdfsyntax as pdf

class SimpleFile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = pdf.readfile('./samples/simple_text_string.pdf')

    def test_index_length(self):
        self.assertEqual(len(self.doc.index), 2)

    def test_prev(self):
        self.assertEqual('/Prev' in self.doc.cache[0], True)

    def test_page_list(self):
        self.assertEqual(pdf.flat_page_tree(self.doc), [(4j, {})])

