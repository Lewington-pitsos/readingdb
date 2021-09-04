import unittest
from converter import Converter

class TestConverter(unittest.TestCase):

    def test_xml_to_reading(self):
        xml_string = "<annotation><size><depth>3</depth><width>1920</width><height>1080</height></size><object><name>D1001</name><severity>1.0</severity><truncated>0</truncated><difficult>0</difficult><bndbox><xmin>0</xmin><ymin>0</ymin><xmax>0</xmax><ymax>0</ymax></bndbox></object></annotation>"
        reading = Converter.XML_to_single_reading(xml_string)