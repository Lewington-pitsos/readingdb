from pprint import pprint
import unittest
import time

from readingdb.db import DB
from readingdb.constants import *
from readingdb.reading import PredictionReading, ImageReading
from readingdb.route import Route

class TestDBOps(unittest.TestCase):
    def setUp(self):
        # We assume that a dynamodb server is running on that endpoint already
        self.db = DB("http://localhost:8000")
    
    def test_saves_readings(self):
        self.db.create_reading_db()
        readings = self.db.routes_for_user("103")
        self.assertEqual(len(readings), 0)

        reading_time = int(time.time())

        for i in range(21):
            self.db.put_reading(
                ImageReading(
                    i,
                    "103",
                    reading_time,
                    ReadingTypes.IMAGE,
                    "https://aws/s3/somebucket/file.jpg", 
                )
            )
        
        readings = self.db.all_route_readings("103")
        self.assertEqual(len(readings), 21)
        first_reading = readings[0]
        self.assertEqual(first_reading[ReadingRouteKeys.ROUTE_ID], "103")
        self.assertEqual(first_reading[ReadingKeys.READING_ID], 0)
        self.assertEqual(first_reading[ReadingKeys.TYPE], ReadingTypes.IMAGE)
        self.assertEqual(first_reading[ReadingKeys.READING], {
                ImageReadingKeys.FILENAME: "https://aws/s3/somebucket/file.jpg" 
        })
        self.assertEqual(first_reading[ReadingKeys.TIMESTAMP], reading_time)

    def test_creates_new_route(self):
        self.db.create_reading_db()
        routes = self.db.routes_for_user("103")
        self.assertEqual(len(routes), 0)

        self.db.put_route(Route("3", "103"))
        
        routes = self.db.routes_for_user("3")
        self.assertEqual(len(routes), 1)

    def test_creates_new_route_with_name(self):
        name = "someName"
        self.db.create_reading_db()
        routes = self.db.routes_for_user("103")
        self.assertEqual(len(routes), 0)

        self.db.put_route(Route("3", "103", name=name))
        routes = self.db.routes_for_user("3")
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0][RouteKeys.NAME], name)

    def test_creates_new_route_with_sample_data(self):
        sample_entry = {"PredictionReading": {
            "ReadingID": 78,
            "Type": "PredictionReading",
            "Reading": {
                "Latitude": -37.8714232,
                "Longitude": 145.2450816,
                "IsCrocodileCrackFault": False,
                "LatCrackConfidence": 0.07661053,
                "ImageFileName": "/home/lewington/code/faultnet/data/inference/route_2021_03_19_12_08_03_249/images/snap_2021_03_19_12_08_26_863.jpg",
                "LongCrackConfidence": 0.6557837,
                "IsLongCrackFault": False,
                "IsLatCrackFault": False,
                "CrocodileCrackConfidence": 0.17722677,
                "PotholeConfidence": 0.14074452,
                "IsPotholeFault": False,
                "LineblurConfidence": 0.09903459,
                "IsLineblurFault": False
            },
            "RouteID": "45",
            "Timestamp": 1616116106935,
            "MillisecondPrecision": True,
            "Row": 30,
        }}
   
        expected_entry = {"PredictionReading": {
            "ReadingID": 78,
            "Type": "PredictionReading",
            "Reading": {
                "Latitude": -37.8714232,
                "Longitude": 145.2450816,
                "IsCrocodileCrackFault": False,
                "LatCrackConfidence": 0.07661053,
                "ImageFileName": "/home/lewington/code/faultnet/data/inference/route_2021_03_19_12_08_03_249/images/snap_2021_03_19_12_08_26_863.jpg",
                "LongCrackConfidence": 0.6557837,
                "IsLongCrackFault": False,
                "IsLatCrackFault": False,
                "CrocodileCrackConfidence": 0.17722677,
                "PotholeConfidence": 0.14074452,
                "IsPotholeFault": False,
                "LineblurConfidence": 0.09903459,
                "IsLineblurFault": False
            },
            "RouteID": "45",
            "Timestamp": 1616116106935,
        }}

        self.db.create_reading_db()
        routes = self.db.routes_for_user("103")
        self.assertEqual(len(routes), 0)

        self.db.put_route(Route("3", "103", sample_data=sample_entry))
        
        routes = self.db.routes_for_user("3")
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0][RouteKeys.SAMPLE_DATA], expected_entry)

    def test_creates_and_deletes_tables(self):
        self.db.create_reading_db()
        tables = self.db.all_tables()
        self.assertEqual(len(tables), 2)

        self.db.teardown_reading_db()
        tables = self.db.all_tables()
        self.assertEqual(len(tables), 0)

    def tearDown(self):
        tables = self.db.all_tables()
        if len(tables) > 0:
            self.db.teardown_reading_db()