import json
import os
from pprint import pprint
from readingdb.route import Route
from readingdb.routestatus import RouteStatus
from readingdb.constants import ReadingRouteKeys, RouteKeys
from typing import List
from readingdb.routespec import RouteSpec
import tempfile
import unittest
import boto3
import botocore
from moto import mock_s3

from readingdb.download_json import download_json_files
from readingdb.api import API
from readingdb.unzipper import Unzipper
from readingdb.tutils import *

@mock_s3
class TestAPI(unittest.TestCase):
    region_name = "ap-southeast-2"
    access_key = "fake_access_key"
    secret_key = "fake_secret_key"
    ddb_url = "http://localhost:8000"
    bucket_name = "my_bucket"
    test_prefix = "mocks"

    def setUp(self):
        self.current_dir = os.path.dirname(__file__)
        create_bucket(
            self.current_dir, 
            self.region_name, 
            self.access_key, 
            self.secret_key, 
            self.bucket_name
        )

        self.api = API(self.ddb_url) 
        self.api.create_reading_db()
    
    def tearDown(self):
        teardown_s3_bucket(
            self.region_name,
            self.access_key,
            self.secret_key,
            self.bucket_name
        )

        self.api.teardown_reading_db()

    def test_mocking_works(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            download_json_files(self.bucket_name, self.test_prefix, tmpdir)
            mock_folder_local_path = os.path.join(tmpdir, self.test_prefix)
            self.assertTrue(os.path.isdir(mock_folder_local_path))
            result = os.listdir(mock_folder_local_path)
            desired_result = ["file.json", "apple.json"]
            self.assertCountEqual(result, desired_result)
