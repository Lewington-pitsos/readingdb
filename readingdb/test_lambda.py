import os
import json
from unittest import mock
from readingdb.routespec import RouteSpec
from readingdb.api import API
from readingdb.tutils import Increment, create_bucket, teardown_s3_bucket
from readingdb.endpoints import DYNAMO_ENDPOINT, TEST_BUCKET, TEST_DYNAMO_ENDPOINT
import unittest
from moto import mock_s3, mock_sqs

from readingdb.lamb import handler
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
        resp = handler({}, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Invalid Event Syntax'
        }, resp)

        resp = handler({'InvalidKey': 9}, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Invalid Event Syntax'
        }, resp)

    def test_correct_error_on_malformed_s3_event(self):
        resp = handler({
            'Records': []
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Invalid Event Syntax'
        }, resp)

    def test_correct_error_on_unauthenticated_upload_event(self):
        resp = handler({
             'Type': 'NotifyUploadComplete'
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Unauthenticated request, no Access Token Provided'
        }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_correct_error_on_malformed_upload_event(self):
        resp = handler({
             'Type': 'NotifyUploadComplete',
             'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Bad Format Error: key Bucket missing from event'
        }, resp)

        resp = handler({
             'Type': 'NotifyUploadComplete',
             'AccessToken': self.access_token,
             'Bucket': 'somebucket'
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Bad Format Error: key Key missing from event'
        }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_error_response_on_delete_event(self):
        resp = handler({
            'Type': 'DeleteRoute',
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Bad Format Error: key RouteID missing from event'
        }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_error_response_on_save_predictions_event(self):
        resp = handler({
            'Type': 'SavePredictions',
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Bad Format Error: key RouteID missing from event'
        }, resp)

        resp = handler({
            'Type': 'SavePredictions',
            'RouteID': "1721739812-1238123",
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Bad Format Error: key UserID missing from event'
        }, resp)

        resp = handler({
            'Type': 'SavePredictions',
            'RouteID': "1721739812-1238123",
            'UserID': 'asbdasd-asdasvdy',
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Bad Format Error: key Predictions missing from event'
        }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_error_response_on_paginated_readings_event(self):
        resp = handler({
            'Type': 'GetPaginatedReadings',
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Bad Format Error: key RouteID missing from event'
        }, resp)

    def test_error_response_on_unauthenticated_event(self):
        resp = handler({
            'Type': 'GetRoute',
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Unauthenticated request, no Access Token Provided'
        }, resp)

        resp = handler({
            'Type': 'GetRoute',
            'AccessToken': 'bad_access_token',
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Unauthenticated request, unrecognized Access Token bad_access_token'
        }, resp)


    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_error_response_on_nonexistant_type(self):
        resp = handler({
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
        handler({
             'Type': 'NotifyUploadComplete',
             'AccessToken': 'eyJraWQiOiI0QXl3TjdidExEWm1RWFBEdVpxZ3JRTVk2MkVheXc0ZlN6eXBNcFI2bDh3PSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI5OWJmNDUxOS04NWQ5LTQ3MjYtOTQ3MS00YzkxYTc2Nzc5MjUiLCJjb2duaXRvOmdyb3VwcyI6WyJhZG1pbiJdLCJldmVudF9pZCI6IjljYjMyZjRjLWFhMDktNDk4Yi1hYjkzLTk5ODE3ZjdmNGQxYyIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE2MTgyNjc5MzEsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5hcC1zb3V0aGVhc3QtMi5hbWF6b25hd3MuY29tXC9hcC1zb3V0aGVhc3QtMl9jdHBnbTBLdzQiLCJleHAiOjE2MTgyNzE1MzEsImlhdCI6MTYxODI2NzkzMSwianRpIjoiNmRkNGZiNWMtMTZhZS00N2JjLTg4OTEtODRkYjUzNjg0NmMwIiwiY2xpZW50X2lkIjoiNHVxaHFzb29lNDNlYnRxMG9idm4wbG03dWkiLCJ1c2VybmFtZSI6ImZkc2FkbWluIn0.EgNiuZYENTdIF7t7Zs0LC0UEPaMSc1M66fxfi4OpoLcKvCXdLax6r4wa0gdeL96N6x2PzpBmdxEoeZfSnIFq2NNtcLPXYpmONGgbmP4bxdQW1FcplE6dlvkfo6UnQQdmjTd6r6rTq6CHlHBskFWfi7YRcdbtFf8Ic9nIB2G8J8EkjN1cwGrUUrQ3CqaOuLNjUqxtP6fYgrqEk6lseWVp4P33HK8zOwPUxUuqjwtWfJK_Mchy0QL_K-HpnyUoXU5cv63_PY_OI63QYz5FHFtloTwj1iWqGdE43_tH8AdT3UJpmFNHwHijqVVpsFVmTowRuw1QskdZP-yHK4p7Ea8Y7Q',
             'Bucket': 'mobileappsessions172800-main',
             'Key': 'public/route_2021_04_12_20_59_16_782.zip',
             'RouteName': 'Blinkins Ct.'
        }, TEST_CONTEXT)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_gets_non_existant_route(self):
        resp = handler({
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
        resp = handler({
            'Type': 'AddUser',
            'UserID': "a98s7das87dba0sa7gdas87",
            'DataAccessGroups': [
                {'GroupName': 'Roora', 'GroupID': 'a9sd6a7s128123'},
                {'GroupName': 'Vicroads', 'GroupID': '12--1tg122168'}
            ],
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Success',
            'Body': {'DataAccessGroups': [
                {'GroupName': 'Roora', 'GroupID': 'a9sd6a7s128123'},
                {'GroupName': 'Vicroads', 'GroupID': '12--1tg122168'}
            ]}
        }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_handles_user_put_request_correctly(self):
        resp = handler({
            'Type': 'AddUser',
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'Bad Format Error: key UserID missing from event'
        }, resp)

        resp = handler({
            'Type': 'AddUser',
            'UserID': 'too-short',
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'User ID too-short was too short, must be at least 20 characters long'
        }, resp)

        resp = handler({
            'Type': 'AddUser',
            'UserID': 'too-shorta-sd-asdas-dasd-asd',
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Success',
            'Body': {'DataAccessGroups': [
                 {'GroupName': 'too-shorta-sd-asdas-dasd-asd', 'GroupID': 'too-shorta-sd-asdas-dasd-asd'}
            ]}
        }, resp)
  
        resp = handler({
            'Type': 'AddUser',
            'UserID': 'too-shorta-sd-asdas-dasd-asd',
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Error',
            'Body': 'User ID too-shorta-sd-asdas-dasd-asd has already been registered'
        }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_success_on_paginated_readings_for_absent_route(self):
        resp = handler({
            'Type': 'GetPaginatedReadings',
            'RouteID': 'INVALID_ID',
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual({
            'Status': 'Success',
            'Body': None
        }, resp)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    @mock.patch('time.time', mock.MagicMock(side_effect=Increment(1619496879)))
    def test_uploads_predictions(self):
        with open('readingdb/test_data/gps_img_route.json') as f:
            route_json = json.load(f) 
        r = self.api.save_route(RouteSpec.from_json(route_json), self.user_id)

        resp = handler({
            'Type': 'GetPaginatedReadings',
            'RouteID': r.id,
            'PredictionOnly': False,
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual(resp['Status'], 'Success')
        self.assertEqual(len(resp['Body']['Readings']), 116)

        with open('readingdb/test_data/ftg_imgs.json') as f:
            pred_json = json.load(f)

        for reading in pred_json:
            reading['Reading']['ImageFileName'] = "readingdb/test_data/route_imgs/route_2021_04_07_17_14_36_709/2021_04_07_17_14_49_386-25.jpg"

        resp = handler({
            'Type': 'SavePredictions',
            'RouteID': r.id,
            'UserID': self.user_id,
            'Predictions': pred_json,
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual(22, len(resp['Body']['SavedReadings']))
        resp = handler({
            'Type': 'GetPaginatedReadings',
            'RouteID': r.id,
            'PredictionOnly': False,
            'AnnotatorPreference': None,
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual(resp['Status'], 'Success')
        self.assertEqual(len(resp['Body']['Readings']), 138)
    
    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    @mock.patch('time.time', mock.MagicMock(side_effect=Increment(1619496879)))
    def test_uploads_predictions_for_long_route(self):
        with open('readingdb/test_data/sydney_route_short.json') as f:
            route_json = json.load(f) 
        r = self.api.save_route(RouteSpec.from_json(route_json), self.user_id)

        resp = handler({
            'Type': 'GetPaginatedReadings',
            'RouteID': r.id,
            'AnnotatorPreference': [
                '99bf4519-85d9-4726-9471-4c91a7677925'
            ],
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual(resp['Status'], 'Success')
        self.assertEqual(len(resp['Body']['Readings']), 713)
        self.assertIsNone(resp['Body']['PaginationKey'])

        resp = handler({
            'Type': 'GetReadings',
            'RouteID': r.id,
            'AnnotatorPreference': [
                '99bf4519-85d9-4726-9471-4c91a7677925'
            ],
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual(resp['Status'], 'Success')
        self.assertEqual(len(resp['Body']['Readings']), 713)

@mock_s3
class TestLambdaR(TestLambdaRW): 
    @mock.patch('time.time', mock.MagicMock(side_effect=Increment(1619496879)))
    def setUp(self) -> None:
        super().setUp()

        with open('readingdb/test_data/gps_img_route.json') as f:
            route_json = json.load(f) 
        r = self.api.save_route(RouteSpec.from_json(route_json), self.user_id)
        self.gps_img_route = r

        with open('readingdb/test_data/ftg_route.json') as f:
            route_json = json.load(f) 
        r = self.api.save_route(RouteSpec.from_json(route_json), self.user_id)
        self.tst_route = r

        with open('readingdb/test_data/ftg_20_route.json') as f:
            route_json = json.load(f) 
        r = self.api.save_route(RouteSpec.from_json(route_json), self.user_id)
        self.twenty_route = r

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_pagination_filters_non_prediction_readings(self):
        resp = handler({
            'Type': 'GetPaginatedReadings',
            'RouteID': self.gps_img_route.id,
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual(resp['Status'], 'Success')
        self.assertEqual(len(resp['Body']['Readings']), 0)
        self.assertIsNone(resp['Body']['PaginationKey'])

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_gets_paginated_readings_for_user(self):
        resp = handler({
            'Type': 'GetPaginatedReadings',
            'RouteID': self.twenty_route.id,
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual(resp['Status'], 'Success')
        self.assertEqual(len(resp['Body']['Readings']), 1)
        self.assertIsNone(resp['Body']['PaginationKey'])
        self.assertEqual(resp['Body']['Readings'][0]['RouteID'], self.twenty_route.id)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_gets_paginated_readings_with_start_key(self):
        key_reading = [r for r in self.gps_img_route.sample_data.values() if r.readingType == 'PositionalReading'][0]
        key1 = { "ReadingID": key_reading.id, "RouteID": key_reading.route_id }
        key_reading = [r for r in self.gps_img_route.sample_data.values() if r.readingType == 'ImageReading'][0]
        key2 = { "ReadingID": key_reading.id, "RouteID": key_reading.route_id }
        resp = handler({
            'Type': 'GetPaginatedReadings',
            'RouteID': self.gps_img_route.id,
            'PredictionOnly': False,
            'PaginationKey': key1,
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual(resp['Status'], 'Success')
        self.assertEqual(len(resp['Body']['Readings']), 86)
        self.assertIsNone(resp['Body']['PaginationKey'])
        self.assertEqual(resp['Body']['Readings'][0]['RouteID'], self.gps_img_route.id)

        resp = handler({
            'Type': 'GetPaginatedReadings',
            'RouteID': self.gps_img_route.id,
            'PredictionOnly': False,
            'PaginationKey': key2,
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual(resp['Status'], 'Success')
        self.assertEqual(len(resp['Body']['Readings']), 115)
        self.assertIsNone(resp['Body']['PaginationKey'])
        self.assertEqual(resp['Body']['Readings'][0]['RouteID'], self.gps_img_route.id)

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_gets_routes_for_user(self):
        resp = handler({
            'Type': 'GetUserRoutes',
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertEqual(len(resp['Body']), 3)
        self.assertTrue(resp['Body'][0]['RouteID'] in [
            self.twenty_route.id,
            self.gps_img_route.id,
            self.tst_route.id
        ])

    # @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    # def test_gets_readings(self):
    #     resp = handler({
    #         'Type': 'GetReadings',
    #         'RouteID': self.twenty_route.id,
    #         'AccessToken': self.access_token,
    #     }, TEST_CONTEXT)

    #     self.assertEqual(resp['Status'], 'Success')
    #     self.assertIsInstance(resp['Body'], dict)
    #     self.assertEqual(resp['Body']['Bucket'], self.tmp_bucket)

    # @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    # def test_gets_readings_with_key(self):
    #     resp = handler({
    #         'Type': 'GetReadings',
    #         'BucketKey': 'rulerruler.json',
    #         'RouteID': self.twenty_route.id,
    #         'AccessToken': self.access_token,
    #     }, TEST_CONTEXT)

    #     self.assertEqual(resp['Status'], 'Success')
    #     self.assertEqual(resp['Body']['Key'], 'rulerruler.json')

    @unittest.skipIf(not credentials_present(), NO_CREDS_REASON)
    def test_gets_route(self):
        resp = handler({
            'Type': 'GetRoute',
            'RouteID': self.twenty_route.id,
            'AccessToken': self.access_token,
        }, TEST_CONTEXT)

        self.assertIn('PresignedURL', resp['Body']['SampleData']['PredictionReading']['Reading'])
        del resp['Body']['SampleData']['PredictionReading']['Reading']['PresignedURL']

        self.maxDiff = None

        self.assertIn('LastUpdated', resp['Body'])
        del resp['Body']['LastUpdated']
        self.assertEqual({
            'Status': 'Success', 
            'Body': {
                'RouteStatus': 1, 
                'Timestamp': 1616116106935,
                'UserID': '99bf4519-85d9-4726-9471-4c91a7677925', 
                'SampleData': {
                    'PredictionReading': {
                        'AnnotationTimestamp': 2378910,
                        'AnnotatorID': '99994519-85d9-4726-9471-4c91a7677925',
                        'ReadingID': resp['Body']['SampleData']['PredictionReading']['ReadingID'], 
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
                        'Timestamp': 1616116106935
                    }
                }, 
                'RouteID': self.twenty_route.id, 
                'RouteName': self.twenty_route.name
            }
        }, resp)
