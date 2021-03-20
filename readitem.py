from pprint import pprint
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


def get_movie(title, year, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")

    table = dynamodb.Table('Movies')

    print("table size:", table.table_size_bytes)

    try:
        response = table.scan(FilterExpression=Key('year').gt(1011))
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print(response)
        return response['Items']

if __name__ == '__main__':
    movie = get_movie("The Big New Movie", 2015,)
    if movie:
        print("Get movie succeeded:")
        pprint(movie, sort_dicts=False)