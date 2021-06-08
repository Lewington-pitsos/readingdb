import json
from readingdb.geolocator import Geolocator
import unittest
from readingdb.format import *

class TestGeolocator(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with open('readingdb/test_data/melb_gps_img.json', 'r') as f:
            allReadings = json.load(f)
        
        cls.pos_readings = [r for r in allReadings if r[ReadingKeys.TYPE] == ReadingTypes.POSITIONAL] 
        cls.img_readings = [r for r in allReadings if r[ReadingKeys.TYPE] == ReadingTypes.IMAGE] 

    def test_snapping(self):
        snapped_pos_readings = Geolocator.geolocate(self.pos_readings)

        self.assertEqual(len(self.pos_readings), len(snapped_pos_readings))

    def test_prediction_generating(self):
        predictions = Geolocator.generate_predictions(self.pos_readings, self.img_readings)

        self.assertEqual(len(self.img_readings), len(predictions))