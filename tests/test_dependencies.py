import unittest
import pdfsyntax as pdf

class Dependencies(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = pdf.readfile('./samples/simple_text_string.pdf')

    def test_dict(self):
        self.assertEqual(pdf.dependencies(self.doc, {'/a': 2j}), {2j})

    def test_list(self):
        self.assertEqual(pdf.dependencies(self.doc, [5j, 6j]), {5j, 6j})

    def test_page(self):
        self.assertEqual(pdf.dependencies(self.doc, 4j), {4j, 5j, 6j, 7j})

    def test_page2(self):
        self.assertEqual(pdf.dependencies(self.doc, pdf.get_object(self.doc, 4j)), {5j, 6j, 7j})

    def test_str(self):
        self.assertEqual(pdf.dependencies(self.doc, b'test'), set())
