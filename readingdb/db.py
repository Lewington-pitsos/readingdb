from random import sample
from readingdb.utils import timestamp
import time
from readingdb.routestatus import RouteStatus
from typing import Any, Callable, Dict, List, Tuple

import boto3
from boto3.dynamodb.conditions import Key

from readingdb.clean import *
from readingdb.reading import AbstractReading, ddb_to_dict
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
        self.delete_table(Database.READING_TABLE_NAME)
        self.delete_table(Database.ROUTE_TABLE_NAME)
        self.delete_table(Database.USER_TABLE_NAME)

    
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- ROUTE --------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def all_known_users(self) -> List[str]: 
        user_ids = set()
        pg = self.scan_paginator.paginate(TableName=Database.ROUTE_TABLE_NAME)
        for page in pg:
            for item in page[self.ITEM_KEY]:
                user_ids.add(item[RouteKeys.USER_ID])

        return list(user_ids)

    def put_route(self, route: Route): 
        route_table = self.db.Table(Database.ROUTE_TABLE_NAME)
        return route_table.put_item(Item=route.item_data())

    def get_route(self, route_id: str, user_id: str) -> Dict[str, Any]:
        table = self.db.Table(Database.ROUTE_TABLE_NAME)
        response = table.query(
            KeyConditionExpression=Key(ReadingRouteKeys.ROUTE_ID).eq(route_id) & Key(RouteKeys.USER_ID).eq(user_id)
        )

        if len(response[self.ITEM_KEY]) < 1:
            return None

        item = response[self.ITEM_KEY][0]
        Route.decode_item(item)

        return item

    def routes_for_user(self, user_id: str) -> List[Dict[str, Any]]:     
        return self.__ddb_query(
            Database.ROUTE_TABLE_NAME,
            RouteKeys.USER_ID,
            user_id,
            Route.decode_item
        )

    def update_route_name(self, route_id: str, user_id: str, name: str) -> None:
        table = self.db.Table(Database.ROUTE_TABLE_NAME)

        r: Dict[str, Any] = self.get_route(route_id, user_id)

        if r[RouteKeys.NAME] != name:        
            table.update_item(
                Key={
                    ReadingRouteKeys.ROUTE_ID: route_id,
                    RouteKeys.USER_ID: user_id
                },
                UpdateExpression=f'set {RouteKeys.NAME} = :r, {RouteKeys.LAST_UPDATED} = :l',
                ExpressionAttributeValues={
                    ':r': name,
                    ':l': int(time.time())
                },
            )

    def set_route_status(self, route_id: str, user_id: str, status: int) -> None:
        table = self.db.Table(Database.ROUTE_TABLE_NAME)
        
        r: Dict[str, Any] = self.get_route(route_id, user_id)

        if r[RouteKeys.STATUS] != status:
            table.update_item(
                Key={
                    ReadingRouteKeys.ROUTE_ID: route_id,
                    RouteKeys.USER_ID: user_id
                },
                UpdateExpression=f'set {RouteKeys.STATUS} = :r, {RouteKeys.LAST_UPDATED} = :l',
                ExpressionAttributeValues={
                    ':r': status,
                    ':l': int(time.time())
                },
            )

    def __make_route_table(self):
        table = self.db.create_table(
            TableName=Database.ROUTE_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName':  RouteKeys.USER_ID,
                    'KeyType': 'HASH'  
                },
                {
                    'AttributeName': ReadingRouteKeys.ROUTE_ID,
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': RouteKeys.USER_ID,
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': ReadingRouteKeys.ROUTE_ID,
                    'AttributeType': 'S'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 50,
                'WriteCapacityUnits': 50
            }
        )

        self.route_table = table
        return table

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- READING ------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def put_readings(self, readings: List[AbstractReading]):
        table = self.db.Table(Database.READING_TABLE_NAME)
        with table.batch_writer() as batch:
            for r in readings:
                batch.put_item(Item=r.item_data())

    def all_route_readings(self, route_id: str) -> List[Dict[str, Any]]:
        return self.__paginate_table(
            Database.READING_TABLE_NAME,
            ddb_to_dict,
            ReadingRouteKeys.ROUTE_ID,
            route_id,
        )

    def paginated_route_readings(self, route_id: str, last_key: str = None) -> Tuple[List[Dict[str, Any]], str]:
        table = self.db.Table(Database.READING_TABLE_NAME)

        query_params = {
            'KeyConditionExpression': Key('RouteID').eq(route_id),
            'Limit': self.max_page_readings
        }

        if last_key is not None:
            query_params['ExclusiveStartKey']= last_key

        resp = table.query(**query_params)

        next_key = None
        if self.LAST_EVAL_KEY in resp:
            next_key = resp[self.LAST_EVAL_KEY]

        items = []
        for item in resp[self.ITEM_KEY]:
            ddb_to_dict(item)
            items.append(item)

        return items, next_key

    def put_reading(self, reading: AbstractReading):
        table = self.db.Table(Database.READING_TABLE_NAME)
        response = table.put_item(Item=reading.item_data())
        return response

    def delete_reading_items(self, route_id: str, reading_ids: List[str])-> None:
        table = self.db.Table('Readings')
        
        for r in reading_ids:
            table.delete_item(
                Key={
                    ReadingRouteKeys.ROUTE_ID: route_id,
                    ReadingKeys.READING_ID: r
                }
            )

    def __make_reading_table(self):
        table = self.db.create_table(
            TableName=Database.READING_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': ReadingRouteKeys.ROUTE_ID,
                    'KeyType': 'HASH'  
                },
                {
                    'AttributeName': ReadingKeys.READING_ID,
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': ReadingRouteKeys.ROUTE_ID,
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': ReadingKeys.READING_ID,
                    'AttributeType': 'S'
                },

            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 500,
                'WriteCapacityUnits': 500
            }
        )
        self.reading_table = table
        return table

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- USER ---------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def user_data(self, uid: str)-> Dict[str, Any]:
        return self.__ddb_query(
            Database.USER_TABLE_NAME,
            AdjKeys.PK,
            uid,
        )[0]

    def all_users(self) -> List[Dict[str, Any]]:
        users = self.__paginate_table(
            Database.USER_TABLE_NAME,
            lambda item: item
        )

        for u in users:
           self.__decode_adj_pattern_item(u)
        
        return users

    def put_user(self, uid: str):
        user_table = self.db.Table(Database.USER_TABLE_NAME)
        uk = self.__user_k(uid)

        user_table.put_item(Item={
            ReadingKeys.TIMESTAMP: timestamp(),
            AdjKeys.PK: uk,
            AdjKeys.SK: uk
        })

        return uid

    def add_access_group(self, uid: str, agid: str) -> None:
        user_table = self.db.Table(Database.USER_TABLE_NAME)
        uk = self.__user_k(uid)
        gk = self.__group_k(agid)

        user_table.put_item(Item={
            ReadingKeys.TIMESTAMP: timestamp(),
            AdjKeys.PK: gk,
            AdjKeys.SK: gk
        })

        user_table.put_item(Item={
            ReadingKeys.TIMESTAMP: timestamp(),
            AdjKeys.PK: uk,
            AdjKeys.SK: gk
        })

    def __user_k(self, uid: str) -> str:
        return self.__k(uid, UserKeys.USER_SUFFIX)

    def __group_k(self, uid: str) -> str:
        return self.__k(uid, UserKeys.GROUP_SUFFIX)

    def __k(self, identifier: str, prefix: str) -> str:
        return prefix + AdjKeys.DIVIDER + identifier


    def __decode_adj_pattern_item(self, item: Dict[str, Any]) -> str:
        item[AdjKeys.PK] = item[AdjKeys.PK].split(AdjKeys.DIVIDER)[-1]
        item[AdjKeys.SK] = item[AdjKeys.SK].split(AdjKeys.DIVIDER)[-1]

    def __make_user_table(self):
        table = self.db.create_table(
            TableName=Database.USER_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName':  AdjKeys.PK,
                    'KeyType': 'HASH'  
                },
                {
                    'AttributeName': AdjKeys.SK,
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': AdjKeys.PK,
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': AdjKeys.SK,
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 50,
                'WriteCapacityUnits': 50
            }
        )

        self.user_table = table
        return table


