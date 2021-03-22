import json
import unittest
import decimal

from readingdb.constants import Database
from readingdb.api import API

class TestAPIEntryConsumption(unittest.TestCase):

    def setUp(self):
        self.api = API("http://localhost:8000")
        self.api.create_reading_table()
        

    def test_reads_and_loads_entries_correctly(self):
        with open("readingdb/test_data/ftg_filtered_entries.json", "r") as f:
            entries = json.load(f)

        rid = 0

        for e in entries[500:600]:
            self.api.save_entry(103, 45, rid, e)
            rid+=1

        readings = self.api.all_route_readings(45)

        with open("readingdb/test_data/sample_readings.json", "r") as f:
            expected_readings = json.load(f)

        for r in readings:
            for k, v in r.items():
                if isinstance(v, decimal.Decimal):
                    r[k] = int(v)
        
        self.assertEqual(readings, expected_readings)
    
    def tearDown(self):
        self.api.delete_table(Database.READING_TABLE_NAME)
