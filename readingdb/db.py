from pprint import pprint

import boto3
from boto3.dynamodb.conditions import Key

from readingdb.clean import *

class DB():
    def __init__(self, url, resource_name='dynamodb'):
        self.db = boto3.resource(resource_name, endpoint_url=url)

    def all_tables(self):
        return list(self.db.tables.all())

    def create_reading_db(self, readCapacity=200, writeCapacity=200):
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
                    'AttributeType': 'N'
                },
                {
                    'AttributeName': ReadingKeys.READING_ID,
                    'AttributeType': 'N'
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
                    'AttributeType': 'N'
                },
                {
                    'AttributeName': ReadingRouteKeys.ROUTE_ID,
                    'AttributeType': 'N'
                },

            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 25,
                'WriteCapacityUnits': 25
            }
        )

        return (reading_table, route_table)

    
    def routes_for(self, user_id):
        table = self.db.Table(Database.ROUTE_TABLE_NAME)
        response = table.query(KeyConditionExpression=Key(RouteKeys.USER_ID).eq(user_id))
        return response['Items']

    def delete_table(self, table_name):
        self.db.Table(table_name).delete()

    def teardown_reading_db(self):
        self.delete_table(Database.READING_TABLE_NAME)
        self.delete_table(Database.ROUTE_TABLE_NAME)

    def put_route(self, user_id, route_id, route_name=None): 
        route_table = self.db.Table(Database.ROUTE_TABLE_NAME)

        route = {
                RouteKeys.USER_ID: user_id,
                ReadingRouteKeys.ROUTE_ID: route_id
            }
        
        if route_name:
            route[RouteKeys.NAME] = route_name

        return route_table.put_item(Item=route)

    def put_reading(
        self, 
        route_id, 
        reading_id, 
        reading_type, 
        reading_value, 
        timestamp,
    ):
        reading_value = encoded_value(reading_type, reading_value)
        
        table = self.db.Table(Database.READING_TABLE_NAME)
        response = table.put_item(
            Item={
                    ReadingKeys.READING_ID: reading_id,
                    ReadingRouteKeys.ROUTE_ID: route_id,
                    ReadingKeys.TYPE: reading_type, 
                    ReadingKeys.READING: reading_value, 
                    ReadingKeys.TIMESTAMP: timestamp, 
                }
            )

        return response

    def all_route_readings(self, routeID):
        table = self.db.Table(Database.READING_TABLE_NAME)
        response = table.query(KeyConditionExpression=Key(ReadingRouteKeys.ROUTE_ID).eq(routeID))
        return [decode_item(i) for i in response['Items']]