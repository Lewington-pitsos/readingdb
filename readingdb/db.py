import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from readingdb.normalize import *

class DB():
    def __init__(self, url, resource_name='dynamodb') -> None:
        self.db = boto3.resource(resource_name, endpoint_url=url)

    def create_reading_table(self):
        table = self.db.create_table(
            TableName=Database.READING_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'readingID',
                    'KeyType': 'HASH'  
                },
                {
                    'AttributeName': 'routeID',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'readingID',
                    'AttributeType': 'N'
                },
                {
                    'AttributeName': 'routeID',
                    'AttributeType': 'N'
                },

            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 200,
                'WriteCapacityUnits': 200
            }
        )
        return table
    
    def delete_table(self):
        table = self.db.Table(Database.READING_TABLE_NAME)
        table.delete()

    def put_reading(self, user_id, route_id, reading_id, reading_type, reading_value, timestamp):
        reading_value = encoded_value(reading_type, reading_value)

        table = self.db.Table(Database.READING_TABLE_NAME)
        response = table.put_item(
        Item={
                'readingID': reading_id,
                'routeID': route_id,
                'userID': user_id,
                'type': reading_type, 
                'reading': reading_value, 
                'timestamp': timestamp, 
            }
        )
        return response

    def all_route_readings(self, routeID):
        table = self.db.Table(Database.READING_TABLE_NAME)

        print("table size:", table.table_size_bytes)

        try:
            response = table.scan(FilterExpression=Key('routeID').eq(routeID))
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            print(response)
            return response['Items']