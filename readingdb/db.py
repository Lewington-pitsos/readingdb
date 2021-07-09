from random import sample
from readingdb.utils import timestamp
import time
from typing import Any, Callable, Dict, List, Set, Tuple

import boto3
from boto3.dynamodb.conditions import Key

from readingdb.clean import *
from readingdb.reading import PredictionReading, ddb_to_dict, reading_sort_key
from readingdb.route import Route
from readingdb.constants import *

class DB():
    ITEM_KEY = 'Items'
    LAST_EVAL_KEY = 'LastEvaluatedKey'

    def __init__(
        self, 
        url, 
        resource_name='dynamodb',
        region_name='ap-southeast-2', 
        config=None,
        max_page_readings=1800,
    ):
        self.db = boto3.resource(
            resource_name, 
            region_name=region_name,
            endpoint_url=url, 
            config=config,
        )

        # DynamoDB only returns 1MB of data in a single query
        # use paginator on queries that stand a chance of returning
        # > 1MB of data.
        self.paginator = self.db.meta.client.get_paginator('query')
        self.scan_paginator = self.db.meta.client.get_paginator('scan')
        self.max_page_readings = max_page_readings

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- GENERAL ------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def __ddb_query(
        self,
        table_name: str,
        query_key: str, 
        query_value: str,
        decode_fn: Callable[[Dict[str, Any]], Dict[str, Any]] = lambda item: item
    ) -> List[Dict[str, Any]]:
        table = self.db.Table(table_name)
        response = table.query(KeyConditionExpression=Key(query_key).eq(query_value))

        items = []
        for item in response[self.ITEM_KEY]:
            items.append(decode_fn(item))

        return items

    def __paginate_table(
        self, 
        table_name: str,
        decode_fn: Callable[[Dict[str, Any]], Any],
        query_key: str = None,
        query_value: str = None,
    )-> Any:
        if query_key is not None:
            pg = self.paginator.paginate(
                TableName=table_name,
                KeyConditionExpression=Key(query_key).eq(query_value)
            )
        else:
            pg = self.scan_paginator.paginate(
                TableName=table_name,
            )

        items = []
        for page in pg:
            for item in page[self.ITEM_KEY]:
                decode_fn(item)
                items.append(item)

        return items

    def all_tables(self) -> List[Any]:
        return list(self.db.tables.all())

    def create_reading_db(
        self, 
    ) -> Tuple[Any, Any]:
        return (
            self.__make_reading_table(), 
            self.__make_route_table(),
            self.__make_user_table()
        )

    def delete_table(self, table_name) -> None:
        self.db.Table(table_name).delete()

    def teardown_reading_db(self) -> None:
        self.delete_table(Constants.READING_TABLE_NAME)
        self.delete_table(Constants.ROUTE_TABLE_NAME)
        self.delete_table(Constants.USER_TABLE_NAME)

    
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- ROUTE --------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def remove_route(self, route_id: str, user_sub: str):
        table = self.db.Table(Constants.ROUTE_TABLE_NAME)
        table.delete_item(
            Key={
                Constants.ROUTE_ID: route_id,
                Constants.USER_ID: user_sub
            }
        )

    def all_known_users(self) -> List[str]: 
        user_ids = set()
        pg = self.scan_paginator.paginate(TableName=Constants.ROUTE_TABLE_NAME)
        for page in pg:
            for item in page[self.ITEM_KEY]:
                user_ids.add(item[Constants.USER_ID])

        return list(user_ids)

    def put_route(self, route: Route): 
        route_table = self.db.Table(Constants.ROUTE_TABLE_NAME)
        return route_table.put_item(Item=route.item_data())

    def get_route(self, route_id: str, user_id: str) -> Dict[str, Any]:
        table = self.db.Table(Constants.ROUTE_TABLE_NAME)
        response = table.query(
            KeyConditionExpression=Key(Constants.ROUTE_ID).eq(route_id) & Key(Constants.USER_ID).eq(user_id)
        )

        if len(response[self.ITEM_KEY]) < 1:
            return None

        item = response[self.ITEM_KEY][0]
        Route.decode_item(item)

        return item

    def route_geohashes(self, route_id: str, user_id: str) -> Set[str]:
        route = self.get_route(route_id, user_id)

        if route is None:
            return set()

        return set(route[Constants.ROUTE_HASHES])

    def routes_for_user(self, user_id: str) -> List[Dict[str, Any]]:     
        return self.__ddb_query(
            Constants.ROUTE_TABLE_NAME,
            Constants.USER_ID,
            user_id,
            Route.decode_item
        )

    def update_route_name(self, route_id: str, user_id: str, name: str) -> None:
        table = self.db.Table(Constants.ROUTE_TABLE_NAME)

        r: Dict[str, Any] = self.get_route(route_id, user_id)

        if r[Constants.NAME] != name:        
            table.update_item(
                Key={
                    Constants.ROUTE_ID: route_id,
                    Constants.USER_ID: user_id
                },
                UpdateExpression=f'set {Constants.NAME} = :r, {Constants.LAST_UPDATED} = :l',
                ExpressionAttributeValues={
                    ':r': name,
                    ':l': int(time.time())
                },
            )

    def set_route_status(self, route_id: str, user_id: str, status: int) -> None:
        table = self.db.Table(Constants.ROUTE_TABLE_NAME)
        
        r: Dict[str, Any] = self.get_route(route_id, user_id)

        if r[Constants.STATUS] != status:
            table.update_item(
                Key={
                    Constants.ROUTE_ID: route_id,
                    Constants.USER_ID: user_id
                },
                UpdateExpression=f'set {Constants.STATUS} = :r, {Constants.LAST_UPDATED} = :l',
                ExpressionAttributeValues={
                    ':r': status,
                    ':l': int(time.time())
                },
            )

    def __make_route_table(self):
        return self.db.create_table(
            TableName=Constants.ROUTE_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName':  Constants.USER_ID,
                    'KeyType': 'HASH'  
                },
                {
                    'AttributeName': Constants.ROUTE_ID,
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': Constants.USER_ID,
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': Constants.ROUTE_ID,
                    'AttributeType': 'S'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 50,
                'WriteCapacityUnits': 50
            }
        )

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- READING ------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def put_readings(self, readings: List[PredictionReading]):
        table = self.db.Table(Constants.READING_TABLE_NAME)
        with table.batch_writer() as batch:
            for r in readings:
                batch.put_item(Item=r.item_data())

    def all_route_readings(self, route_id: str, user_id: str) -> List[Dict[str, Any]]:
        geohashes = self.route_geohashes(route_id, user_id)
        all_readings = []

        for h in geohashes:
            hash_readings = self.__paginate_table(
                Constants.READING_TABLE_NAME,
                ddb_to_dict,
                Constants.PART_KEY,
                h,
            )
            all_readings.extend([r for r in hash_readings if r[Constants.ROUTE_ID] == route_id])
        
        return all_readings

    def put_reading(self, reading: PredictionReading):
        table = self.db.Table(Constants.READING_TABLE_NAME)
        response = table.put_item(Item=reading.item_data())
        return response

    def delete_reading_items(self, readings: List[Dict[str, str]])-> None:
        table = self.db.Table(Constants.READING_TABLE_NAME)
    
        for r in readings:
            table.delete_item(
                Key={
                    Constants.PART_KEY: r[Constants.GEOHASH],
                    Constants.SORT_KEY: reading_sort_key(r[Constants.LAYER_ID], r[Constants.READING_ID])
                }
            )

    def __make_reading_table(self):
        return self.db.create_table(
            TableName=Constants.READING_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': Constants.PART_KEY,
                    'KeyType': 'HASH'  
                },
                {
                    'AttributeName': Constants.SORT_KEY,
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': Constants.PART_KEY,
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': Constants.SORT_KEY,
                    'AttributeType': 'S'
                },

            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 500,
                'WriteCapacityUnits': 500
            }
        )

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- USER ---------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def user_data(self, uid: str)-> Dict[str, Any]:
        return self.__ddb_query(
            Constants.USER_TABLE_NAME,
            Constants.USER_ID,
            uid,
        )[0]

    def all_users(self) -> List[Dict[str, Any]]:
        return self.__paginate_table(
            Constants.USER_TABLE_NAME,
            lambda item: item
        )

    def put_user(self, uid: str, data_access_groups: List[Dict[str, str]] = []):
        if len(data_access_groups) == 0:
            data_access_groups = [{
                Constants.GROUP_NAME: uid,
                Constants.GROUP_ID: uid
            }]

        for g in data_access_groups:
            assert Constants.GROUP_NAME in g 
            assert Constants.GROUP_ID in g 

        route_table = self.db.Table(Constants.USER_TABLE_NAME)
        route_table.put_item(Item={
            Constants.TIMESTAMP: timestamp(),
            Constants.USER_ID: uid,
            Constants.DATA_ACCESS_GROUPS: data_access_groups 
        })

        return data_access_groups

    def __make_user_table(self):
        return self.db.create_table(
            TableName=Constants.USER_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName':  Constants.USER_ID,
                    'KeyType': 'HASH'  
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': Constants.USER_ID,
                    'AttributeType': 'S'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 50,
                'WriteCapacityUnits': 50
            }
        )


