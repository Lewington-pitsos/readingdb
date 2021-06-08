from readingdb.geolocator import Geolocator
import unittest
from readingdb.format import *

class TestGeolocator(unittest.TestCase):
    def test_snapping(self):
        pos_readings = []
        snapped_pos_readings = Geolocator.geolocate(pos_readings)

        self.assertEqual(len(pos_readings), len(snapped_pos_readings))