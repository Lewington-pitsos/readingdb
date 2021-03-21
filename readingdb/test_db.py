import unittest
import time

from readingdb.db import DB
from readingdb.constants import *


class TestFileUtils(unittest.TestCase):
    def setUp(self):
        # We assume that a dynamodb server is running on that endpoint already
        self.db = DB("http://localhost:8000")
    
    def test_creates_and_deletes_table(self):
        self.db.create_reading_table()
        tables = self.db.all_tables()
        self.assertEqual(len(tables), 1)

        self.db.delete_table(Database.READING_TABLE_NAME)
        tables = self.db.all_tables()
        self.assertEqual(len(tables), 0)

    def test_creates_table_adds_values(self):
        self.db.create_reading_table()
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
        if len(tables) == 1:
            self.db.delete_table(Database.READING_TABLE_NAME)
        if len(tables) > 1:
            raise ValueError(f"Too many tables in database: {tables}")
        
