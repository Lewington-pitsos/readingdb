import os
import json
from pprint import pprint
from readingdb.routespec import RouteSpec
from readingdb.api import API
from readingdb.tutils import create_bucket, teardown_s3_bucket
from readingdb.endpoints import DYNAMO_ENDPOINT, TEST_DYNAMO_ENDPOINT
from typing import Tuple
import unittest
from moto import mock_s3

from readingdb.lamb import handler
from readingdb.getat import get_access_token, CREDENTIALS_FILE

NO_CREDS_REASON = f"no credentials file located at {CREDENTIALS_FILE}"

def credentials_present():
    return os.path.isfile(CREDENTIALS_FILE)

@mock_s3
class TestLambda(unittest.TestCase): 
    TEST_CONTEXT = "TEST_STUB"

    region_name = "ap-southeast-2"
    access_key = "fake_access_key"
    secret_key = "fake_secret_key"
    bucket_name = "my_bucket"
    user_id = "99bf4519-85d9-4726-9471-4c91a7677925"

    # Helper Code
    @classmethod
    def setUpClass(cls):
        if credentials_present():
            cls.access_token = get_access_token()
        else:
            cls.access_token = ""

    def setUp(self) -> None:
        self.current_dir = os.path.dirname(__file__)
        create_bucket(
            self.current_dir, 
            self.region_name, 
            self.access_key, 
            self.secret_key, 
            self.bucket_name,
        )

        self.api = API(TEST_DYNAMO_ENDPOINT, bucket=self.bucket_name) 
        self.api.create_reading_db()

        with open("readingdb/test_data/gps_img_route.json") as f:
            route_json = json.load(f) 
        r = self.api.save_route(RouteSpec.from_json(route_json), self.user_id)
        self.gps_img_route = r

        with open("readingdb/test_data/ftg_route.json") as f:
            route_json = json.load(f) 
        r = self.api.save_route(RouteSpec.from_json(route_json), self.user_id)
        self.tst_route = r

        with open("readingdb/test_data/ftg_20_route.json") as f:
            route_json = json.load(f) 
        r = self.api.save_route(RouteSpec.from_json(route_json), self.user_id)
        self.twenty_route = r

    def tearDown(self):
        teardown_s3_bucket(
            self.region_name,
            self.access_key,
            self.secret_key,
            self.bucket_name
        )

        self.api.teardown_reading_db()

    def test_error_response_on_bad_input(self):
        resp = handler({}, self.TEST_CONTEXT)

        self.assertEqual({
            "Status": "Error",
            "Body": "Invalid Event Syntax"
        }, resp)

        resp = handler({"InvalidKey": 9}, self.TEST_CONTEXT)

        self.assertEqual({
            "Status": "Error",
            "Body": "Invalid Event Syntax"
        }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_error_response_on_nonexistant_type(self):
        resp = handler({
            "Type": "foo",
            "AccessToken": self.access_token,
        }, self.TEST_CONTEXT)

        self.assertEqual({
            "Status": "Error",
            "Body": "Unrecognized event type foo"
        }, resp)

    def test_error_response_on_unauthenticated_event(self):
        resp = handler({
            "Type": "GetRoute",
        }, self.TEST_CONTEXT)

        self.assertEqual({
            "Status": "Error",
            "Body": "Unauthenticated request, no Access Token Provided"
        }, resp)

        resp = handler({
            "Type": "GetRoute",
            "AccessToken": "bad_access_token",
        }, self.TEST_CONTEXT)

        self.assertEqual({
            "Status": "Error",
            "Body": "Unauthenticated request, unrecognized Access Token bad_access_token"
        }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_gets_non_existant_route(self):
        resp = handler({
            "Type": "GetRoute",
            "RouteID": "route-that-doesnt-exist",
            "AccessToken": self.access_token,
        }, self.TEST_CONTEXT)

        self.assertEqual({
            "Status": "Success",
            "Body": None
        }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_gets_readings(self):
        resp = handler({
            "Type": "GetReadings",
            "RouteID": self.twenty_route.id,
            "AccessToken": self.access_token,
        }, self.TEST_CONTEXT)

        self.assertEqual(resp["Status"], "Success")
        self.assertTrue(isinstance(resp["Body"], list))
        self.assertEqual(len(resp["Body"]), 22)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_gets_routes_for_user(self):
        resp = handler({
            "Type": "GetUserRoutes",
            "AccessToken": self.access_token,
        }, self.TEST_CONTEXT)

        self.assertEqual(len(resp["Body"]), 3)
        self.assertTrue(resp["Body"][0]["RouteID"] in [
            self.twenty_route.id,
            self.gps_img_route.id,
            self.tst_route.id
        ])

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_gets_route(self):
        resp = handler({
            "Type": "GetRoute",
            "RouteID": self.twenty_route.id,
            "AccessToken": self.access_token,
        }, self.TEST_CONTEXT)

        self.assertIn("PresignedURL", resp["Body"]["SampleData"]["PredictionReading"]["Reading"])
        del resp["Body"]["SampleData"]["PredictionReading"]["Reading"]["PresignedURL"]

        self.maxDiff = None
        self.assertEqual({
            'Status': 'Success', 
            'Body': {
                'RouteStatus': 1, 
                'Timestamp': 1616116106935,
                'UserID': '99bf4519-85d9-4726-9471-4c91a7677925', 
                'SampleData': {
                    'PredictionReading': {
                        'ReadingID': 0, 
                        'Type': 'PredictionReading', 
                        'Reading': {
                            'S3Uri': {
                                'Bucket': 'my_bucket', 
                                'Key': self.twenty_route.id + 'readingdb/test_data/images/road1.jpg'
                            }, 
                            'Longitude': 145.2450816, 
                            'Latitude': -37.8714232, 
                            'ImageFileName': 'readingdb/test_data/images/road1.jpg', 
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
                                    'Present': False},

                            ],
                        }, 
                        'RouteID': self.twenty_route.id, 
                        'Timestamp': 1616116106935
                    }
                }, 
                'RouteID': self.twenty_route.id, 
                'RouteName': self.twenty_route.name
            }
        }, resp)
