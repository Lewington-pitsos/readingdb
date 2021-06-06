from random import sample
import time
from readingdb.routestatus import RouteStatus
from typing import Any, Dict, List, Tuple

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
        self.max_page_readings = max_page_readings

    def all_tables(self) -> List[Any]:
        return list(self.db.tables.all())

    def create_reading_db(
        self, 
        readCapacity=500, 
        writeCapacity=500
    ) -> Tuple[Any, Any]:
        reading_table = self.db.create_table(
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
                'ReadCapacityUnits': readCapacity,
                'WriteCapacityUnits': writeCapacity
            }
        )

        route_table = self.db.create_table(
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
        
        annotator_table = self.db.create_table(
            TableName=Database.ANNOTATOR_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName':  AnnotatorKeys.ANNOTATOR_ID,
                    'KeyType': 'HASH'  
                },
                {
                    'AttributeName':  AnnotatorKeys.ANNOTATOR_GROUP,
                    'KeyType': 'RANGE'  
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': AnnotatorKeys.ANNOTATOR_ID,
                    'AttributeType': 'S'
                },
                {
                    'AttributeName':  AnnotatorKeys.ANNOTATOR_GROUP,
                    'AttributeType': 'S'  
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 50,
                'WriteCapacityUnits': 50
            }
        )

        return (reading_table, route_table, annotator_table)

    def delete_table(self, table_name) -> None:
        self.db.Table(table_name).delete()

    def teardown_reading_db(self) -> None:
        self.delete_table(Database.READING_TABLE_NAME)
        self.delete_table(Database.ROUTE_TABLE_NAME)
        self.delete_table(Database.ANNOTATOR_TABLE_NAME)

    def put_route(self, route: Route): 
        route_table = self.db.Table(Database.ROUTE_TABLE_NAME)
        return route_table.put_item(Item=route.item_data())

    def put_readings(self, readings: List[AbstractReading]):
        
        table = self.db.Table(Database.READING_TABLE_NAME)
        with table.batch_writer() as batch:
            for r in readings:
                response = batch.put_item(Item=r.item_data())
        return response

    def put_reading(self, reading: AbstractReading):
        table = self.db.Table(Database.READING_TABLE_NAME)
        response = table.put_item(Item=reading.item_data())
        return response

    def all_route_readings(self, route_id: str) -> List[Dict[str, Any]]:
        pg = self.paginator.paginate(
            TableName=Database.READING_TABLE_NAME,
            KeyConditionExpression=Key(ReadingRouteKeys.ROUTE_ID).eq(route_id)
        )
        items = []
        for page in pg:
            for item in page[self.ITEM_KEY]:
                ddb_to_dict(item[ReadingKeys.TYPE], item)
                items.append(item)

        return items

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
            ddb_to_dict(item[ReadingKeys.TYPE], item)
            items.append(item)

        return items, next_key

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
        table = self.db.Table(Database.ROUTE_TABLE_NAME)
        response = table.query(KeyConditionExpression=Key(RouteKeys.USER_ID).eq(user_id))

        items = []
        for item in response[self.ITEM_KEY]:
            Route.decode_item(item)
            items.append(item)

        return items

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
