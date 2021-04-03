from pprint import pprint
from random import sample

import boto3
from boto3.dynamodb.conditions import Key

from readingdb.clean import *

class DB():
    def __init__(self, url, auth, resource_name='dynamodb', config=None):
        self.db = boto3.resource(
            resource_name, 
            endpoint_url=url, 
            config=config,
            aws_access_key_id=auth.id_token,
            aws_secret_access_key=auth.access_token,
        )

    def all_tables(self):
        return list(self.db.tables.all())

    def create_reading_db(self, readCapacity=500, writeCapacity=500):
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

        return (reading_table, route_table)

    def delete_table(self, table_name):
        self.db.Table(table_name).delete()

    def teardown_reading_db(self):
        self.delete_table(Database.READING_TABLE_NAME)
        self.delete_table(Database.ROUTE_TABLE_NAME)

    def put_route(self, user_id, route_id, name=None, sample_data=None): 
        route_table = self.db.Table(Database.ROUTE_TABLE_NAME)
        route = encoded_route_item(user_id, route_id, name, sample_data)

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

    def all_route_readings(self, route_id):
        table = self.db.Table(Database.READING_TABLE_NAME)
        response = table.query(KeyConditionExpression=Key(ReadingRouteKeys.ROUTE_ID).eq(route_id))
        return [decode_item(i) for i in response['Items']]

    def routes_for_user(self, user_id):
        table = self.db.Table(Database.ROUTE_TABLE_NAME)
        response = table.query(KeyConditionExpression=Key(RouteKeys.USER_ID).eq(user_id))
        return [decoded_route_item(i) for i in response['Items']]