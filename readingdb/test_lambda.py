import json
import os
from pprint import pprint
from typing import Tuple
import unittest
import time

import boto3

from readingdb.lamb import handler


CURRENT_DIR = os.path.dirname(__file__)

CREDENTIALS_FILE = CURRENT_DIR + "/test_data/fdsadmin.json"
NO_CREDS_REASON = f"no credentials file located at {CREDENTIALS_FILE}"

def credentials_present():
    return os.path.isfile(CREDENTIALS_FILE)

class TestLambda(unittest.TestCase): 
    # Helper Code

    USERNAME_KEY = "username"
    PASSWORD_KEY = "password"
    CLIENT_ID = "client_id"

    ACCESS_TOKEN_KEY = 'AccessToken'
    AUTH_RESULT_KEY = 'AuthenticationResult'

    @classmethod
    def setUpClass(cls):
        if credentials_present():
            cls.access_token = cls.get_access_token()
        else:
            cls.access_token = ""
    
    @classmethod
    def get_credentials(cls) -> Tuple[str, str, str]:
        with open(CREDENTIALS_FILE, "r") as f:
            creds = json.load(f)
        
        return creds[cls.USERNAME_KEY], creds[cls.PASSWORD_KEY], creds[cls.CLIENT_ID]

    @classmethod
    def get_access_token(cls) -> str:
        cclient = boto3.client('cognito-idp', region_name="ap-southeast-2")

        uname, pwd, cid = cls.get_credentials()

        auth_resp = cclient.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': uname,
                'PASSWORD': pwd
            },
            ClientId=cid
        )

        return auth_resp[cls.AUTH_RESULT_KEY][cls.ACCESS_TOKEN_KEY]

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
