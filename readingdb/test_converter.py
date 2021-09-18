import unittest
from pathlib import Path
from readingdb.converter import Converter
class TestConverter(unittest.TestCase):

    def test_xml_to_reading(self):
        extra_data = {
            'image_filename': 'test',
            'image_file_path': 'testtest'
        }

        xml_string = Path('readingdb/test_data/xml_test_readings/melb_test/annotations/xmls/2021_05_10_09_57_11_218-242.xml').read_text().replace('\n','')
        reading = Converter.XML_to_single_reading(xml_string, **extra_data)
        self.assertEqual(reading['Reading']['Entities'][0]['Name'], 'D1001')
        self.assertEqual(len(reading['Reading']['Entities']), 2)
        self.assertIn('image_filename', reading['Reading'])