import unittest
import pdfsyntax as pdf

class Bdata(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        #If a function is a direct parameter of the class
        #then self is passed and call breaks because there are too many arguments
        cls.f = {}
        cls.f["SINGLE"] = pdf.bdata_provider('./samples/simple_text_string.pdf', 'SINGLE')
        cls.f["CONTINUOUS"] = pdf.bdata_provider('./samples/simple_text_string.pdf', 'CONTINUOUS')

    def test_length_single(self):
        self.assertEqual(pdf.bdata_length(self.f["SINGLE"]), 823)

    def test_length_continuous(self):
        self.assertEqual(pdf.bdata_length(self.f["CONTINUOUS"]), 823)

    def test_all_single(self):
        self.assertEqual(len(pdf.bdata_all(self.f["SINGLE"])), 823)

    def test_all_continuous(self):
        self.assertEqual(len(pdf.bdata_all(self.f["CONTINUOUS"])), 823)

