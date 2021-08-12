import json
import readingdb.constants as C
from readingdb.rutils import RUtils
from readingdb.geolocator import Geolocator
import unittest
from readingdb.tutils import roads_api_test
from readingdb.format import *

class TestGeolocator(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with open('readingdb/test_data/melb_gps_img.json', 'r') as f:
            allReadings = json.load(f)
        
        cls.pos_readings = [r for r in allReadings if r[Constants.READING_TYPE] == 'PositionalReading'] 
        cls.img_readings = [r for r in allReadings if r[Constants.READING_TYPE] == 'ImageReading'] 

    @roads_api_test
    def test_snapping(self):
        g = Geolocator()
        snapped_pos_readings = g.geolocate(self.pos_readings[:80])
        self.assertEqual(70, len(snapped_pos_readings))
        self.assertEqual(-37.69701799822927, RUtils.get_lat(snapped_pos_readings[0]))
        self.assertEqual(144.80300877308167,  RUtils.get_lng(snapped_pos_readings[0]))
        self.assertEqual(-37.7022301, RUtils.get_lat(snapped_pos_readings[-1]))
        self.assertEqual(144.8019646,  RUtils.get_lng(snapped_pos_readings[-1]))

        lastTimestamp = 0
        for s in snapped_pos_readings:
            new_ts = s[Constants.TIMESTAMP]
            self.assertGreaterEqual(new_ts, lastTimestamp)
            lastTimestamp = new_ts
    
    @roads_api_test
    def test_snapping_for_less_than_15_readings(self):
        g = Geolocator()
        snapped_pos_readings = g.geolocate(self.pos_readings[:10])
        self.assertEqual(10, len(snapped_pos_readings))
        self.assertEqual(-37.6969851, RUtils.get_lat(snapped_pos_readings[0]))
        self.assertEqual(144.8028779,  RUtils.get_lng(snapped_pos_readings[0]))

    @roads_api_test
    def test_snapping_for_more_than_100_readings(self):
        g = Geolocator()
        snapped_pos_readings = g.geolocate(self.pos_readings[:240])
        self.assertEqual(230, len(snapped_pos_readings))
        self.assertEqual(-37.69701799822927, RUtils.get_lat(snapped_pos_readings[0]))
        self.assertEqual(144.80300877308167,  RUtils.get_lng(snapped_pos_readings[0]))

        lastTimestamp = 0
        for s in snapped_pos_readings:
            new_ts = s[Constants.TIMESTAMP]
            self.assertGreater(new_ts, lastTimestamp)
            lastTimestamp = new_ts

        snapped_pos_readings = g.geolocate(self.pos_readings[:101])
        self.assertEqual(91, len(snapped_pos_readings))
        self.assertEqual(-37.69701799822927,  RUtils.get_lat(snapped_pos_readings[0]))
        self.assertEqual(144.80300877308167,  RUtils.get_lng(snapped_pos_readings[0]))

    @roads_api_test
    def test_replacement_for_more_than_100_readings(self):
        g = Geolocator()
        snapped_pos_readings = g.geolocate(self.pos_readings[:240], replacement=True)
        self.assertEqual(392, len(snapped_pos_readings))
        self.assertEqual(-37.69701799822927, snapped_pos_readings[0][C.LAT])
        self.assertEqual(144.80300877308167, snapped_pos_readings[0][C.LNG])

        snapped_pos_readings = g.geolocate(self.pos_readings[:100], replacement=True)
        self.assertEqual(169, len(snapped_pos_readings))
        self.assertEqual(-37.69701799822927, snapped_pos_readings[0][C.LAT])
        self.assertEqual(144.80300877308167, snapped_pos_readings[0][C.LNG])

    @roads_api_test
    def test_prediction_generating(self):
        g = Geolocator()
        predictions = g.generate_predictions(self.pos_readings[:80], self.img_readings[:80])
        self.assertEqual(80, len(predictions))
        self.assertEqual('PredictionReading', RUtils.get_type(predictions[0]))

    def test_filtering(self):
        g = Geolocator()
        with open('readingdb/test_data/box-hill.json', 'r') as f:
            readings = json.load(f)

        filtered = g.filter_stationary(readings)
        self.assertLess(len(filtered), len(readings))

        all_imgs = set()
        filtered_imgs = set()

        for r in readings:
            all_imgs.add(r[Constants.READING][Constants.URI][Constants.KEY])
        for r in filtered:
            filtered_imgs.add(r[Constants.READING][Constants.URI][Constants.KEY])

        removed = list(all_imgs - filtered_imgs)
        self.assertEqual(553, len(removed))
   
    def test_filtering_after_geolocation(self):
        g = Geolocator()
        with open('readingdb/test_data/box-hill-geolocated.json', 'r') as f:
            readings = json.load(f)

        filtered = g.filter_stationary(readings)
        self.assertLess(len(filtered), len(readings))

        all_imgs = set()
        filtered_imgs = set()

        for r in readings:
            all_imgs.add(r[Constants.READING][Constants.URI][Constants.KEY])
        for r in filtered:
            filtered_imgs.add(r[Constants.READING][Constants.URI][Constants.KEY])

        removed = list(all_imgs - filtered_imgs)
        self.assertEqual(501, len(removed))

    def test_interpolation(self):
        g = Geolocator()
        interp = g.interpolated(self.pos_readings, self.img_readings)
        self.assertEqual(1529, len(interp))
        self.assertEqual('PredictionReading', RUtils.get_type(interp[0]))
        self.assertIn('Entities', interp[0]['Reading'])
        self.assertEqual(-37.69698717037037, RUtils.get_lat(interp[0]))
        self.assertEqual(144.802889819943,  RUtils.get_lng(interp[0]))

    def test_interpolation_does_not_add_useless_img_readings(self):
        g = Geolocator()
        interp = g.interpolated(self.pos_readings[400:], self.img_readings)
        self.assertEqual(806, len(interp))

        interp = g.interpolated(self.pos_readings[:700], self.img_readings)
        self.assertEqual(1263, len(interp))