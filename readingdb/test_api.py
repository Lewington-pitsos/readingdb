import json
import os
from pprint import pprint
from typing import List
from readingdb.route import Route
from readingdb.routespec import RouteSpec
import tempfile
import unittest
import boto3
import botocore
from moto import mock_s3

from readingdb.download_json import download_json_files
from readingdb.api import API

TEST_BUCKET = "my_bucket"
TEST_PREFIX = "mocks"

def _upload_fixtures(bucket: str, fixtures_dir: str) -> None:
    client = boto3.client("s3")
    fixtures_paths = [
        os.path.join(path,  filename)
        for path, _, files in os.walk(fixtures_dir)
        for filename in files
    ]

    for path in fixtures_paths:
        key = os.path.relpath(path, fixtures_dir)
        client.upload_file(Filename=path, Bucket=bucket, Key=key)

@mock_s3
class TestDownloadJsonFiles(unittest.TestCase):
    region_name = "ap-southeast-2"
    access_key = "fake_access_key"
    secret_key = "fake_secret_key"
    ddb_url = "http://localhost:8000"

    def setUp(self):
        self.current_dir = os.path.dirname(__file__)
        client = boto3.client(
            "s3",
            region_name=self.region_name,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            )
        try:
            s3 = boto3.resource(
                "s3",
                region_name=self.region_name,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                )
            s3.meta.client.head_bucket(Bucket=TEST_BUCKET)
        except botocore.exceptions.ClientError:
            pass
        else:
            err = "{bucket} should not exist.".format(bucket=TEST_BUCKET)
            raise EnvironmentError(err)        
        
        client.create_bucket(
            Bucket=TEST_BUCKET,  
            CreateBucketConfiguration={
                'LocationConstraint': self.region_name
            }
        )
        fixtures_dir = os.path.join(self.current_dir, "test_data/s3_fixtures")
        _upload_fixtures(TEST_BUCKET, fixtures_dir)   

        self.api = API(self.ddb_url) 

        self.api.create_reading_db()
    
    def tearDown(self):
        s3 = boto3.resource(
            "s3",
            region_name=self.region_name,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        )
        bucket = s3.Bucket(TEST_BUCKET)
        for key in bucket.objects.all():
            key.delete()
        bucket.delete()

        self.api.teardown_reading_db()
    
    def test_mocking_works(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            download_json_files(TEST_BUCKET, TEST_PREFIX, tmpdir)
            mock_folder_local_path = os.path.join(tmpdir, TEST_PREFIX)
            self.assertTrue(os.path.isdir(mock_folder_local_path))
            result = os.listdir(mock_folder_local_path)
            desired_result = ["file.json", "apple.json"]
            self.assertCountEqual(result, desired_result)
    
    def test_uploads_small_route(self):
        user_id = "asdy7asdh"

        api = API(self.ddb_url, bucket=TEST_BUCKET)

        with open(self.current_dir + "/test_data/ftg_route.json", "r") as j:
            route_spec_data = json.load(j)

        route_spec = RouteSpec.from_json(route_spec_data)


        route = api.upload(route_spec, user_id)

        user_routes: List[Route] = api.routes_for_user(user_id)
        self.assertEqual(len(user_routes), 1)
        
        expected_sample_data = {
            'Status': 1,
            'RouteID': route.id,
            'UserID': 'asdy7asdh',
            'Name': route.name,
            'SampleData': {
                'PredictionReading': {
                'Reading': {
                    'CrocodileCrackConfidence': 0.17722677,
                    'ImageFileName': '/home/lewington/code/faultnet/data/inference/route_2021_03_19_12_08_03_249/images/snap_2021_03_19_12_08_26_863.jpg',
                    'IsCrocodileCrackFault': False,
                    'IsLatCrackFault': False,
                    'IsLineblurFault': False,
                    'IsLongCrackFault': False,
                    'IsPotholeFault': False,
                    'LatCrackConfidence': 0.07661053,
                    'Latitude': -37.8714232,
                    'LineblurConfidence': 0.09903459,
                    'LongCrackConfidence': 0.6557837,
                    'Longitude': 145.2450816,
                    'PotholeConfidence': 0.14074452
                    },
                    'ReadingID': 0,
                    'RouteID': route.id,
                    'Timestamp': 1616116106935,
                    'Type': 'PredictionReading'
                }
            }
        }

        print(user_routes[0])

        self.assertEqual(user_routes[0], expected_sample_data)
