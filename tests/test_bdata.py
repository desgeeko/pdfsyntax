import unittest
import pdfsyntax as pdf

class Bdata(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        #If a function is a direct parameter of the class
        #then self is passed and call breaks because there are too many arguments
        cls.f = {}
        f1 = open('./samples/simple_text_string.pdf', 'rb')
        cls.f["SINGLE"] = pdf.bdata_provider(f1, 'SINGLE')
        f1.close()
        f2 = open('./samples/simple_text_string.pdf', 'rb')
        cls.f["file"] = f2
        cls.f["CONTINUOUS"] = pdf.bdata_provider(f2, 'CONTINUOUS')

    def test_read_data(self):
        data = pdf.bdata_provider(b'0123456789')
        self.assertEqual(data(0, 2),(b'0123456789', 0, 0, 2))

    def test_read_data2(self):
        data = pdf.bdata_provider(b'0123456789')
        self.assertEqual(data(5, 3),(b'0123456789', 5, 0, 3))

    def test_read_partial_data(self):
        data = pdf.bdata_provider(b'0123456789')
        self.assertEqual(data(0, 99),(b'0123456789', 0, 0, 10))

    def test_length_single(self):
        self.assertEqual(pdf.bdata_length(self.f["SINGLE"]), 866)

    def test_length_continuous(self):
        self.assertEqual(pdf.bdata_length(self.f["CONTINUOUS"]), 866)

    def test_all_single(self):
        self.assertEqual(len(pdf.bdata_all(self.f["SINGLE"])), 866)

    def test_all_continuous(self):
        self.assertEqual(len(pdf.bdata_all(self.f["CONTINUOUS"])), 866)

    @classmethod
    def tearDownClass(cls):
        cls.f["file"].close()

