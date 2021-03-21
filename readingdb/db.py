from pprint import pprint

import boto3
from boto3.dynamodb.conditions import Key

from readingdb.clean import *

class DB():
    def __init__(self, url, resource_name='dynamodb') -> None:
        self.db = boto3.resource(resource_name, endpoint_url=url)

    def all_tables(self):
        return list(self.db.tables.all())

    def create_reading_table(self, readCapacity=200, writeCapacity=200):
        table = self.db.create_table(
            TableName=Database.READING_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName':  Keys.READING_ID,
                    'KeyType': 'HASH'  
                },
                {
                    'AttributeName': Keys.ROUTE_ID,
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': Keys.READING_ID,
                    'AttributeType': 'N'
                },
                {
                    'AttributeName': Keys.ROUTE_ID,
                    'AttributeType': 'N'
                },

            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': readCapacity,
                'WriteCapacityUnits': writeCapacity
            }
        )
        return table
    
    def delete_table(self, table_name):
        table = self.db.Table(table_name)
        table.delete()

    def put_reading(
        self, 
        user_id, 
        route_id, 
        reading_id, 
        reading_type, 
        reading_value, 
        timestamp
    ):
        reading_value = encoded_value(reading_type, reading_value)

        table = self.db.Table(Database.READING_TABLE_NAME)
        response = table.put_item(
        Item={
                Keys.READING_ID: reading_id,
                Keys.ROUTE_ID: route_id,
                Keys.USER_ID: user_id,
                Keys.TYPE: reading_type, 
                Keys.READING: reading_value, 
                Keys.TIMESTAMP: timestamp, 
            }
        )
        return response

    def all_route_readings(self, routeID):
        table = self.db.Table(Database.READING_TABLE_NAME)
        response = table.scan(FilterExpression=Key(Keys.ROUTE_ID).eq(routeID))
        return [decode_item(i) for i in response['Items']]