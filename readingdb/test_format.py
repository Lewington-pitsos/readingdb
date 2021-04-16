import unittest
import time

from readingdb.format import *

class TestFormatting(unittest.TestCase):
    def test_key_to_datetime(self):
        key = "mocks/route45/2021_04_10_22_18_22_123-1.jpg"
        self.assertEqual(unix_from_key(key), 1618093102123)

        key = "mocks/route45/2018_01_05_22_58_22_123-1.jpg"
        self.assertEqual(unix_from_key(key), 1515193102123)

        key = "mocks/route45/2021_01_31_11_56_59_949-876.png"
        self.assertEqual(unix_from_key(key), 1612094219949)

    def test_file_to_entry(self):
        key = "mocks/route45/2011_08_19_04_45_02_832-31.jpg"
        bucket = "test_bkt"

        e = entry_from_file(bucket, key)

        self.assertEqual(e, {
            "Timestamp": 1313729102832,
            "Reading": {
                "S3Uri": {
                    "Bucket": bucket,
                    "Key": key
                }
            }
        })