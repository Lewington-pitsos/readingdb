import json
import os
from readingdb.rutils import RUtils
from readingdb.geolocator import Geolocator
import unittest
from readingdb.format import *

roads_api_test = unittest.skipIf(
    not os.environ.get('ROADS_API', False), 'Googls Maps Road API tests are skipped by default'
)

class TestGeolocator(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with open('readingdb/test_data/melb_gps_img.json', 'r') as f:
            allReadings = json.load(f)
        
        cls.pos_readings = [r for r in allReadings if r[ReadingKeys.TYPE] == ReadingTypes.POSITIONAL] 
        cls.img_readings = [r for r in allReadings if r[ReadingKeys.TYPE] == ReadingTypes.IMAGE] 

    @roads_api_test
    def test_snapping(self):
        g = Geolocator()
        snapped_pos_readings = g.geolocate(self.pos_readings[:80])
        self.assertEqual(80, len(snapped_pos_readings))
        self.assertEqual(-37.69701799822927, RUtils.get_lat(snapped_pos_readings[0]))
        self.assertEqual(144.80300877308167,  RUtils.get_lng(snapped_pos_readings[0]))
        self.assertEqual(-37.7022301, RUtils.get_lat(snapped_pos_readings[-1]))
        self.assertEqual(144.8019646,  RUtils.get_lng(snapped_pos_readings[-1]))

        lastTimestamp = 0
        for s in snapped_pos_readings:
            new_ts = s[ReadingKeys.TIMESTAMP]
            self.assertGreater(new_ts, lastTimestamp)
            lastTimestamp = new_ts
    
    @roads_api_test
    def test_snapping_for_more_than_100_readings(self):
        g = Geolocator()
        snapped_pos_readings = g.geolocate(self.pos_readings[:240])
        self.assertEqual(240, len(snapped_pos_readings))
        self.assertEqual(-37.69701799822927, RUtils.get_lat(snapped_pos_readings[0]))
        self.assertEqual(144.80300877308167,  RUtils.get_lng(snapped_pos_readings[0]))

        lastTimestamp = 0
        for s in snapped_pos_readings:
            new_ts = s[ReadingKeys.TIMESTAMP]
            self.assertGreater(new_ts, lastTimestamp)
            lastTimestamp = new_ts

        snapped_pos_readings = g.geolocate(self.pos_readings[:101])
        self.assertEqual(101, len(snapped_pos_readings))
        self.assertEqual(-37.69701799822927, RUtils.get_lat(snapped_pos_readings[0]))
        self.assertEqual(144.80300877308167,  RUtils.get_lng(snapped_pos_readings[0]))

        lastTimestamp = 0
        for s in snapped_pos_readings:
            new_ts = s[ReadingKeys.TIMESTAMP]
            self.assertGreater(new_ts, lastTimestamp)
            lastTimestamp = new_ts

        snapped_pos_readings = g.geolocate(self.pos_readings[:100])
        self.assertEqual(100, len(snapped_pos_readings))
        self.assertEqual(-37.69701799822927, RUtils.get_lat(snapped_pos_readings[0]))
        self.assertEqual(144.80300877308167,  RUtils.get_lng(snapped_pos_readings[0]))

        lastTimestamp = 0
        for s in snapped_pos_readings:
            new_ts = s[ReadingKeys.TIMESTAMP]
            self.assertGreater(new_ts, lastTimestamp)
            lastTimestamp = new_ts

    @roads_api_test
    def test_prediction_generating(self):
        g = Geolocator()
        cnt = 80
        predictions = g.generate_predictions(self.pos_readings[:cnt], self.img_readings[:cnt])
        self.assertEqual(cnt, len(predictions))
        self.assertEqual('PredictionReading', RUtils.get_type(predictions[0]))

    def test_interpolation(self):
        g = Geolocator()
        interp = g.interpolated(self.pos_readings, self.img_readings)
        self.assertEqual(1529, len(interp))
        self.assertEqual('PredictionReading', RUtils.get_type(interp[0]))
        self.assertEqual(-37.69698717037037, RUtils.get_lat(interp[0]))
        self.assertEqual(144.802889819943,  RUtils.get_lng(interp[0]))

    def test_interpolation_does_not_add_useless_img_readings(self):
        g = Geolocator()
        interp = g.interpolated(self.pos_readings[400:], self.img_readings)
        self.assertEqual(806, len(interp))

        interp = g.interpolated(self.pos_readings[:700], self.img_readings)
        self.assertEqual(1263, len(interp))