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
class TestAPI(unittest.TestCase):
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
    
    def test_updates_route_name(self):
        user_id = "aghsghavgas"
        api = API(self.ddb_url, bucket=TEST_BUCKET)
        with open(self.current_dir + "/test_data/ftg_route.json", "r") as j:
            route_spec_data = json.load(j)
        route_spec = RouteSpec.from_json(route_spec_data)
        route = api.save_route(route_spec, user_id)

        self.assertEqual(route.name, route.id.split("-")[-1])

        api.update_route_name(route.id, user_id, "Belgrave")

        loaded_route = api.get_route(route.id, user_id)
        self.assertEqual(loaded_route[ReadingRouteKeys.ROUTE_ID], route.id)
        self.assertEqual(loaded_route[RouteKeys.NAME], "Belgrave")

    def test_update_route_status(self):
        user_id = "aghsghavgas"
        api = API(self.ddb_url, bucket=TEST_BUCKET)
        with open(self.current_dir + "/test_data/ftg_route.json", "r") as j:
            route_spec_data = json.load(j)
        route_spec = RouteSpec.from_json(route_spec_data)
        route = api.save_route(route_spec, user_id)

        self.assertEqual(RouteStatus.UPLOADED, route.status)
        api.set_as_predicting(route.id, user_id)

        loaded_route = api.get_route(route.id, user_id)
        self.assertEqual(loaded_route[ReadingRouteKeys.ROUTE_ID], route.id)
        self.assertEqual(loaded_route[RouteKeys.STATUS], RouteStatus.PREDICTING)

        preds = [{
            'Reading': {
                'ImageFileName': "route_2021_03_19_12_08_03_249/images/snap_2021_03_19_12_08_26_863.jpg",
                'PresignedURL': "INVALID_URL",
                'S3Uri': {
                    "Bucket": TEST_BUCKET,
                    "Key": route.id + "route_2021_03_19_12_08_03_249/images/snap_2021_03_19_12_08_26_863.jpg"
                },
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
                'Longitude': 145.2450816,
                'Latitude': -37.8714232,
            },
            'ReadingID': 0,
            'Type': 'PredictionReading',
            'RouteID': route.id,
            'Timestamp': 1616116106935,
        }]

        api.save_predictions(preds, route.id, user_id)

        loaded_route = api.get_route(route.id, user_id)
        self.assertEqual(loaded_route[ReadingRouteKeys.ROUTE_ID], route.id)
        self.assertEqual(loaded_route[RouteKeys.STATUS], RouteStatus.COMPLETE)

    def test_saves_readings_to_existing_route(self):
        user_id = "asdy7asdh"
        route_id = "asdasdasdasd"
        api = API(self.ddb_url, bucket=TEST_BUCKET)

        user_routes = api.routes_for_user(user_id)
        self.assertEqual(len(user_routes), 0)

        api.put_route(Route(
            user_id,
            route_id,
            0
        ))

        user_routes = api.routes_for_user(user_id)
        self.assertEqual(len(user_routes), 1)
        self.assertNotIn("SampleData", user_routes[0])

        readings = api.all_route_readings(route_id)
        self.assertEqual(len(readings), 0)
        print(user_routes)

        with open(self.current_dir + "/test_data/ftg_imgs.json", "r") as j:
            route_spec_data = json.load(j)

        api.save_predictions(route_spec_data, route_id, user_id)

        readings = api.all_route_readings(route_id)
        self.assertEqual(len(readings), 22)

    def test_uploads_small_route(self):
        user_id = "asdy7asdh"
        api = API(self.ddb_url, bucket=TEST_BUCKET)

        with open(self.current_dir + "/test_data/ftg_route.json", "r") as j:
            route_spec_data = json.load(j)

        route_spec = RouteSpec.from_json(route_spec_data)
        route = api.save_route(route_spec, user_id)

        user_routes = api.routes_for_user(user_id)
        self.assertEqual(len(user_routes), 1)

        expected_sample_data = {
            'RouteStatus': 1,
            'RouteID': route.id,
            'Timestamp': 1616116106935,
            'UserID': 'asdy7asdh',
            'SampleData': {
                'PredictionReading': {
                'Reading': {
                    "ImageFileName": 'readingdb/test_data/images/road1.jpg',
                    'S3Uri': {
                        "Bucket": TEST_BUCKET,
                        "Key": route.id + 'readingdb/test_data/images/road1.jpg'
                    },
                    "Entities": [
                        {'Confidence': 0.6557837,
                        'Name': 'LongCrack',
                        'Present': False},
                        {'Confidence': 0.07661053,
                        'Name': 'LatCrack',
                        'Present': False},
                        {'Confidence': 0.17722677,
                        'Name': 'CrocodileCrack',
                        'Present': False},
                        {'Confidence': 0.14074452,
                        'Name': 'Pothole',
                        'Present': False},
                        {'Confidence': 0.09903459,
                        'Name': 'Lineblur',
                        'Present': False}
                    ],
                    'Longitude': 145.2450816,
                    'Latitude': -37.8714232,
                },
                'ReadingID': 0,
                'Type': 'PredictionReading',
                'RouteID': route.id,
                'Timestamp': 1616116106935
                }
            },
            'RouteName': route.name,
        }

        self.assertIn("PresignedURL", user_routes[0]["SampleData"]["PredictionReading"]['Reading'])
        del user_routes[0]["SampleData"]["PredictionReading"]['Reading']['PresignedURL']
        self.maxDiff = None
        self.assertEqual(expected_sample_data, user_routes[0])

        s3 = boto3.resource(
            "s3",
            region_name=self.region_name,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        )

        bucket = s3.Bucket(TEST_BUCKET)

        bucket_objects = []

        for my_bucket_object in bucket.objects.all():
            bucket_objects.append(my_bucket_object.key)

        self.assertEqual(set(bucket_objects), set([
            "mocks/apple.json", 
            "mocks/file.json",
            route.id + 'readingdb/test_data/images/road1.jpg'
,
        ]))