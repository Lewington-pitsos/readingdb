import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from readingdb.normalize import *

class DB():
    def __init__(self) -> None:
        self.db = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
    
    def put_reading(self, user_id, route_id, reading_id, reading_type, reading_value, timestamp):
        reading_value = encoded_value(reading_type, reading_value)

        table = self.db.Table('Readings')
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
    

    def all_route_readings(self, routeID, dynamodb=None):
        table = self.db.Table('Readings')

        print("table size:", table.table_size_bytes)

        try:
            response = table.scan(FilterExpression=Key('routeID').eq(routeID))
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            print(response)
            return response['Items']

