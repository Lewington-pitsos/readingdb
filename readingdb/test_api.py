import json
import os
from typing import List
from unittest import mock
from readingdb.reading import AbstractReading, json_to_reading
import uuid
from readingdb.endpoints import TEST_BUCKET, TEST_DYNAMO_ENDPOINT
from readingdb.route import Route
from readingdb.constants import *
from readingdb.routestatus import RouteStatus
from readingdb.constants import ReadingRouteKeys, RouteKeys
from readingdb.routespec import RouteSpec
import tempfile
import unittest
import boto3
from moto import mock_s3

from readingdb.download_json import download_json_files
from readingdb.api import API
from readingdb.tutils import *

@mock_s3
class TestAPI(unittest.TestCase):
    region_name = 'ap-southeast-2'
    access_key = 'fake_access_key'
    secret_key = 'fake_secret_key'
    bucket_name = TEST_BUCKET
    test_prefix = 'mocks'
    tmp_bucket ='tmp'

    def setUp(self):
        self.current_dir = os.path.dirname(__file__)
        create_bucket(
            self.current_dir, 
            self.region_name, 
            self.access_key, 
            self.secret_key, 
            self.bucket_name,
        )
        create_bucket(
            self.current_dir, 
            self.region_name, 
            self.access_key, 
            self.secret_key, 
            self.tmp_bucket,
        )

        self.api = API(
            TEST_DYNAMO_ENDPOINT,  
            bucket=self.bucket_name,
            tmp_bucket=self.tmp_bucket
        ) 
        self.api.create_reading_db()
    
    def tearDown(self):
        teardown_s3_bucket(
            self.region_name,
            self.access_key,
            self.secret_key,
            self.bucket_name
        )
        teardown_s3_bucket(
            self.region_name,
            self.access_key,
            self.secret_key,
            self.tmp_bucket
        )

        self.api.teardown_reading_db()
    
    def test_mocking_works(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            download_json_files(self.bucket_name, self.test_prefix, tmpdir)
            mock_folder_local_path = os.path.join(tmpdir, self.test_prefix)
            self.assertTrue(os.path.isdir(mock_folder_local_path))
            result = os.listdir(mock_folder_local_path)
            desired_result = ['file.json', 'apple.json']
            self.assertCountEqual(result, desired_result)

    def test_adds_presigned_urls_to_paginated_readings(self):
        user_id = 'aghsghavgas'
        api = API(TEST_DYNAMO_ENDPOINT, bucket=self.bucket_name)
        with open(self.current_dir + '/test_data/ftg_20_route.json', 'r') as j:
            route_spec_data = json.load(j)
        route_spec = RouteSpec.from_json(route_spec_data)
        route = api.save_route(route_spec, user_id)

        page0, _ = self.api.paginated_route_readings(route.id)
        self.assertEqual(22, len(page0))
        self.assertIn('PresignedURL', page0[0]['Reading'])

    def test_handles_large_queries_correctly(self):
        route_id = '103'
        self.api.put_route(Route('3', route_id, 123617823))
        
        with open(self.current_dir +  '/test_data/sydney_entries.json', 'r') as f:
            entities = json.load(f)

        finalized = []
        for e in entities[:60]:
            e[ReadingKeys.READING_ID] = str(uuid.uuid1())
            e[ReadingRouteKeys.ROUTE_ID] = route_id
            r: AbstractReading = json_to_reading('PredictionReading', e)
            finalized.append(r)
        self.api.put_readings(finalized)

        readings =  self.api.all_route_readings(route_id)
        self.assertIsInstance(readings, list)
        self.assertEqual(60, len(readings))
        
        self.api.size_limit = 400
        uri = self.api.all_route_readings(route_id)
        
        self.assertIsInstance(uri, dict)
        self.assertEqual(uri['Bucket'], self.tmp_bucket)

    def test_can_upload_readings_with_given_key(self):
        route_id = '103'
        self.api.put_route(Route('3', route_id, 123617823))
        
        with open(self.current_dir +  '/test_data/sydney_entries.json', 'r') as f:
            entities = json.load(f)

        finalized = []
        for e in entities[:60]:
            e[ReadingKeys.READING_ID] = str(uuid.uuid1())
            e[ReadingRouteKeys.ROUTE_ID] = route_id
            r: AbstractReading = json_to_reading('PredictionReading', e)
            finalized.append(r)
        self.api.put_readings(finalized)

        self.api.size_limit = 400
        uri = self.api.all_route_readings(route_id, key='kingofkings.json')
        
        self.assertIsInstance(uri, dict)
        self.assertEqual(uri['Bucket'], self.tmp_bucket)
        self.assertEqual(uri['Key'], 'kingofkings.json')

    def test_updates_route_name(self):
        user_id = 'aghsghavgas'
        api = API(TEST_DYNAMO_ENDPOINT, bucket=self.bucket_name)
        with open(self.current_dir + '/test_data/ftg_route.json', 'r') as j:
            route_spec_data = json.load(j)
        route_spec = RouteSpec.from_json(route_spec_data)
        route = api.save_route(route_spec, user_id)

        self.assertEqual(route.name, route.id[:Route.MAX_NAME_LENGTH])
        api.update_route_name(route.id, user_id, 'Belgrave')

        loaded_route = api.get_route(route.id, user_id)
        self.assertEqual(loaded_route[ReadingRouteKeys.ROUTE_ID], route.id)
        self.assertEqual(loaded_route[RouteKeys.NAME], 'Belgrave')

    def test_update_route_status(self):
        user_id = 'aghsghavgas'
        api = API(TEST_DYNAMO_ENDPOINT, bucket=self.bucket_name)
        with open(self.current_dir + '/test_data/ftg_route.json', 'r') as j:
            route_spec_data = json.load(j)
        route_spec = RouteSpec.from_json(route_spec_data)
        route = api.save_route(route_spec, user_id)

        self.assertEqual(RouteStatus.UPLOADED, route.status)
        api.set_as_predicting(route.id, user_id)

        loaded_route = api.get_route(route.id, user_id)
        self.assertEqual(loaded_route[ReadingRouteKeys.ROUTE_ID], route.id)

        preds = [{
            'Reading': {
                'ImageFileName': 'route_2021_03_19_12_08_03_249/images/snap_2021_03_19_12_08_26_863.jpg',
                'PresignedURL': 'INVALID_URL',
                'S3Uri': {
                    'Bucket': self.bucket_name,
                    'Key': route.id + 'route_2021_03_19_12_08_03_249/images/snap_2021_03_19_12_08_26_863.jpg'
                },
                'Entities': [
                    {
                        'Name': 'CrocodileCrack',
                        'Confidence': 0.17722677,
                        'Severity': 1.0,
                        'Present': False,
                    },
                    {
                        'Name': 'LatCrack', 
                        'Confidence': 0.07661053,
                        'Severity': 1.0,
                        'Present': False,
                    },
                    {
                        'Name': 'LongCrack', 
                        'Confidence': 0.6557837,
                        'Severity': 1.0,
                        'Present': False,
                    },
                    {
                        'Name': 'Pothole',
                        'Confidence': 0.14074452,
                        'Severity': 1.0,
                        'Present': False,
                    },
                    {
                        'Name': 'Lineblur',
                        'Confidence': 0.09903459,
                        'Severity': 1.0,
                        'Present': False,
                    }
                ],
                'Longitude': 145.2450816,
                'Latitude': -37.8714232,
            },
            'ReadingID': 0,
            'AnnotatorID': '3f01d5ec-c80b-11eb-acfa-02428ee80691',
            'AnnotationTimestamp': 1623124571562,
            'Type': 'PredictionReading',
            'RouteID': route.id,
            'Timestamp': 1616116106935,
        }]

        saved = api.save_predictions(preds, route.id)
        loaded_route = api.get_route(route.id, user_id)
        self.assertEqual(len(preds), len(saved))
        self.assertEqual(loaded_route[ReadingRouteKeys.ROUTE_ID], route.id)

    def test_saves_severity(self):
        user_id = 'aghsghavgas'
        api = API(TEST_DYNAMO_ENDPOINT, bucket=self.bucket_name)
        with open(self.current_dir + '/test_data/ftg_route.json', 'r') as j:
            route_spec_data = json.load(j)
        route_spec = RouteSpec.from_json(route_spec_data)
        route = api.save_route(route_spec, user_id)

        readings = api.all_route_readings(route.id)
        self.assertEqual(3, len(readings))
        first_reading = readings[0]

        self.assertEqual(first_reading[ReadingKeys.TIMESTAMP], 1616116106935)
        entites = first_reading[ReadingKeys.READING][PredictionReadingKeys.ENTITIES]

        longCrack = None
        crockCrack = None

        for e in entites:
            if e['Name'] == 'LongCrack':
                longCrack = e
            if e['Name'] == 'CrocodileCrack':
                crockCrack = e
                
        self.assertEqual(1.3, longCrack['Severity'])
        self.assertEqual(1.34, crockCrack['Severity'])

    @mock.patch('time.time', mock.MagicMock(side_effect=Increment(1619496879)))
    def test_saves_readings_to_existing_route(self):
        user_id = 'asdy7asdh'
        route_id = 'asdasdasdasd'
        api = API(TEST_DYNAMO_ENDPOINT, bucket=self.bucket_name)

        user_routes = api.routes_for_user(user_id)
        self.assertEqual(len(user_routes), 0)

        r = Route(
            user_id,
            route_id,
            0,
        )
        updated_time = r.update_timestamp
        api.put_route(r)

        s3 = boto3.resource(
            's3',
            region_name=self.region_name,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        )

        bucket = s3.Bucket(self.bucket_name)
        bucket_objects = []
        for my_bucket_object in bucket.objects.all():
            bucket_objects.append(my_bucket_object.key)

        self.assertEqual(set(bucket_objects), set([
            'mocks/apple.json', 
            'mocks/file.json',
            'mocks/route_2021_04_07_17_14_36_709.zip',
            'mocks/route_1621394080578.zip'
        ]))

        user_routes = api.routes_for_user(user_id)
        self.assertEqual(len(user_routes), 1)
        self.assertNotIn('SampleData', user_routes[0])

        readings = api.all_route_readings(route_id)
        self.assertEqual(len(readings), 0)

        with open(self.current_dir + '/test_data/ftg_imgs.json', 'r') as j:
            route_spec_data = json.load(j)

        api.save_predictions(route_spec_data, route_id)
        readings = api.all_route_readings(route_id)
        self.assertEqual(len(readings), 22)

        bucket_objects = []

        for my_bucket_object in bucket.objects.all():
            bucket_objects.append(my_bucket_object.key)

        self.assertEqual(set(bucket_objects), set([
            'mocks/apple.json', 
            'mocks/file.json',
            route_id + 'readingdb/test_data/images/road1.jpg',
            'mocks/route_2021_04_07_17_14_36_709.zip',
            'mocks/route_1621394080578.zip'
        ]))
    
    def test_raises_while_saving_readings_to_existing_route_with_unknown_images(self):
        user_id = 'asdy7asdh'
        route_id = 'asdasdasdasd'
        api = API(TEST_DYNAMO_ENDPOINT, bucket=self.bucket_name)
        user_routes = api.routes_for_user(user_id)
        self.assertEqual(len(user_routes), 0)
        r = Route(
            user_id,
            route_id,
            0,
        )
        api.put_route(r)
        with open(self.current_dir + '/test_data/ftg_imgs.json', 'r') as j:
            route_spec_data = json.load(j)
        self.assertRaises(ValueError, api.save_predictions, route_spec_data, route_id, False) 

    def test_saves_readings_to_existing_route_with_unknown_images(self):
        user_id = 'asdy7asdh'
        route_id = 'asdasdasdasd'
        api = API(TEST_DYNAMO_ENDPOINT, bucket=self.bucket_name)
        user_routes = api.routes_for_user(user_id)
        self.assertEqual(len(user_routes), 0)
        r = Route(user_id, route_id, 0)
        api.put_route(r)
        with open(self.current_dir + '/test_data/ftg_imgs.json', 'r') as j:
            raw_readings = json.load(j)        
        api.save_predictions(raw_readings, route_id)
        readings = api.all_route_readings(route_id)
        self.assertEqual(len(readings), 22)

        self.maxDiff = None
        for r in readings:
            self.assertEqual(
                {'Bucket': 'test_bucket', 'Key': 'asdasdasdasdreadingdb/test_data/images/road1.jpg'}, 
                r['Reading']['S3Uri'],
            )
            self.assertEqual(   
                r['AnnotationTimestamp'],
                2378910
            )
            self.assertEqual(   
                r['AnnotatorID'],
                '99994519-85d9-4726-9471-4c91a7677925'
            )

        api.save_predictions(raw_readings, route_id, save_imgs=False)
        readings = api.all_route_readings(route_id)
        self.assertEqual(len(readings), 22)

        new_annotator_id = "9a9a9a9a9a9a9a9a9" 
        for r in raw_readings:
            r['AnnotatorID'] = new_annotator_id
        api.save_predictions(raw_readings, route_id, save_imgs=False)
        readings = api.all_route_readings(route_id)
        self.assertEqual(len(readings), 44)

        self.maxDiff = None
        for r in readings:
            self.assertEqual(
                {'Bucket': 'test_bucket', 'Key': 'asdasdasdasdreadingdb/test_data/images/road1.jpg'}, 
                r['Reading']['S3Uri'],
            )
            self.assertEqual(   
                r['AnnotationTimestamp'],
                2378910
            )
            self.assertIn(   
                r['AnnotatorID'],
                ['9a9a9a9a9a9a9a9a9', '99994519-85d9-4726-9471-4c91a7677925']
            )

    @mock.patch('time.time', mock.MagicMock(side_effect=Increment(1619496879)))
    def test_uploads_small_route(self):
        user_id = 'asdy7asdh'
        api = API(TEST_DYNAMO_ENDPOINT, bucket=self.bucket_name)

        with open(self.current_dir + '/test_data/ftg_route.json', 'r') as j:
            route_spec_data = json.load(j)

        route_spec = RouteSpec.from_json(route_spec_data)
        route = api.save_route(route_spec, user_id)

        user_routes = api.routes_for_user(user_id)
        self.assertEqual(len(user_routes), 1)

        self.assertIn('PresignedURL', user_routes[0]['SampleData']['PredictionReading']['Reading'])
        del user_routes[0]['SampleData']['PredictionReading']['Reading']['PresignedURL']
        self.maxDiff = None
        expected_sample_data = {
            'LastUpdated': 1619496879,
            'RouteStatus': 1,
            'RouteID': route.id,
            'Timestamp': 1616116106935,
            'UserID': 'asdy7asdh',
            'SampleData': {
                'PredictionReading': {
                    'AnnotationTimestamp': 1623124150112,
                    'AnnotatorID': '3f01d5ec-c80b-11eb-acfa-02428ee80691',
                    'Reading': {
                        'ImageFileName': 'readingdb/test_data/images/road1.jpg',
                        'S3Uri': {
                            'Bucket': self.bucket_name,
                            'Key': route.id + 'readingdb/test_data/images/road1.jpg'
                        },
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
                            'Present': False}
                        ],
                        'Longitude': 145.2450816,
                        'Latitude': -37.8714232,
                    },
                'ReadingID': user_routes[0]['SampleData']['PredictionReading']['ReadingID'],
                'Type': 'PredictionReading',
                'RouteID': route.id,
                'Timestamp': 1616116106935
                }
            },
            'RouteName': route.name,
        }
        
        self.assertEqual(expected_sample_data, user_routes[0])

        s3 = boto3.resource(
            's3',
            region_name=self.region_name,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        )

        bucket = s3.Bucket(self.bucket_name)

        bucket_objects = []

        for my_bucket_object in bucket.objects.all():
            bucket_objects.append(my_bucket_object.key)

        self.assertEqual(set(bucket_objects), set([
            'mocks/apple.json', 
            'mocks/file.json',
            route.id + 'readingdb/test_data/images/road1.jpg',
            'mocks/route_2021_04_07_17_14_36_709.zip',
            'mocks/route_1621394080578.zip'
        ]))

    def test_deletes_route(self):
        user_id = 'aghsghavgas'
        s3 = boto3.resource(
            's3',
            region_name=self.region_name,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        )
        bucket = s3.Bucket(self.bucket_name)
        api = API(TEST_DYNAMO_ENDPOINT, bucket=self.bucket_name)
        with open(self.current_dir + '/test_data/ftg_20_route.json', 'r') as j:
            route_spec_data = json.load(j)
        route_spec = RouteSpec.from_json(route_spec_data)
        
        self.assertEqual(0, len(api.routes_for_user(user_id)))
        self.assertEqual(4, len(self.__get_bucket_objects(bucket)))

        route = api.save_route(route_spec, user_id)
        self.assertEqual(1, len(api.routes_for_user(user_id)))
        self.assertEqual(22, len(api.all_route_readings(route.id)))
        self.assertEqual(5, len(self.__get_bucket_objects(bucket)))

        api.delete_route(route.id, user_id)
        self.assertEqual(0, len(api.routes_for_user(user_id)))
        self.assertEqual(0, len(api.all_route_readings(route.id)))
        self.assertEqual(4, len(self.__get_bucket_objects(bucket)))
        
        route = api.save_route(route_spec, user_id)
        self.assertEqual(1, len(api.routes_for_user(user_id)))
        
        user_id2 = "9a8a7ssa7s"
        route2 = api.save_route(route_spec, user_id)
        route3 = api.save_route(route_spec, user_id2)
        self.assertEqual(2, len(api.routes_for_user(user_id)))
        self.assertEqual(1, len(api.routes_for_user(user_id2)))
        self.assertEqual(22, len(api.all_route_readings(route.id)))
        self.assertEqual(22, len(api.all_route_readings(route2.id)))
        self.assertEqual(22, len(api.all_route_readings(route3.id)))
        self.assertEqual(7, len(self.__get_bucket_objects(bucket)))
        
        api.delete_route(route.id, user_id)
        self.assertEqual(1, len(api.routes_for_user(user_id)))
        self.assertEqual(1, len(api.routes_for_user(user_id2)))
        self.assertEqual(6, len(self.__get_bucket_objects(bucket)))

        api.delete_route(route2.id, user_id)
        self.assertEqual(0, len(api.routes_for_user(user_id)))
        self.assertEqual(1, len(api.routes_for_user(user_id2)))
        self.assertEqual(5, len(self.__get_bucket_objects(bucket)))
        
        api.delete_route(route3.id, user_id2)
        self.assertEqual(0, len(api.routes_for_user(user_id)))
        self.assertEqual(0, len(api.routes_for_user(user_id2)))
        self.assertEqual(0, len(api.all_route_readings(route.id)))
        self.assertEqual(0, len(api.all_route_readings(route2.id)))
        self.assertEqual(0, len(api.all_route_readings(route3.id)))
        self.assertEqual(4, len(self.__get_bucket_objects(bucket)))

    def __get_bucket_objects(self, bucket: str) -> List[str]:
        bucket_objects = []
        for my_bucket_object in bucket.objects.all():
            bucket_objects.append(my_bucket_object.key)

        return bucket_objects

    def test_can_filter_moot_readings(self):
        user_id = 'aghsghavgas'
        api = API(TEST_DYNAMO_ENDPOINT, bucket=self.bucket_name)
        with open(self.current_dir + '/test_data/ann_route.json', 'r') as j:
            route_spec_data = json.load(j)
        route_spec = RouteSpec.from_json(route_spec_data)

        route = api.save_route(route_spec, user_id)
        self.assertEqual(3, len(api.all_route_readings(route.id)))

        readings = api.prediction_readings(route.id, [DEFAULT_ANNOTATOR_ID])
        self.assertEqual(2, len(readings))

        for r in readings:
            if r['Reading']['ImageFileName'] == 'readingdb/test_data/images/road1.jpg':
                self.assertEqual(r['AnnotatorID'], '99bf4519-85d9-4726-9471-4c91a7677925')
            else:
                self.assertEqual(r['AnnotatorID'], '3f01d5ec-c80b-11eb-acfa-02428ee80691')
        
    def test_can_filter_non_prediction_readings(self):
        user_id = 'aghsghavgas'
        api = API(TEST_DYNAMO_ENDPOINT, bucket=self.bucket_name)
        with open(self.current_dir + '/test_data/gps_img_route.json', 'r') as j:
            route_spec_data = json.load(j)
        route_spec = RouteSpec.from_json(route_spec_data)

        route = api.save_route(route_spec, user_id)
        self.assertEqual(116, len(api.all_route_readings(route.id)))
        self.assertEqual(0, len(api.prediction_readings(route.id)))

        with open(self.current_dir + '/test_data/gps_img_route.json', 'r') as j:
            route_spec_data = json.load(j)
        route_spec = RouteSpec.from_json(route_spec_data)

        route = api.save_route(route_spec, user_id)
        self.assertEqual(116, len(api.all_route_readings(route.id)))
        self.assertEqual(0, len(api.prediction_readings(route.id)))

    def test_filters_paginated_readings_correctly(self):
        user_id = 'aghsghavgas'
        api = API(TEST_DYNAMO_ENDPOINT, bucket=self.bucket_name)
        api.max_page_readings = 300
        with open(self.current_dir + '/test_data/sydney_route_short.json', 'r') as j:
            route_spec_data = json.load(j)
        route_spec = RouteSpec.from_json(route_spec_data)
        route = api.save_route(route_spec, user_id)

        readings = api.all_route_readings(route.id)
        self.assertEqual(971, len(readings))

        preference = [
            DEFAULT_ANNOTATOR_ID
        ]
        all_readings = []
        pag, key = api.filtered_paginated_readings(
            route.id, 
            annotator_preference=preference
        )
        all_readings += pag
        pag, key = api.filtered_paginated_readings(
            route.id, 
            annotator_preference=preference,
            last_key=key,
        )
        all_readings += pag
        pag, key = api.filtered_paginated_readings(
            route.id, 
            annotator_preference=preference,
            last_key=key,
        )
        all_readings += pag

        pag, key = api.filtered_paginated_readings(
            route.id, 
            annotator_preference=preference,
            last_key=key,
        )
        all_readings += pag
        self.assertIsNone(key)
        self.assertEqual(713, len(all_readings))

        well_annotated = [r for r in all_readings if r['AnnotatorID'] == DEFAULT_ANNOTATOR_ID]
        self.assertEqual(227, len(well_annotated))

    def test_save_user(self):
        usrs = self.api.all_users()
        self.assertEqual(0, len(usrs))

        success = self.api.save_user('some-user-id-that-is')
        self.assertTrue(success)
        usrs = self.api.all_users()
        self.assertEqual(1, len(usrs))

        success = self.api.save_user('some-user-id-that-is')
        self.assertFalse(success)
        usrs = self.api.all_users()
        self.assertEqual(1, len(usrs))
    
    # def test_gets_accessible_routes(self):
    #     uid = "ahsd78astdy87asdgha87s"

    #     access_groups = self.api.save_user(uid)
    #     routes = self.api.routes_for_user(uid)
    #     self.assertEqual(0, len(routes))

    #     rid = '17231-12312321'
    #     self.api.put_route(Route('3', rid, 123617823, access_groups))
    #     routes = self.api.routes_for_user(uid)
    #     self.assertEqual(1, len(routes))
        