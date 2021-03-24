import unittest
import time

from readingdb.db import DB
from readingdb.constants import *


class TestFileUtils(unittest.TestCase):
    def setUp(self):
        # We assume that a dynamodb server is running on that endpoint already
        self.db = DB("http://localhost:8000")
    
    def test_creates_new_sessions(self):
        self.db.create_reading_db()
        routes = self.db.routes_for(103)
        self.assertEqual(len(routes), 0)

        for i in range(21):
            self.db.put_reading(
                103,
                3,
                i,
                ReadingTypes.IMAGE,
                {
                    ImageReading.FILENAME: "https://aws/s3/somebucket/file.jpg" 
                },
                int(time.time())
            )
        
        routes = self.db.routes_for(103)
        self.assertEqual(len(routes), 1)

    def test_creates_and_deletes_tables(self):
        self.db.create_reading_db()
        tables = self.db.all_tables()
        self.assertEqual(len(tables), 2)

        self.db.teardown_reading_db()
        tables = self.db.all_tables()
        self.assertEqual(len(tables), 0)

    def test_creates_table_adds_values(self):
        self.db.create_reading_db()
        readings = self.db.all_route_readings(3)
        self.assertEqual(len(readings), 0)

        for i in range(21):
            self.db.put_reading(
                103,
                3,
                i,
                ReadingTypes.IMAGE,
                {
                    ImageReading.FILENAME: "https://aws/s3/somebucket/file.jpg" 
                },
                int(time.time())
            )
        
        readings = self.db.all_route_readings(3)
        self.assertEqual(len(readings), 21)
    
    def tearDown(self):
        tables = self.db.all_tables()
        if len(tables) > 0:
            self.db.teardown_reading_db()