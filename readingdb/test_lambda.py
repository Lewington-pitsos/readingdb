import json
import os
from pprint import pprint
from typing import Tuple
import unittest
import time

import boto3

from readingdb.lamb import handler
from readingdb.getat import get_access_token, CREDENTIALS_FILE

NO_CREDS_REASON = f"no credentials file located at {CREDENTIALS_FILE}"

def credentials_present():
    return os.path.isfile(CREDENTIALS_FILE)

class TestLambda(unittest.TestCase): 
    # Helper Code

    @classmethod
    def setUpClass(cls):
        if credentials_present():
            cls.access_token = get_access_token()
        else:
            cls.access_token = ""

    # Tests

    def test_error_response_on_bad_input(self):
        resp = handler({}, None)

        self.assertEqual({
            "Status": "Error",
            "Body": "Invalid Event Syntax"
        }, resp)

        resp = handler({"InvalidKey": 9}, None)

        self.assertEqual({
            "Status": "Error",
            "Body": "Invalid Event Syntax"
        }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_error_response_on_nonexistant_type(self):
        resp = handler({
            "Type": "foo",
            "AccessToken": self.access_token,
        }, None)

        self.assertEqual({
            "Status": "Error",
            "Body": "Unrecognized event type foo"
        }, resp)

    def test_error_response_on_unauthenticated_event(self):
        resp = handler({
            "Type": "GetRoute",
        }, None)

        self.assertEqual({
            "Status": "Error",
            "Body": "Unauthenticated request, no Access Token Provided"
        }, resp)

        resp = handler({
            "Type": "GetRoute",
            "AccessToken": "bad_access_token",
        }, None)

        self.assertEqual({
            "Status": "Error",
            "Body": "Unauthenticated request, unrecognized Access Token bad_access_token"
        }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_gets_non_existant_route(self):
        resp = handler({
            "Type": "GetRoute",
            "RouteID": "1617270526.9399285-8C4ZCJ1WMM5360X",
            "AccessToken": self.access_token,
        }, None)

        self.assertEqual({
            "Status": "Success",
            "Body": None
        }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_gets_readings(self):
        resp = handler({
            "Type": "GetReadings",
            "RouteID": "1617839705.6470242-61ZDT8KWSA41RQV",
            "AccessToken": self.access_token,
        }, None)

        self.assertEqual(resp["Status"], "Success")
        self.assertTrue(isinstance(resp["Body"], list))
        self.assertEqual(len(resp["Body"]), 22)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_gets_route(self):
        resp = handler({
            "Type": "GetRoute",
            "RouteID": "1617839705.6470242-61ZDT8KWSA41RQV",
            "AccessToken": self.access_token,
        }, None)
    
        self.assertEqual({
            'Status': 'Success', 
            'Body': {
                'RouteStatus': 1, 
                'UserID': '99bf4519-85d9-4726-9471-4c91a7677925', 
                'SampleData': {
                    'PredictionReading': {
                        'ReadingID': 0, 
                        'Type': 'PredictionReading', 
                        'Reading': {
                            'IsCrocodileCrackFault': False, 
                            'S3Uri': {
                                'Bucket': 'mobileappsessions172800-main', 
                                'Key': '1617839705.6470242-61ZDT8KWSA41RQV/home/lewington/code/faultnet/data/inference/route_2021_03_19_12_08_03_249/images/snap_2021_03_19_12_08_26_863.jpg'
                            }, 
                            'LatCrackConfidence': 0.07661053, 
                            'IsLatCrackFault': False, 
                            'Latitude': -37.8714232, 
                            'LongCrackConfidence': 0.6557837, 
                            'PotholeConfidence': 0.14074452, 
                            'LineblurConfidence': 0.09903459, 
                            'Longitude': 145.2450816, 
                            'IsLineblurFault': False, 
                            'ImageFileName': '/home/lewington/code/faultnet/data/inference/route_2021_03_19_12_08_03_249/images/snap_2021_03_19_12_08_26_863.jpg', 
                            'IsPotholeFault': False, 
                            'IsLongCrackFault': False, 
                            'CrocodileCrackConfidence': 0.17722677
                        }, 
                        'RouteID': '1617839705.6470242-61ZDT8KWSA41RQV', 
                        'Timestamp': 1616116106935
                    }
                }, 
                'RouteID': '1617839705.6470242-61ZDT8KWSA41RQV', 
                'RouteName': '61ZDT8KWSA41RQV'
            }
        }, resp)
