from pprint import pprint
import unittest
import time
import os
import json
import uuid

from botocore.utils import ensure_boolean

from readingdb.db import DB
from readingdb.constants import *
from readingdb.reading import AbstractReading, ImageReading, json_to_reading
from readingdb.route import Route

class TestDB(unittest.TestCase):
    def setUp(self):
        self.current_dir = os.path.dirname(__file__)
        self.db = DB("http://localhost:8000")
    
    def test_saves_readings(self):
        self.db.create_reading_db()
        readings = self.db.routes_for_user("103")
        self.assertEqual(len(readings), 0)

        reading_time = int(time.time())

        for i in range(21):
            self.db.put_reading(
                ImageReading(
                    "sdasdasd-" + str(i),
                    "xxxa",
                    reading_time,
                    ReadingTypes.IMAGE,
                    "https://aws/s3/somebucket/file.jpg", 
                )
            )
        
        readings = self.db.all_route_readings("xxxa")
        self.assertEqual(len(readings), 21)
        first_reading = readings[0]
        self.assertEqual(first_reading[ReadingRouteKeys.ROUTE_ID], "xxxa")
        self.assertEqual(first_reading[ReadingKeys.TYPE], ReadingTypes.IMAGE)
        self.assertEqual(first_reading[ReadingKeys.READING_ID], "sdasdasd-0")
        self.assertEqual(first_reading[ReadingKeys.READING], {
                ImageReadingKeys.FILENAME: "https://aws/s3/somebucket/file.jpg" 
        })
        self.assertEqual(first_reading[ReadingKeys.TIMESTAMP], reading_time)

    def test_creates_new_route(self):
        self.db.create_reading_db()
        routes = self.db.routes_for_user("103")
        self.assertEqual(len(routes), 0)

        self.db.put_route(Route("3", "103", 123617823))
        
        routes = self.db.routes_for_user("3")
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0], {
            "RouteID": "103",
            "RouteName": "103",
            "UserID": "3",
            "RouteStatus": 1,
            "Timestamp": 123617823
        })

    def test_loads_large_dataset(self):
        self.db.create_reading_db()
        routes = self.db.routes_for_user("103")
        self.assertEqual(len(routes), 0)

        self.db.put_route(Route("3", "103", 123617823))
        
        with open(self.current_dir +  "/test_data/sydney_entries.json", "r") as f:
            entities = json.load(f)

        route_id = "103"
        for e in entities:
            e[ReadingKeys.READING_ID] = str(uuid.uuid1())
            e[ReadingRouteKeys.ROUTE_ID] = route_id
            r: AbstractReading = json_to_reading("PredictionReading", e)
            self.db.put_reading(r)

        readings = self.db.all_route_readings(route_id)
    
        self.assertEqual(3383, len(readings))

    def test_creates_new_route_with_name(self):
        name = "someName"
        self.db.create_reading_db()
        routes = self.db.routes_for_user("103")
        self.assertEqual(len(routes), 0)

        self.db.put_route(Route("3", "103", 123617823, name=name))
        routes = self.db.routes_for_user("3")
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0][RouteKeys.NAME], name)

    def test_creates_new_route_with_sample_data(self):
        sample_entry = {
            "ReadingID": 78,
            "Type": "PredictionReading",
            "Reading": {
                "Entities": [
                    {
                        "Name": "CrocodileCrack",
                        "Confidence": 0.17722677,
                        "Present": False,
                    },
                    {
                        "Name": "LatCrack", 
                        "Confidence": 0.07661053,
                        "Present": False,
                    },
                    {
                        "Name": "LongCrack", 
                        "Confidence": 0.6557837,
                        "Present": False,
                    },
                    {
                        "Name": "Pothole",
                        "Confidence": 0.14074452,
                        "Present": False,
                    },
                    {
                        "Name": "Lineblur",
                        "Confidence": 0.09903459,
                        "Present": False,
                    }
                ],
                "Latitude": -37.8714232,
                "Longitude": 145.2450816,
                "ImageFileName": "route_2021_03_19_12_08_03_249/images/snap_2021_03_19_12_08_26_863.jpg",
            },
            "RouteID": "45",
            "Timestamp": 1616116106935,
            "MillisecondPrecision": True,
            "Row": 30,
        }
   
        expected_entry = {"PredictionReading": {
            "ReadingID": 78,
            "Type": "PredictionReading",
            "Reading": {
                "Entities": [
                    {
                        "Name": "CrocodileCrack",
                        "Confidence": 0.17722677,
                        "Present": False,
                    },
                    {
                        "Name": "LatCrack", 
                        "Confidence": 0.07661053,
                        "Present": False,
                    },
                    {
                        "Name": "LongCrack", 
                        "Confidence": 0.6557837,
                        "Present": False,
                    },
                    {
                        "Name": "Pothole",
                        "Confidence": 0.14074452,
                        "Present": False,
                    },
                    {
                        "Name": "Lineblur",
                        "Confidence": 0.09903459,
                        "Present": False,
                    }
                ],
                "Latitude": -37.8714232,
                "Longitude": 145.2450816,
                "ImageFileName": "route_2021_03_19_12_08_03_249/images/snap_2021_03_19_12_08_26_863.jpg",
            },
            "RouteID": "45",
            "Timestamp": 1616116106935,
        }}

        self.db.create_reading_db()
        routes = self.db.routes_for_user("103")
        self.assertEqual(len(routes), 0)

        self.db.put_route(Route(
            "3", 
            "103", 
            123617823,
            sample_data={"PredictionReading": json_to_reading("PredictionReading", sample_entry)}
        ))
        
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