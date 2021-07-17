from collections import defaultdict
from io import BytesIO
import os
import zipfile
import boto3
import json
from readingdb.constants import *
from unittest import mock
from readingdb.routespec import RouteSpec
from readingdb.api import API
from readingdb.tutils import roads_api_test
from readingdb.tutils import Increment, create_bucket, teardown_s3_bucket
from readingdb.endpoints import DYNAMO_ENDPOINT, TEST_BUCKET, TEST_DYNAMO_ENDPOINT
import unittest
from moto import mock_s3

from readingdb.lamb import test_handler
from readingdb.getat import get_access_token, CREDENTIALS_FILE

NO_CREDS_REASON = f'no credentials file located at {CREDENTIALS_FILE}'
TEST_CONTEXT = 'TEST_STUB'

def credentials_present():
    return os.path.isfile(CREDENTIALS_FILE)

class TestLambda(unittest.TestCase): 
    @classmethod
    def setUpClass(cls):
        if credentials_present():
            cls.access_token = get_access_token()
        else:
            cls.access_token = ''

class TestBasic(TestLambda):
    def test_error_response_on_bad_input(self):
        resp = test_handler({}, TEST_CONTEXT)
        self.assertEqual({
            'Status': 'Error',
            'Body': 'Invalid Event Syntax'
        }, resp)

        resp = test_handler({'InvalidKey': 9}, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Invalid Event Syntax'
        }, resp)

    def test_correct_error_on_malformed_s3_event(self):
        resp = test_handler({
            'Records': []
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Invalid Event Syntax'
        }, resp)

    def test_correct_error_on_unauthenticated_upload_event(self):
        resp = test_handler({
             'Type': 'NotifyUploadComplete'
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Unauthenticated request, no Access Token Provided'
        }, resp)

    def test_correct_error_on_unauthenticated_process_upload_event(self):
        resp = test_handler({
             'Type': 'ProcessUpload'
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Unauthenticated request, no Access Token Provided'
        }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_correct_error_on_malformed_upload_event(self):
        resp = test_handler({
             'Type': 'NotifyUploadComplete',
             'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Bad Format Error: key Bucket missing from event'
        }, resp)

        resp = test_handler({
             'Type': 'NotifyUploadComplete',
             'AccessToken': self.access_token,
             'Bucket': 'somebucket'
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Bad Format Error: key Key missing from event'
        }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_correct_error_on_malformed_process_upload_event(self):
        resp = test_handler({
             'Type': 'ProcessUpload',
             'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Bad Format Error: key Bucket missing from event'
        }, resp)

        resp = test_handler({
             'Type': 'ProcessUpload',
             'AccessToken': self.access_token,
             'Bucket': 'somebucket'
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Bad Format Error: key Key missing from event'
        }, resp)

        resp = test_handler({
             'Type': 'ProcessUpload',
             'AccessToken': self.access_token,
             'Key': "a9a9a9a9a9a9a.json",
             'Bucket': 'somebucket'
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Bad Format Error: key GroupID missing from event'
        }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_error_response_on_delete_event(self):
        resp = test_handler({
            'Type': 'DeleteRoute',
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Bad Format Error: key RouteID missing from event'
        }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_error_response_on_save_predictions_event(self):
        resp = test_handler({
            'Type': 'SavePredictions',
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Bad Format Error: key RouteID missing from event'
        }, resp)

        resp = test_handler({
            'Type': 'SavePredictions',
            'RouteID': "1721739812-1238123",
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Bad Format Error: key Predictions missing from event'
        }, resp)

        # resp = test_handler({
        #     'Type': 'SavePredictions',
        #     'RouteID': "1721739812-1238123",
        #     'Predictions': {},
        #     'AccessToken': self.access_token,
        # }, TEST_CONTEXT)

        # self.assertEqual({
        #     'Status': 'Error',
        #     'Body': 'Bad Format Error: key GroupID missing from event'
        # }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_error_response_on_road_snap_event(self):
        resp = test_handler({
            'Type': 'SnapToRoads',
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Bad Format Error: key Points missing from event'
        }, resp)

        resp = test_handler({
            'Type': 'SnapToRoads',
            'Points': [],
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Not Enough Points Given (0)'
        }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    @roads_api_test
    def test_road_snap_event(self):
        pnts = [
            {'lat': -36.8782232, 'lng': 146.12628160000003},
            {'lat': -36.8518232, 'lng': 146.14488160000002},
            {'lat': -36.8123232, 'lng': 146.15788160000002},
            {'lat': -36.8106232, 'lng': 146.18498160000001},
            {'lat': -36.8058232, 'lng': 146.21268160000002},
            {'lat': -36.7679232, 'lng': 146.25158160000004},
            {'lat': -36.7577232, 'lng': 146.27578160000004},
            {'lat': -36.7316232, 'lng': 146.27978160000004},
            {'lat': -36.6926232, 'lng': 146.31318160000004},
            {'lat': -36.6641232, 'lng': 146.34268160000005},
            {'lat': -36.642623199999996, 'lng': 146.34758160000004},
            {'lat': -36.6061232, 'lng': 146.36898160000004},
            {'lat': -36.5783232, 'lng': 146.38298160000005},
            {'lat': -36.5487232, 'lng': 146.42298160000004},
            {'lat': -36.5107232, 'lng': 146.43248160000005},
            {'lat': -36.4983232, 'lng': 146.46168160000005},
            {'lat': -36.492623200000004, 'lng': 146.47348160000004},
            {'lat': -36.49162320000001, 'lng': 146.51188160000004},
            {'lat': -36.490723200000005, 'lng': 146.51388160000005},
            {'lat': -36.48782320000001, 'lng': 146.51758160000006},
            {'lat': -36.47182320000001, 'lng': 146.51768160000006},
            {'lat': -36.46052320000001, 'lng': 146.54788160000007},
            {'lat': -36.43902320000001, 'lng': 146.55778160000006},
            {'lat': -36.40092320000001, 'lng': 146.58598160000005},
            {'lat': -36.36652320000001, 'lng': 146.59298160000006},
            {'lat': -36.34632320000001, 'lng': 146.60488160000006},
            {'lat': -36.32642320000001, 'lng': 146.62048160000006},
            {'lat': -36.32622320000001, 'lng': 146.62048160000006},
            {'lat': -36.30992320000001, 'lng': 146.63848160000006},
            {'lat': -36.29092320000001, 'lng': 146.64848160000005},
            {'lat': -36.25712320000001, 'lng': 146.68448160000005},
            {'lat': -36.224923200000006, 'lng': 146.70968160000007},
            {'lat': -36.19632320000001, 'lng': 146.74638160000006},
            {'lat': -36.171623200000006, 'lng': 146.76858160000006},
            {'lat': -36.15602320000001, 'lng': 146.78528160000005},
            {'lat': -36.15002320000001, 'lng': 146.79948160000004},
            {'lat': -36.143123200000005, 'lng': 146.80808160000004},
            {'lat': -36.13402320000001, 'lng': 146.81158160000004},
            {'lat': -36.09572320000001, 'lng': 146.83088160000003},
            {'lat': -36.07712320000001, 'lng': 146.85548160000002},
            {'lat': -36.07202320000001, 'lng': 146.8935816}
        ]

        resp = test_handler({
            'Type': 'SnapToRoads',
            'Points': pnts,
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertNotEqual(len(pnts), len(resp['Body']['Points']))
        self.assertEqual({
            'Status': 'Error',
            'Body': {
                'Points': [
                    {'lat': -36.8518232, 'lng': 146.14488160000002},
                    {'lat': -36.8123232, 'lng': 146.15788160000002},
                    {'lat': -36.8106232, 'lng': 146.18498160000001},
                    {'lat': -36.8058232, 'lng': 146.21268160000002},
                    {'lat': -36.7679232, 'lng': 146.25158160000004},
                    {'lat': -36.7577232, 'lng': 146.27578160000004},
                    {'lat': -36.7316232, 'lng': 146.27978160000004},
                    {'lat': -36.6926232, 'lng': 146.31318160000004},
                    {'lat': -36.6641232, 'lng': 146.34268160000005},
                    {'lat': -36.642623199999996, 'lng': 146.34758160000004},
                    {'lat': -36.6061232, 'lng': 146.36898160000004},
                    {'lat': -36.5783232, 'lng': 146.38298160000005},
                    {'lat': -36.5487232, 'lng': 146.42298160000004},
                    {'lat': -36.5107232, 'lng': 146.43248160000005},
                    {'lat': -36.4983232, 'lng': 146.46168160000005},
                    {'lat': -36.492623200000004, 'lng': 146.47348160000004},
                    {'lat': -36.49162320000001, 'lng': 146.51188160000004},
                    {'lat': -36.490723200000005, 'lng': 146.51388160000005},
                    {'lat': -36.48782320000001, 'lng': 146.51758160000006},
                    {'lat': -36.47182320000001, 'lng': 146.51768160000006},
                    {'lat': -36.46052320000001, 'lng': 146.54788160000007},
                    {'lat': -36.43902320000001, 'lng': 146.55778160000006},
                    {'lat': -36.40092320000001, 'lng': 146.58598160000005},
                    {'lat': -36.36652320000001, 'lng': 146.59298160000006},
                    {'lat': -36.34632320000001, 'lng': 146.60488160000006},
                    {'lat': -36.32642320000001, 'lng': 146.62048160000006},
                    {'lat': -36.32622320000001, 'lng': 146.62048160000006},
                    {'lat': -36.30992320000001, 'lng': 146.63848160000006},
                    {'lat': -36.29092320000001, 'lng': 146.64848160000005},
                    {'lat': -36.25712320000001, 'lng': 146.68448160000005},
                    {'lat': -36.224923200000006, 'lng': 146.70968160000007},
                    {'lat': -36.19632320000001, 'lng': 146.74638160000006},
                    {'lat': -36.171623200000006, 'lng': 146.76858160000006},
                    {'lat': -36.15602320000001, 'lng': 146.78528160000005},
                    {'lat': -36.15002320000001, 'lng': 146.79948160000004},
                    {'lat': -36.143123200000005, 'lng': 146.80808160000004},
                    {'lat': -36.13402320000001, 'lng': 146.81158160000004},
                    {'lat': -36.09572320000001, 'lng': 146.83088160000003},
                    {'lat': -36.07712320000001, 'lng': 146.85548160000002},
                    {'lat': -36.07202320000001, 'lng': 146.8935816}
                ]
            },
        }, resp)

    def test_error_response_on_unauthenticated_event(self):
        resp = test_handler({
            'Type': 'GetRoute',
        }, TEST_CONTEXT)
        self.assertEqual({
            'Status': 'Error',
            'Body': 'Unauthenticated request, no Access Token Provided'
        }, resp)
        resp = test_handler({
            'Type': 'GetRoute',
            'AccessToken': 'bad_access_token',
        }, TEST_CONTEXT)
        self.assertEqual({
            'Status': 'Error',
            'Body': 'Unauthenticated request, unrecognized Access Token bad_access_token'
        }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_error_response_on_nonexistant_type(self):
        resp = test_handler({
            'Type': 'foo',
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Unrecognized event type foo'
        }, resp)

@mock_s3
class TestLambdaRW(TestLambda):
    region_name = 'ap-southeast-2'
    access_key = 'fake_access_key'
    secret_key = 'fake_secret_key'
    bucket_name = TEST_BUCKET
    user_id = '99bf4519-85d9-4726-9471-4c91a7677925'
    tmp_bucket = TEST_BUCKET

    def setUp(self) -> None:
        self.current_dir = os.path.dirname(__file__)
        create_bucket(
            self.current_dir, 
            self.region_name, 
            self.access_key, 
            self.secret_key, 
            self.bucket_name,
        )
        
        self.api = API(TEST_DYNAMO_ENDPOINT, bucket=self.bucket_name, tmp_bucket=self.tmp_bucket) 
        self.api.create_reading_db()

        org_data = self.api.put_org('Frontline Data Systems')
        self.default_group = org_data[Constants.ORG_GROUP]
        self.org_name = org_data[Constants.ORG_NAME]

    def tearDown(self):
        self.api.teardown_reading_db()
        teardown_s3_bucket(
            self.region_name,
            self.access_key,
            self.secret_key,
            self.bucket_name
        )      

class TestLambdaW(TestLambdaRW):
    @unittest.skip('This make an actual call to fargate')
    def test_correct_upload_event_handling(self):
        test_handler({
             'Type': 'NotifyUploadComplete',
             'AccessToken': 'eyJraWQiOiI0QXl3TjdidExEWm1RWFBEdVpxZ3JRTVk2MkVheXc0ZlN6eXBNcFI2bDh3PSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI5OWJmNDUxOS04NWQ5LTQ3MjYtOTQ3MS00YzkxYTc2Nzc5MjUiLCJjb2duaXRvOmdyb3VwcyI6WyJhZG1pbiJdLCJldmVudF9pZCI6IjljYjMyZjRjLWFhMDktNDk4Yi1hYjkzLTk5ODE3ZjdmNGQxYyIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE2MTgyNjc5MzEsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5hcC1zb3V0aGVhc3QtMi5hbWF6b25hd3MuY29tXC9hcC1zb3V0aGVhc3QtMl9jdHBnbTBLdzQiLCJleHAiOjE2MTgyNzE1MzEsImlhdCI6MTYxODI2NzkzMSwianRpIjoiNmRkNGZiNWMtMTZhZS00N2JjLTg4OTEtODRkYjUzNjg0NmMwIiwiY2xpZW50X2lkIjoiNHVxaHFzb29lNDNlYnRxMG9idm4wbG03dWkiLCJ1c2VybmFtZSI6ImZkc2FkbWluIn0.EgNiuZYENTdIF7t7Zs0LC0UEPaMSc1M66fxfi4OpoLcKvCXdLax6r4wa0gdeL96N6x2PzpBmdxEoeZfSnIFq2NNtcLPXYpmONGgbmP4bxdQW1FcplE6dlvkfo6UnQQdmjTd6r6rTq6CHlHBskFWfi7YRcdbtFf8Ic9nIB2G8J8EkjN1cwGrUUrQ3CqaOuLNjUqxtP6fYgrqEk6lseWVp4P33HK8zOwPUxUuqjwtWfJK_Mchy0QL_K-HpnyUoXU5cv63_PY_OI63QYz5FHFtloTwj1iWqGdE43_tH8AdT3UJpmFNHwHijqVVpsFVmTowRuw1QskdZP-yHK4p7Ea8Y7Q',
             'Bucket': 'mobileappsessions172800-main',
             'Key': 'public/route_2021_04_12_20_59_16_782.zip',
             'RouteName': 'Blinkins Ct.'
        }, TEST_CONTEXT)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_integrates_uploaded_files(self):
        s3_resource = boto3.resource('s3')
        zip_obj = s3_resource.Object(
            bucket_name=TEST_BUCKET, 
            key='mocks/route_1621394080578.zip'
        )
        buffer = BytesIO(zip_obj.get()['Body'].read())
        d = zipfile.ZipFile(buffer)
        key = 'mocks/route_1621394080578.zip'

        for filename in d.namelist():
            s3_filename = f'{key.split(".")[0]}/{filename.split("/")[-1]}'
            s3_resource.meta.client.upload_fileobj(
                d.open(filename),
                Bucket=TEST_BUCKET,
                Key=s3_filename
            )

        resp = test_handler({
             'Type': 'ProcessUpload',
             'AccessToken': self.access_token,
             'Bucket': TEST_BUCKET,
             'GroupID': self.default_group,
             'Key': 'mocks/route_1621394080578',
             'RouteName': 'Jenkins Way'
        }, TEST_CONTEXT)

        self.assertEqual('Success', resp['Status'])
        self.assertIn('RouteID', resp['Body'])
        rid = resp['Body']['RouteID']
        resp = test_handler({
            'Type': 'GetReadings',
            'RouteID': rid,
            'PredictionOnly': False,
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual(42, len(resp['Body']['Readings']))

        resp = test_handler({
            'Type': 'GetRoute',
            'RouteID': rid,
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)
        self.assertEqual('Jenkins Way', resp['Body']['RouteName'])

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_gets_non_existant_route(self):
        resp = test_handler({
            'Type': 'GetRoute',
            'RouteID': 'route-that-doesnt-exist',
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Success',
            'Body': None
        }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_saves_data_access_groups(self):
        resp = test_handler({
            'Type': 'AddUser',
            'UserID': "a98s7das87dba0sa7gdas87",
            "OrgName": self.org_name,
            'DataAccessGroups': [
                {'GroupName': 'Roora', 'GroupID': 'a9sd6a7s128123'},
                {'GroupName': 'Vicroads', 'GroupID': '12--1tg122168'}
            ],
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Success',
            'Body': None
        }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_handles_user_put_request_correctly(self):
        resp = test_handler({
            'Type': 'AddUser',
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Bad Format Error: key UserID missing from event'
        }, resp)

        resp = test_handler({
            'Type': 'AddUser',
            'UserID': 'too-short',
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'User ID too-short was too short, must be at least 20 characters long'
        }, resp)

        resp = test_handler({
            'Type': 'AddUser',
            'UserID': 'aaaaaaaaaaaaaaaa-sd-asdas-dasd-asd',
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Bad Format Error: key OrgName missing from event'
        }, resp)

        resp = test_handler({
            'Type': 'AddUser',
            'UserID': 'aaaaaaaaaaaaaaaa-sd-asdas-dasd-asd',
            'OrgName': self.org_name,
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Success',
            'Body': None}
        , resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    @mock.patch('time.time', mock.MagicMock(side_effect=Increment(1619496879)))
    def test_uploads_predictions(self):
        group_id = 'apapapa'
        layer_id = 'aalalala'
        self.api.put_user(self.org_name, self.user_id)
        self.api.user_add_group(self.user_id, group_id)
        self.api.group_add_layer(group_id, layer_id)

        with open('readingdb/test_data/long_route.json') as f:
            route_json = json.load(f) 
        route = self.api.save_route(RouteSpec.from_json(route_json), self.user_id, layer_id)

        resp = test_handler({
            'Type': 'GetReadings',
            'RouteID': route.id,
            'PredictionOnly': False,
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual(resp['Status'], 'Success')
        self.assertEqual(len(resp['Body']['Readings']), 181)

        with open('readingdb/test_data/ftg_imgs.json') as f:
            pred_json = json.load(f)

        for reading in pred_json:
            reading['Reading']['ImageFileName'] = "readingdb/test_data/route_imgs/route_2021_04_07_17_14_36_709/2021_04_07_17_14_49_386-25.jpg"

        resp = test_handler({
            'Type': 'SavePredictions',
            'RouteID': route.id,
            'Predictions': pred_json,
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual(22, len(resp['Body']['SavedReadings']))
        resp = test_handler({
            'Type': 'GetReadings',
            'RouteID': route.id,
            'PredictionOnly': False,
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual(resp['Status'], 'Success')
        self.assertEqual(len(resp['Body']['Readings']), 182)

        annotator_count = defaultdict(lambda: 0)
        for r in resp['Body']['Readings']:
            if r['Type'] == 'PredictionReading':
                annotator_count[r['AnnotatorID']] += 1

        self.assertEqual(annotator_count["99994519-85d9-4726-9471-4c91a7677925"], 1)

        for reading in pred_json:
            reading['AnnotatorID'] = 'a8s8as78a7a7a7a7a'

        resp = test_handler({
            'Type': 'SavePredictions',
            'RouteID': route.id,
            'Predictions': pred_json,
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        resp = test_handler({
            'Type': 'GetReadings',
            'RouteID': route.id,
            'PredictionOnly': False,
            'AnnotatorPreference': ['a8s8as78a7a7a7a7a'],
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual(resp['Status'], 'Success')
        self.assertEqual(len(resp['Body']['Readings']), 182)

        annotator_count = defaultdict(lambda: 0)
        for r in resp['Body']['Readings']:
            if r['Type'] == 'PredictionReading':
                annotator_count[r['AnnotatorID']] += 1

        self.assertEqual(annotator_count['a8s8as78a7a7a7a7a'], 1)
        self.assertEqual(annotator_count["99994519-85d9-4726-9471-4c91a7677925"], 0)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    @mock.patch('time.time', mock.MagicMock(side_effect=Increment(1619496879)))
    def test_uploads_predictions_for_long_route(self):
        group_id = 'apapapa'
        layer_id = 'aalalala'
        self.api.put_user(self.org_name, self.user_id)
        self.api.user_add_group(self.user_id, group_id)
        self.api.group_add_layer(group_id, layer_id)

        with open('readingdb/test_data/sydney_route_short.json') as f:
            route_json = json.load(f) 
        r = self.api.save_route(RouteSpec.from_json(route_json), self.user_id, layer_id)

        resp = test_handler({
            'Type': 'GetReadings',
            'RouteID': r.id,
            'AnnotatorPreference': [
                '99bf4519-85d9-4726-9471-4c91a7677925'
            ],
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual(resp['Status'], 'Success')
        self.assertEqual(len(resp['Body']['Readings']), 713)

        resp = test_handler({
            'Type': 'GetReadings',
            'RouteID': r.id,
            'AnnotatorPreference': [
                '99bf4519-85d9-4726-9471-4c91a7677925'
            ],
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual(resp['Status'], 'Success')
        self.assertEqual(len(resp['Body']['Readings']), 713)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    @mock.patch('time.time', mock.MagicMock(side_effect=Increment(1619496879)))
    def test_returns_s3_url_if_response_body_too_large(self):
        group_id = 'apapapa'
        layer_id = 'aalalala'
        self.api.put_user(self.org_name, self.user_id)
        self.api.user_add_group(self.user_id, group_id)
        self.api.group_add_layer(group_id, layer_id)
        
        with open('readingdb/test_data/sydney_route_short.json') as f:
            route_json = json.load(f) 
        r = self.api.save_route(RouteSpec.from_json(route_json), self.user_id, layer_id)

        s3 = boto3.resource('s3', region_name=REGION_NAME)
        bucket = s3.Bucket(TEST_BUCKET)
        bucket_objects = []
        for my_bucket_object in bucket.objects.all():
            bucket_objects.append(my_bucket_object.key)

        self.assertEqual(len(bucket_objects), 717)
        resp = test_handler({
            'Type': 'GetReadings',
            'RouteID': r.id,
            'AnnotatorPreference': [
                '99bf4519-85d9-4726-9471-4c91a7677925'
            ],
            'AccessToken': self.access_token,
        }, TEST_CONTEXT, size_limit=500)

        self.assertIn('Bucket', resp['Body']['Readings'])
        self.assertIn('Key', resp['Body']['Readings'])
        bucket_objects = []
        for my_bucket_object in bucket.objects.all():
            bucket_objects.append(my_bucket_object.key)
        self.assertEqual(len(bucket_objects), 718)

@mock_s3
class TestLambdaR(TestLambdaRW): 
    @mock.patch('time.time', mock.MagicMock(side_effect=Increment(1619496879)))
    def setUp(self) -> None:
        super().setUp()

        self.layer_id = 'omni-layer'
        self.group_id = 'omni-group'
        
        self.api.user_add_group(self.user_id, self.group_id)
        self.api.put_layer(self.layer_id)
        self.api.group_add_layer(self.group_id, self.layer_id)

        with open('readingdb/test_data/long_route.json') as f:
            route_json = json.load(f) 
        r = self.api.save_route(RouteSpec.from_json(route_json), self.user_id, self.layer_id)
        self.long_route = r

        with open('readingdb/test_data/ftg_route.json') as f:
            route_json = json.load(f) 
        r = self.api.save_route(RouteSpec.from_json(route_json), self.user_id, self.layer_id)
        self.tst_route = r

        with open('readingdb/test_data/ftg_20_route.json') as f:
            route_json = json.load(f) 
        r = self.api.save_route(RouteSpec.from_json(route_json), self.user_id, self.layer_id)
        self.twenty_route = r

    def tearDown(self):
        super().tearDown()

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_gets_routes_for_user(self):
        resp = test_handler({
            'Type': 'GetUserRoutes',
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual(len(resp['Body']), 3)
        self.assertTrue(resp['Body'][0]['RouteID'] in [
            self.twenty_route.id,
            self.long_route.id,
            self.tst_route.id
        ])

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_gets_route(self):
        resp = test_handler({
            'Type': 'GetRoute',
            'RouteID': self.twenty_route.id,
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertIn('PresignedURL', resp['Body']['SampleData']['PredictionReading']['Reading'])
        del resp['Body']['SampleData']['PredictionReading']['Reading']['PresignedURL']

        self.maxDiff = None

        self.assertIn('LastUpdated', resp['Body'])
        del resp['Body']['LastUpdated']
        user_id = resp['Body']['SampleData']['PredictionReading']['ReadingID']
        self.assertEqual({
            'Status': 'Success', 
            'Body': {
                'RouteStatus': 1, 
                'Timestamp': 1616116106935,
                'SampleData': {
                    'PredictionReading': {
                        'AnnotationTimestamp': 2378910,
                        'AnnotatorID': '99994519-85d9-4726-9471-4c91a7677925',
                        'Geohash': 'r1r291',
                        'PK': 'r1r291',
                        'ReadingID': user_id, 
                        'Type': 'PredictionReading', 
                        'Reading': {
                            'S3Uri': {
                                'Bucket': TEST_BUCKET,
                                'Key': self.twenty_route.id + 'readingdb/test_data/images/road1.jpg'
                            }, 
                            'Longitude': 145.2450816, 
                            'Latitude': -37.8714232, 
                            'ImageFileName': 'readingdb/test_data/images/road1.jpg', 
                            'Entities': [
                                {'Confidence': 0.6557837,
                                    'Name': 'LongCrack',
                                    'Severity': 1.3,
                                    'Present': False},
                                {'Confidence': 0.07661053,
                                    'Name': 'LatCrack',
                                    'Severity': 1.03,
                                    'Present': False},
                                {'Confidence': 0.17722677,
                                    'Name': 'CrocodileCrack',
                                    'Severity': 1.34,
                                    'Present': False},
                                {'Confidence': 0.14074452,
                                    'Name': 'Pothole',
                                    'Severity': 1.12,
                                    'Present': False},
                                {'Confidence': 0.09903459,
                                    'Name': 'Lineblur',
                                    'Severity': 1.1,
                                    'Present': False},
                            ],
                        }, 
                        'RouteID': self.twenty_route.id,
                        'SK': 'PredictionReading#' + user_id,
                        'Timestamp': 1616116106935
                    }
                }, 
                'Geohashes': {'r1r291'},
                'RouteID': self.twenty_route.id,
                'PK': 'Route',
                'SK': 'Route#' + self.twenty_route.id,
                'RouteName': self.twenty_route.name
            }
        }, resp)
