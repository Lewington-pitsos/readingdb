from typing import Any, Dict
from readingdb.entity import Entity
from readingdb.tutils import Increment
from readingdb.routestatus import RouteStatus
import unittest
import time
import os
import json
import uuid
from unittest import mock

from readingdb.db import DB
from readingdb.constants import *
from readingdb.reading import AbstractReading, ImageReading, PredictionReading, json_to_reading
from readingdb.route import Route

class TestDB(unittest.TestCase):
    def setUp(self):
        self.current_dir = os.path.dirname(__file__)
        self.db = DB('http://localhost:8000')
    
    def test_saves_readings(self):
        self.db.create_reading_db()
        readings = self.db.routes_for_user('103')
        self.assertEqual(len(readings), 0)
        reading_time = int(time.time())

        finalized = []
        for i in range(21):
            finalized.append(
                ImageReading(
                    'sdasdasd-' + str(i),
                    'xxxa',
                    reading_time,
                    ReadingTypes.IMAGE,
                    'https://aws/s3/somebucket/file.jpg', 
                )
            )
        self.db.put_readings(finalized)
        readings = self.db.all_route_readings('xxxa')
        self.assertEqual(len(readings), 21)
        first_reading = readings[0]
        self.assertEqual(first_reading[ReadingRouteKeys.ROUTE_ID], 'xxxa')
        self.assertEqual(first_reading[ReadingKeys.TYPE], ReadingTypes.IMAGE)
        self.assertEqual(first_reading[ReadingKeys.READING_ID], 'sdasdasd-0')
        self.assertEqual(first_reading[ReadingKeys.READING], {
                ImageReadingKeys.FILENAME: 'https://aws/s3/somebucket/file.jpg' 
        })
        self.assertEqual(first_reading[ReadingKeys.TIMESTAMP], reading_time)

    def test_gets_all_users(self):
        self.db.create_reading_db()
        self.assertEqual(0, len(self.db.all_known_users()))

        self.db.put_route(Route('someuser_id', 'someRouteID', 123617823))
        self.assertEqual(1, len(self.db.all_known_users()))
        self.assertEqual('someuser_id', self.db.all_known_users()[0])

        self.db.put_route(Route('one-armed-larry', '2123y1h`278', 123617823))
        self.db.put_route(Route('one-armed-larry', '87218t238', 123617823))
        self.db.put_route(Route('jonny-the-wrench', '929298227', 123617823))
        self.assertEqual(3, len(self.db.all_known_users()))

    def test_saves_readings_with_severity(self):
        self.db.create_reading_db()
        readings = self.db.routes_for_user('103')
        self.assertEqual(len(readings), 0)

        reading_time = int(time.time())

        self.db.put_reading(
            PredictionReading(
                'sdasdasd-',
                'xxxa',
                reading_time,
                ReadingTypes.PREDICTION,
                -33.0089,
                109.868887601,
                'https://aws/s3/somebucket/file.jpg', 
                entities=[
                    Entity('Crocodile Cracks', 0.432, True, 1.876),
                    Entity('Rutting', 0.432, True, 2.1),
                    Entity('Ravelling', 0.432, True, 0.1),
                ],
                annotation_timestamp=1231238,
                annotator_id='someid'
            )
        )
    
        readings = self.db.all_route_readings('xxxa')
        self.assertEqual(len(readings), 1)
        first_reading = readings[0]
        self.assertEqual(first_reading[ReadingRouteKeys.ROUTE_ID], 'xxxa')
        self.assertEqual(first_reading[ReadingKeys.TYPE], ReadingTypes.PREDICTION)
        self.assertEqual(first_reading[ReadingKeys.READING_ID], 'sdasdasd-')
        self.assertEqual(first_reading[ReadingKeys.READING][PredictionReadingKeys.ENTITIES][0], {
            'Name': 'Crocodile Cracks',
            'Confidence': 0.432,
            'Severity': 1.876,
            'Present': True
        })
        self.assertEqual(first_reading[ReadingKeys.READING][PredictionReadingKeys.ENTITIES][1], {
            'Name': 'Rutting',
            'Confidence': 0.432,
            'Severity': 2.1,
            'Present': True
        })

    @mock.patch('time.time', mock.MagicMock(side_effect=Increment(1619496879)))
    def test_creates_new_route(self):
        self.db.create_reading_db()
        routes = self.db.routes_for_user('103')
        self.assertEqual(len(routes), 0)

        self.db.put_route(Route('3', '103', 123617823))
        
        routes = self.db.routes_for_user('3')
        self.assertEqual(len(routes), 1)
        self.assertEqual({
            'LastUpdated': 1619496879,
            'RouteID': '103',
            'RouteName': '103',
            'UserID': '3',
            'RouteStatus': 1,
            'Timestamp': 123617823
        }, routes[0])

    def test_saves_route_written_date(self):
        self.db.create_reading_db()
        routes = self.db.routes_for_user('103')
        self.assertEqual(len(routes), 0)

        r = Route('3', '103', 123617823)
        last_update_timestamp = r.update_timestamp 
        self.db.put_route(r)

        routes = self.db.routes_for_user('3')
        self.assertEqual(routes[0]['LastUpdated'], last_update_timestamp)

    @mock.patch('time.time', mock.MagicMock(side_effect=Increment(1619496879)))
    def test_updates_route_written_date_on_update(self):
        self.db.create_reading_db()
        routes = self.db.routes_for_user('103')
        self.assertEqual(len(routes), 0)
        route_id = '103'
        user_id = '3'

        r = Route(user_id, route_id, 123617823)
        original_update_timestamp = r.update_timestamp 
        self.db.put_route(r)

        routes = self.db.routes_for_user(user_id)
        self.assertEqual(routes[0]['LastUpdated'], original_update_timestamp)

        self.db.update_route_name(route_id, user_id, 'new_name')
        routes = self.db.routes_for_user(user_id)
        name_timestamp = routes[0]['LastUpdated']
        self.assertGreater(name_timestamp, original_update_timestamp)

        self.db.set_route_status(route_id, user_id, RouteStatus.COMPLETE)
        routes = self.db.routes_for_user(user_id)
        status_timestamp = routes[0]['LastUpdated']
        self.assertGreater(status_timestamp, name_timestamp)

        self.db.set_route_status(route_id, user_id, RouteStatus.COMPLETE)
        routes = self.db.routes_for_user(user_id)
        second_status_timestamp = routes[0]['LastUpdated']
        self.assertEqual(second_status_timestamp, status_timestamp)

        self.db.update_route_name(route_id, user_id, 'new_name')
        routes = self.db.routes_for_user(user_id)
        second_name_timestamp = routes[0]['LastUpdated']
        self.assertEqual(second_name_timestamp, second_status_timestamp)

    def test_loads_large_dataset(self):
        route_id = '103'
        self.db.create_reading_db()
        routes = self.db.routes_for_user(route_id)
        self.assertEqual(len(routes), 0)

        self.db.put_route(Route('3', route_id, 123617823))
        
        with open(self.current_dir +  '/test_data/sydney_entries.json', 'r') as f:
            entities = json.load(f)

        entity_readings = []
        for e in entities:
            e[ReadingKeys.READING_ID] = str(uuid.uuid1())
            e[ReadingRouteKeys.ROUTE_ID] = route_id
            r: AbstractReading = json_to_reading('PredictionReading', e)
            entity_readings.append(r)

        self.db.put_readings(entity_readings)

        readings = self.db.all_route_readings(route_id)
    
        self.assertEqual(3383, len(readings))

    def test_creates_new_route_with_name(self):
        name = 'someName'
        self.db.create_reading_db()
        routes = self.db.routes_for_user('103')
        self.assertEqual(len(routes), 0)

        self.db.put_route(Route('3', '103', 123617823, name=name))
        routes = self.db.routes_for_user('3')
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0][RouteKeys.NAME], name)

    def test_creates_new_route_with_sample_data(self):
        self.maxDiff = None
        sample_entry = {
            'ReadingID': 78,
            'Type': 'PredictionReading',
            'AnnotationTimestamp': 2136789,
            'AnnotatorID': '99bf4519-85d9-4726-9471-4c91a7677925',
            'Reading': {
                'Entities': [
                    {
                        'Name': 'CrocodileCrack',
                        'Confidence': 0.17722677,
                        'Present': False,
                    },
                    {
                        'Name': 'LatCrack', 
                        'Confidence': 0.07661053,
                        'Present': False,
                    },
                    {
                        'Name': 'LongCrack', 
                        'Confidence': 0.6557837,
                        'Present': False,
                    },
                    {
                        'Name': 'Pothole',
                        'Confidence': 0.14074452,
                        'Present': False,
                    },
                    {
                        'Name': 'Lineblur',
                        'Confidence': 0.09903459,
                        'Present': False,
                    }
                ],
                'Latitude': -37.8714232,
                'Longitude': 145.2450816,
                'ImageFileName': 'route_2021_03_19_12_08_03_249/images/snap_2021_03_19_12_08_26_863.jpg',
            },
            'RouteID': '45',
            'Timestamp': 1616116106935,
            'MillisecondPrecision': True,
            'Row': 30,
        }
   
        expected_entry = {
            'PredictionReading': {
                'AnnotationTimestamp': 2136789,
                'AnnotatorID': '99bf4519-85d9-4726-9471-4c91a7677925',
                'ReadingID': 78,
                'Type': 'PredictionReading',
                'Reading': {
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
                    'Latitude': -37.8714232,
                    'Longitude': 145.2450816,
                    'ImageFileName': 'route_2021_03_19_12_08_03_249/images/snap_2021_03_19_12_08_26_863.jpg',
                },
            'RouteID': '45',
            'Timestamp': 1616116106935,
        }}

        self.db.create_reading_db()
        routes = self.db.routes_for_user('103')
        self.assertEqual(len(routes), 0)

        self.db.put_route(Route(
            '3', 
            '103', 
            123617823,
            sample_data={'PredictionReading': json_to_reading('PredictionReading', sample_entry)}
        ))
        
        routes = self.db.routes_for_user('3')
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0][RouteKeys.SAMPLE_DATA], expected_entry)

    def test_returns_paginated_results_correctly(self):
        route_id = '103'
        self.db.create_reading_db()
        self.db.max_page_readings = 100
        self.db.put_route(Route('3', route_id, 12, 3617823))
        
        with open(self.current_dir +  '/test_data/sydney_entries.json', 'r') as f:
            entities = json.load(f)

        entity_readings = []
        for e in entities[:250]:
            e[ReadingKeys.READING_ID] = str(uuid.uuid1())
            e[ReadingRouteKeys.ROUTE_ID] = route_id
            r: AbstractReading = json_to_reading('PredictionReading', e)
            entity_readings.append(r)
        self.db.put_readings(entity_readings)

        readings = self.db.all_route_readings(route_id)
        self.assertEqual(250, len(readings))

        page0, key0 = self.db.paginated_route_readings(route_id)
        self.assertEqual(100, len(page0))

        newReadings = set([r['ReadingID'] for r in page0]) - set([r['ReadingID'] for r in readings])
        self.assertEqual(len(newReadings), 0)
 
        page0_retry, _ = self.db.paginated_route_readings(route_id)
        self.assertEqual(page0, page0_retry)

        page1, key1 = self.db.paginated_route_readings(route_id, key0)
        self.assertEqual(100, len(page1))

        newReadings = set([r['ReadingID'] for r in page1]) - set([r['ReadingID'] for r in page0])
        self.assertEqual(len(newReadings), 100)

        page2, key2 = self.db.paginated_route_readings(route_id, key1)
        self.assertIsNone(key2)
        self.assertEqual(50, len(page2))
        
        newReadings = set([r['ReadingID'] for r in page2]) - set([r['ReadingID'] for r in page1]) - set([r['ReadingID'] for r in page0])
        self.assertEqual(len(newReadings), 50)

    def test_creates_and_deletes_tables(self):
        self.db.create_reading_db()
        tables = self.db.all_tables()
        self.assertEqual(len(tables), 3)

        self.db.teardown_reading_db()
        tables = self.db.all_tables()
        self.assertEqual(len(tables), 0)

   
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- USER ---------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def test_creates_new_user(self):
        self.db.create_reading_db()
        users = self.db.all_users()

        self.assertEqual(0, len(users))

        self.db.put_user('asd78asdgasiud-asd87agdasd7-asd78asd')
        users = self.db.all_users()
        self.assertEqual(1, len(users))
        
        self.db.put_user('asdasd7as7das7d')
        users = self.db.all_users()
        self.assertEqual(2, len(users))

        self.db.put_user('akakakakakakak')
        users = self.db.all_users()
        self.assertEqual(3, len(users))

    def test_does_not_find_non_existant_user(self):
        self.db.create_reading_db()
        usr = self.db.get_user('asd78asdgasiud-asd87agdasd7-asd78asd')
        self.assertIsNone(usr)

    def test_never_adds_more_than_one_access_group(self):
        self.db.create_reading_db()
        uid = 'asd78asdgasiud-asd87agdasd7-asd78asd'
        agid = 'someid'
        self.db.put_user(uid)

        self.db.create_access_group(agid, 'Roora')
        self.db.add_access_group(uid, agid)
        self.db.add_access_group(uid, agid)
        self.db.add_access_group(uid, agid)
        self.db.add_access_group(uid, agid)
        self.db.add_access_group(uid, agid)

        usr = self.db.get_user(uid)
        user_data = usr.json()
        self.assertEqual(1, len(user_data['AccessGroups']))

        self.db.remove_user_access(uid, agid)
        usr = self.db.get_user(uid)
        user_data = usr.json()
        self.assertEqual(0, len(user_data['AccessGroups']))

    def test_adds_and_removes_data_access_groups(self):
        self.db.create_reading_db()
        uid = 'asd78asdgasiud-asd87agdasd7-asd78asd'
        agid = 'someid'
        self.db.put_user(uid)
        usr = self.db.get_user(uid)
        user_data = usr.json()
        self.assertEqual(0, len(user_data['AccessGroups']))
        
        self.db.create_access_group(agid, 'Roora')
        self.db.add_access_group(uid, agid)
        usr = self.db.get_user(uid)
        user_data = usr.json()
        self.assertEqual(1, len(user_data['AccessGroups']))
        self.assertEqual(
            {'AccessGroupName': 'Roora', 'AccessGroupID': 'someid'}, 
            user_data['AccessGroups'][0]
        )

        self.db.create_access_group('some-otherid', 'Pwetra')
        self.db.add_access_group(uid, 'some-otherid')
        usr = self.db.get_user(uid)
        user_data = usr.json()
        self.assertEqual(2, len(user_data['AccessGroups']))

        self.db.remove_user_access(uid, agid)
        usr = self.db.get_user(uid)
        user_data = usr.json()
        self.assertEqual(1, len(user_data['AccessGroups']))
        self.assertEqual(
            {'AccessGroupName': 'Pwetra', 'AccessGroupID': 'some-otherid'},
            user_data['AccessGroups'][0]
        )

        self.db.remove_user_access(uid, 'some-otherid')
        usr = self.db.get_user(uid)
        user_data = usr.json()
        self.assertEqual(0, len(user_data['AccessGroups']))

    def test_adds_and_removes_org(self):
        self.db.create_reading_db()
        uid = 'asd78asdgasiud-asd87agdasd7-asd78asd'
        orgid = '12037-21341823'
        self.db.put_user(uid)
        usr = self.db.get_user(uid)
        user_data = usr.json()
        self.assertNotIn('Org', user_data)

        self.db.add_org(orgid, 'Vicroads')
        usr = self.db.get_user(uid)
        user_data = usr.json()
        self.assertNotIn('Org', user_data)

        self.db.set_user_org(uid, orgid)
        usr = self.db.get_user(uid)
        user_data = usr.json()
        self.assertIn('Org', user_data)
        self.assertEqual(
            user_data['Org'], 
            {'OrgName': 'Vicroads', 'OrgID': '12037-21341823'}
        )

        self.db.add_org(orgid, 'Roora')
        usr = self.db.get_user(uid)
        user_data = usr.json()
        self.assertEqual(
            user_data['Org'], 
            {'OrgName': 'Roora', 'OrgID': '12037-21341823'}
        )

        orgid2 = '109273-127217'
        self.db.add_org(orgid2, 'Batman')
        self.db.set_user_org(uid, orgid2)
        usr = self.db.get_user(uid)
        user_data = usr.json()
        self.assertEqual(
            user_data['Org'], 
            {'OrgName': 'Batman', 'OrgID': '109273-127217'}
        )

    def test_saves_user_with_correct_pk(self):
        self.db.create_reading_db()

        pk = self.db.put_user('asd78asdgasiud-asd87agdasd7-asd78asd')
        self.assertEqual('asd78asdgasiud-asd87agdasd7-asd78asd', pk)

        users = self.db.all_users()
        self.assertEqual(1, len(users))
        self.assertEqual('asd78asdgasiud-asd87agdasd7-asd78asd', users[0][AdjKeys.SK])
        self.assertEqual('asd78asdgasiud-asd87agdasd7-asd78asd', users[0][AdjKeys.PK])

    def tearDown(self):
        tables = self.db.all_tables()
        if len(tables) > 0:
            self.db.teardown_reading_db()