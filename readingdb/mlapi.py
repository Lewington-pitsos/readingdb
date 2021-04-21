import boto3
from readingdb.sqsqueue import SQSQueue

class MLAPI(SQSQueue):
    def __init__(self, queue_url: str) -> None:
        super().__init__()
        self.queue_url = queue_url
        self.sqs = boto3.client('sqs')

    def add_message_to_queue(self, user_id: str, route_id: str) -> str:
        response = self.sqs.send_message(
            QueueUrl = self.queue_url,
            MessageBody=(f"{user_id},{route_id}") 
        )
        return response['MessageId']

    def receive_message_from_queue(self) -> str:
        response = self.sqs.receive_message(
            QueueUrl = self.queue_url,
            AttributeNames=[
                'SentTimestamp'
            ],
            MaxNumberOfMessages=1,
            MessageAttributeNames=[
                'All'
            ],
            VisibilityTimeout=0,
            WaitTimeSeconds=0
        )
        return response['Messages'][0]

    def delete_message_from_queue(self, message: str) -> None:
        self.sqs.delete_message(
            QueueUrl = self.queue_url,
            ReceiptHandle = message['ReceiptHandle']
        )














        

