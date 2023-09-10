
import unittest
import pdfsyntax as pdf

class Updating(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = pdf.readfile('./samples/add_text_annotation.pdf')

    def test_index_length(self):
        self.assertEqual(len(self.doc.index), 3)

    def test_prev(self):
        self.assertEqual('/Prev' in self.doc.cache[0], True)

