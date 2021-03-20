import boto3


def create_movie_table(dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")

    table = dynamodb.create_table(
        TableName='Readings',
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


if __name__ == '__main__':
    movie_table = create_movie_table()
    print("Table status:", movie_table.table_status)