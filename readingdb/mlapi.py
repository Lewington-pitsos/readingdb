import boto3
from readingdb.sqsqueue import SQSQueue

class MLAPI(SQSQueue):

    sqs = boto3.client('sqs')


    def add_message_to_queue(queue_url: str, route_id: str) -> str:
        response = sqs.send_message(
            QueueUrl = queue_url,
            DelaySeconds = 10,
            MessageBody=(
                route_id
            ) 
        )
        return response['MessageId']

    def receive_message_from_queue(queue_url: str, ) -> str:
        response = sqs.receive_message(
            QueueUrl = queue_url,
            AttributeNames=[
                'SentTimestamp'
            ],
            MaxNumberOfMEssages=1,
            MessageAttributeNames=[
                'All'
            ],
            VisibilityTimeout=0,
            WaitTimeSeconds=0
        )
        return response['Messages'][0]

    def delete_message_from_queue(queue_url: str, message: str) -> None:
        sqs.delete_message(
            QueueUrl = queue_url,
            ReceiptHandle = message['ReceiptHandle']
        )














        

