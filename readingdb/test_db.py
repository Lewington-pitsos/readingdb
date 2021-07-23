import signal
import sys
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
from readingdb.reading import PredictionReading, json_to_reading
from readingdb.route import Route

class TestDB(unittest.TestCase):
    def setUp(self):
        self.current_dir = os.path.dirname(__file__)
        self.db = DB('http://localhost:8000')

        def signal_handler(sig, frame):
            self.__cleanup()
            print('Ctrl+C detected, cleaning up test resources...')
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

    def __cleanup(self):
        tables = self.db.all_tables()
        if len(tables) > 0:
            self.db.teardown_reading_db()

    def tearDown(self):
        self.__cleanup()

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- READING ------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def test_saves_readings(self):
        self.db.create_reading_db()
        reading_time = int(time.time())
        uid = 'someuser'
        rid = 'someroute'
        group_id = 'a9a98a9a9a'
        self.db.put_route(Route(uid, group_id, rid, 123151234, geohashes=set(['r3gqu8'])))
        finalized = []
        for i in range(21):
            finalized.append(
                PredictionReading(
                    'sdasdasd-' + str(i),
                    rid,
                    reading_time,
                    Constants.PREDICTION,
                    -33.96788819,
                    151.0181246,
                    'https://aws/s3/somebucket/file.jpg',
                    [],
                    reading_time,
                    DEFAULT_ANNOTATOR_ID,
                )
            )
        self.db.put_readings(finalized)
        readings = self.db.all_route_readings(rid)
        self.assertEqual(len(readings), 21)
        first_reading = readings[0]
        self.assertEqual(first_reading[Constants.ROUTE_ID], 'someroute')
        self.assertEqual(first_reading[Constants.TYPE], Constants.PREDICTION)
        self.assertEqual(first_reading[Constants.READING_ID], 'sdasdasd-0')
        self.assertDictEqual(first_reading[Constants.READING], {
            Constants.ENTITIES: [],
            Constants.FILENAME: 'https://aws/s3/somebucket/file.jpg', 
            Constants.LATITUDE: -33.96788819,
            Constants.LONGITUDE: 151.0181246,
        })
        self.assertEqual(first_reading[Constants.TIMESTAMP], reading_time)
        self.assertEqual(first_reading[Constants.GEOHASH], 'r3gqu8')
        self.assertEqual(first_reading[Constants.READING_ID], 'sdasdasd-0')

    def test_saves_readings_with_severity(self):
        self.db.create_reading_db()
        uid = '103'
        rid = 'xxxa'
        group_id = 'a9a98a9a9a'
        self.db.put_route(Route(uid, group_id, rid, 123151234, geohashes=set(['q6nhhn'])))
        reading_time = int(time.time())

        self.db.put_reading(
            PredictionReading(
                'sdasdasd-',
                rid,
                reading_time,
                Constants.PREDICTION,
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
    
        readings = self.db.all_route_readings(rid)
        self.assertEqual(len(readings), 1)
        first_reading = readings[0]
        self.assertEqual(first_reading[Constants.ROUTE_ID], 'xxxa')
        self.assertEqual(first_reading[Constants.TYPE], Constants.PREDICTION)
        self.assertEqual(first_reading[Constants.READING_ID], 'sdasdasd-')
        self.assertEqual(first_reading[Constants.READING][Constants.ENTITIES][0], {
            'Name': 'Crocodile Cracks',
            'Confidence': 0.432,
            'Severity': 1.876,
            'Present': True
        })
        self.assertEqual(first_reading[Constants.READING][Constants.ENTITIES][1], {
            'Name': 'Rutting',
            'Confidence': 0.432,
            'Severity': 2.1,
            'Present': True
        })

    def test_loads_large_dataset(self):
        route_id = '103'
        group_id = 'a9a98a9a9a'
        self.db.create_reading_db()
        
        with open(self.current_dir +  '/test_data/sydney_entries.json', 'r') as f:
            entities = json.load(f)

        geohashes = set([])
        entity_readings = []
        for e in entities:
            e[Constants.READING_ID] = str(uuid.uuid1())
            e[Constants.ROUTE_ID] = route_id
            r: PredictionReading = json_to_reading('PredictionReading', e)
            geohashes.add(r.geohash())
            entity_readings.append(r)

        self.db.put_route(Route('3', group_id, route_id, 123617823, geohashes=geohashes))
        self.db.put_readings(entity_readings)
        readings = self.db.all_route_readings(route_id)
        self.assertEqual(3383, len(readings))

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- GENERAL ------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def test_creates_and_deletes_tables(self):
        self.db.create_reading_db()
        tables = self.db.all_tables()
        self.assertEqual(len(tables), 2)

        self.db.teardown_reading_db()
        tables = self.db.all_tables()
        self.assertEqual(len(tables), 0)

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- ROUTE --------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    @mock.patch('time.time', mock.MagicMock(side_effect=Increment(1619496879)))
    def test_creates_new_route(self):
        self.db.create_reading_db()
        routes = self.db.routes_for_user('103')
        org_name = 'xero'
        self.assertEqual(len(routes), 0)
        rid = '3'
        uid = '103'
        group_id = '12312543'

        org_data = self.db.put_org(org_name)
        default_org_group = org_data[Constants.ORG_GROUP]
        self.db.put_user(org_name, uid)
        self.db.user_add_group(uid, group_id)
        reading = PredictionReading(
                'sdasdasd-',
                rid,
                123617823,
                Constants.PREDICTION,
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
        self.db.put_reading(reading)
        layer_id = self.db.put_layer(DEFAULT_LAYER_ID, [reading.query_data()])
        self.assertEqual(DEFAULT_LAYER_ID, layer_id)
        self.db.group_add_layer(group_id, DEFAULT_LAYER_ID)

        self.assertEqual(set([group_id, default_org_group]), set(self.db.groups_for_user(uid)))
        self.assertEqual(1, len(self.db.layers_for_user(uid)))

        self.db.put_route(Route(uid, group_id, rid, 123617823, geohashes=[reading.geohash()]))
        routes = self.db.routes_for_user(uid)
        self.assertEqual(len(routes), 1)
        self.assertEqual({
            'Geohashes': ['q6nhhn'],
            'GroupID': group_id,
            'PK': 'Route',
            'SK': 'Route#3',
            'LastUpdated': 1619496880,
            'RouteID': '3',
            'RouteName': '3',
            'RouteStatus': 1,
            'Timestamp': 123617823
        }, routes[0])

    def test_saves_route_written_date(self):
        self.db.create_reading_db()
        user_id = '191732j272'
        group_id = '019191' 
        route_id = '0202020'
        org_name = 'fds'

        self.db.put_org(org_name)
        self.db.put_user(org_name, user_id)
        self.db.user_add_group(user_id, group_id)
        reading = PredictionReading(
                'sdasdasd-',
                route_id,
                123617823,
                Constants.PREDICTION,
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
        self.db.put_reading(reading)
        layer_id = self.db.put_layer(DEFAULT_LAYER_ID, [reading.query_data()])
        self.db.group_add_layer(group_id, layer_id)

        routes = self.db.routes_for_user('103')
        self.assertEqual(len(routes), 0)

        r = Route(user_id, group_id, route_id, 123617823, geohashes=[reading.geohash()])
        last_update_timestamp = r.update_timestamp 
        self.db.put_route(r)

        routes = self.db.routes_for_user(user_id)
        self.assertEqual(routes[0]['LastUpdated'], last_update_timestamp)

    @mock.patch('time.time', mock.MagicMock(side_effect=Increment(1619496879)))
    def test_updates_route_written_date_on_update(self):
        self.db.create_reading_db()
        org_name = 'fds'
        self.db.put_org(org_name)
        routes = self.db.routes_for_user('103')
        self.assertEqual(len(routes), 0)
        route_id = '103'
        user_id = '3'
        group_id = '921929292'

        self.db.put_org(org_name)
        self.db.put_user(org_name, user_id)
        self.db.user_add_group(user_id, group_id)
        reading = PredictionReading(
            'sdasdasd-',
            route_id,
            123617823,
            Constants.PREDICTION,
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
        self.db.put_reading(reading)
        layer_id = self.db.put_layer(DEFAULT_LAYER_ID,[reading.query_data()])
        self.db.group_add_layer(group_id, layer_id)

        r = Route(user_id, group_id, route_id, 123617823, geohashes=[reading.geohash()])
        original_update_timestamp = r.update_timestamp 
        self.db.put_route(r)

        routes = self.db.routes_for_user(user_id)
        self.assertEqual(routes[0]['LastUpdated'], original_update_timestamp)

        self.db.update_route_name(route_id, 'new_name')
        routes = self.db.routes_for_user(user_id)
        name_timestamp = routes[0]['LastUpdated']
        self.assertGreater(name_timestamp, original_update_timestamp)

        self.db.set_route_status(route_id, RouteStatus.COMPLETE)
        routes = self.db.routes_for_user(user_id)
        status_timestamp = routes[0]['LastUpdated']
        self.assertGreater(status_timestamp, name_timestamp)

        self.db.set_route_status(route_id, RouteStatus.COMPLETE)
        routes = self.db.routes_for_user(user_id)
        second_status_timestamp = routes[0]['LastUpdated']
        self.assertEqual(second_status_timestamp, status_timestamp)

        self.db.update_route_name(route_id, 'new_name')
        routes = self.db.routes_for_user(user_id)
        second_name_timestamp = routes[0]['LastUpdated']
        self.assertEqual(second_name_timestamp, second_status_timestamp)

    def deletes_route(self):
        rid = '292929922'
        uid = '287226281'
        group_id = 'a9a9a9a8a8a'
        self.db.create_reading_db()

        route = Route(uid, group_id, rid, 31232143242)
        self.db.put_route(route)
        self.db.remove_route(rid)

    def test_creates_new_route_with_name(self):
        user_id = '238282828'
        group_id = 'asjaaja8a8a'
        route_id = '99929292872'
        org_name = 'fds'

        name = 'someName'
        self.db.create_reading_db()
        routes = self.db.routes_for_user(user_id)
        self.assertEqual(len(routes), 0)

        self.db.put_org(org_name)
        self.db.put_user(org_name, user_id)
        self.db.user_add_group(user_id, group_id)
        reading = PredictionReading(
                'sdasdasd-',
                route_id,
                123617823,
                Constants.PREDICTION,
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
        self.db.put_reading(reading)
        layer_id = self.db.put_layer(DEFAULT_LAYER_ID,[reading.query_data()])
        self.db.group_add_layer(group_id, layer_id)

        self.db.put_route(
            Route(user_id, group_id, route_id, 123617823, name=name, geohashes=[reading.geohash()])
        )
        routes = self.db.routes_for_user(user_id)
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0][Constants.NAME], name)

    def test_creates_new_route_with_sample_data(self):
        route_id = '99227827'
        user_id = '202292922'
        group_id = 'ashasa7sa87a'
        org_name = 'fds'

        self.db.create_reading_db()
        routes = self.db.routes_for_user(user_id)
        self.assertEqual(len(routes), 0)
        reading = PredictionReading(
                'sdasdasd-',
                route_id,
                123617823,
                Constants.PREDICTION,
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

        self.db.put_org(org_name)
        self.db.put_user(org_name, user_id)
        self.db.user_add_group(user_id, group_id)
        self.db.put_reading(reading)
        layer_id = self.db.put_layer(DEFAULT_LAYER_ID,[reading.query_data()])
        self.db.group_add_layer(group_id, layer_id)

        self.db.put_route(Route(
            user_id, 
            group_id,
            route_id, 
            123617823,
            sample_data={'PredictionReading': json_to_reading('PredictionReading', reading.item_data())}
        ))
        routes = self.db.routes_for_user(user_id)
        
        self.assertEqual(len(routes), 1)
        sample_reading = routes[0][Constants.SAMPLE_DATA][Constants.PREDICTION] 
        self.assertEqual(
            sample_reading[Constants.READING_ID], 
            reading.item_data()[Constants.READING_ID]
        )
        self.assertEqual(
            sample_reading[Constants.TIMESTAMP], 
            reading.item_data()[Constants.TIMESTAMP]
        )
        self.assertEqual(
            len(sample_reading[Constants.READING][Constants.ENTITIES]), 
            len(reading.item_data()[Constants.READING][Constants.ENTITIES])
        )

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- LAYER --------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def test_saves_layer_names(self):
        self.db.create_reading_db()
        
        layer_id = 'a9a9a9a9'
        self.db.put_layer(layer_id, name='Default')

        layer = self.db.get_layer(layer_id)

        self.assertEqual('Default', layer[Constants.LAYER_NAME])
        self.assertEqual(0, len(layer[Constants.LAYER_READINGS]))

    def test_creates_layer_when_adding_readings(self):
        self.db.create_reading_db()

        route_id = '103'
        layer_id = '919191919'
        
        with open(self.current_dir + '/test_data/sydney_entries.json', 'r') as f:
            entities = json.load(f)

        geohashes = set([])
        prediction_readings = []
        query_data = []
        for e in entities[:50]:
            e[Constants.READING_ID] = str(uuid.uuid1())
            e[Constants.ROUTE_ID] = route_id
            r: PredictionReading = json_to_reading('PredictionReading', e)
            geohashes.add(r.geohash())
            query_data.append(r.query_data())
            prediction_readings.append(r)

        self.db.put_readings(prediction_readings[:20])
        self.db.add_readings_to_layer(layer_id, query_data[:20])
        readings = self.db.readings_for_layer_id(layer_id)
        self.assertEqual(20, len(readings))

    def test_adds_readings_to_existing_layer(self):
        self.db.create_reading_db()

        route_id = '103'
        layer_id = '919191919'
        
        with open(self.current_dir +  '/test_data/sydney_entries.json', 'r') as f:
            entities = json.load(f)

        geohashes = set([])
        prediction_readings = []
        query_data = []
        for e in entities[:100]:
            e[Constants.READING_ID] = str(uuid.uuid1())
            e[Constants.ROUTE_ID] = route_id
            r: PredictionReading = json_to_reading('PredictionReading', e)
            geohashes.add(r.geohash())
            query_data.append(r.query_data())
            prediction_readings.append(r)
        
        self.db.put_readings(prediction_readings[:50])
        self.db.put_layer(layer_id, query_data[:30])
        readings = self.db.readings_for_layer_id(layer_id)
        self.assertEqual(30, len(readings))

        self.db.put_layer(layer_id, query_data[:40])
        readings = self.db.readings_for_layer_id(layer_id)
        self.assertEqual(40, len(readings))

        self.db.add_readings_to_layer(layer_id, query_data[40:50])
        readings = self.db.readings_for_layer_id(layer_id)
        self.assertEqual(50, len(readings))
        
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # --------------------------- ORG ---------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def test_creates_and_gets_orgs(self):
        self.db.create_reading_db()
        orgs = self.db.get_orgs()
        self.assertEqual(0, len(orgs))

        self.db.put_org('roora', 'sdasdadasd')

        orgs = self.db.get_orgs()
        self.assertEqual(1, len(orgs))
        self.assertEqual('roora', orgs[0][Constants.ORG_NAME])

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- USER ---------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def test_gets_all_users(self):
        group_id = 'aasd'
        self.db.create_reading_db()
        self.db.put_org('roora', 'a9a9a9a9a')
        self.assertEqual(0, len(self.db.all_user_ids('roora')))

        self.db.put_route(Route('someuser_id', group_id, 'someRouteID', 123617823))
        self.assertEqual(0, len(self.db.all_user_ids('roora')))

        self.db.put_user('roora', 'one-armed-larry')
        self.assertEqual(1, len(self.db.all_user_ids('roora')))
        self.db.put_user('roora', 'one-armed-larry')
        self.db.put_user('roora', 'jonny-the-wrench')
        self.assertEqual(2, len(self.db.all_user_ids('roora')))

    def test_gets_user_data(self):
        self.db.create_reading_db()
        org_name = 'Frontline Data Systems'
        org_data = self.db.put_org(org_name)
        default_org_group = org_data[Constants.ORG_GROUP]
        self.db.put_user(org_name, 'wendigo')

        self.db.user_add_group('wendigo', '8a8a8a67a6a6a')
        self.db.user_add_group('wendigo', 'a8sa6d7asd')

        user_data = self.db.user_data(org_name, 'wendigo')
        self.assertEqual('wendigo', user_data[Constants.USER_ID])
        groups = self.db.groups_for_user('wendigo')
        self.assertEqual(set(['8a8a8a67a6a6a', 'a8sa6d7asd', default_org_group]), set(groups))

    def test_creates_new_user(self):
        self.db.create_reading_db()
        org_name = 'Frontline Data Systems'
        users = self.db.all_users(org_name)
        self.assertEqual(0, len(users))

        self.db.put_org(org_name)
        self.db.put_user(
            org_name,
            'asd78asdgasiud-asd87agdasd7-asd78asd',
        )
        users = self.db.all_users(org_name)
        self.assertEqual(1, len(users))
        self.assertEqual('Frontline Data Systems', users[0][Constants.ORG_NAME])
        
        self.db.put_user(
            org_name,
            'asdasd7as7das7d',
        )
        users = self.db.all_users(org_name)
        self.assertEqual(2, len(users))

        self.db.put_user(org_name, 'akakakakakakak')
        users = self.db.all_users(org_name)
        self.assertEqual(3, len(users))

    def test_inserts_data_access_groups(self):
        self.db.create_reading_db()
        org_name = 'ekekeke'

        org_data = self.db.put_org(org_name)
        default_org_group = org_data[Constants.ORG_GROUP]
        self.db.put_user(org_name, 'wendigo') 

        self.db.user_add_group('wendigo', '8a8a8a67a6a6a')
        self.db.user_add_group('wendigo', 'a8sa6d7asd')
        usr = self.db.all_users(org_name)[0]

        self.assertEqual(usr['UserID'], 'wendigo')
        groups = self.db.groups_for_user('wendigo')
        self.assertEqual(set([default_org_group, '8a8a8a67a6a6a', 'a8sa6d7asd']), set(groups))

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- GROUP --------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def test_gets_single_group_for_user(self):
        self.db.create_reading_db()
        group_id = 'as8s8s8s'
        self.db.put_org('someorg')
        self.db.put_user('someorg', 'wendy')
        self.assertFalse(self.db.user_has_group('wendy', group_id))
        self.db.user_add_group('wendy', group_id)

        self.assertTrue(self.db.user_has_group('wendy', group_id))
        self.assertFalse(self.db.user_has_group('wendy', 'othergroup'))
        self.assertFalse(self.db.user_has_group('wendy', 'asdasddsa'))

    def test_names_access_groups(self):
        self.db.create_reading_db()
        group_id = 'as8s8s8s'
        self.db.put_group(group_id, 'good_group')

        group = self.db.get_group(group_id)
        self.assertEqual(group[Constants.GROUP_ID], group_id)
        self.assertEqual(group[Constants.GROUP_NAME], 'good_group')

    def test_adds_name_to_existing_group(self):
        self.db.create_reading_db()
        org_name = 'fds'
        self.db.put_org(org_name)
        self.db.put_user(org_name, 'wendigo') 
        self.db.user_add_group('wendigo', '8a8a8a67a6a6a')

        self.db.set_group_name('8a8a8a67a6a6a', 'xxxx')

        group = self.db.get_group('8a8a8a67a6a6a')
        self.assertEqual(group[Constants.GROUP_ID], '8a8a8a67a6a6a')
        self.assertEqual(group[Constants.GROUP_NAME], 'xxxx')

        self.db.set_group_name('8a8a8a67a6a6a', 'yyyy')

        group = self.db.get_group('8a8a8a67a6a6a')
        self.assertEqual(group[Constants.GROUP_ID], '8a8a8a67a6a6a')
        self.assertEqual(group[Constants.GROUP_NAME], 'yyyy')

