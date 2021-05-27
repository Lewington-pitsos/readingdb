import uuid
import unittest
import boto3
from moto import mock_sqs

from readingdb.mlapi import MLAPI

@mock_sqs
class TestMLAPI(unittest.TestCase):
    def setUp(self) -> None:
        self.sqs = boto3.client('sqs')
        # We make a uniquely named queue for each test
        # to avoid tests polluting each other by performing
        # actions on the same queue.
        self.queue_name = str(uuid.uuid1())

        self.sqs_url = self.sqs.create_queue(
            QueueName=self.queue_name
        )['QueueUrl']

    def tearDown(self) -> None:
        self.sqs.delete_queue(QueueUrl=self.sqs_url)

    def test_reads_msg(self):
        self.sqs.send_message(
            QueueUrl=self.sqs_url,
            MessageBody='wakka wakka'
        )
        mlapi = MLAPI(self.sqs_url)

        resp = mlapi.receive_message_from_queue()
        self.assertEqual('wakka wakka', resp['Body'])

    def test_writes_then_reads_msg(self):
        mlapi = MLAPI(self.sqs_url)
        mlapi.add_message_to_queue('user776', 'routeabc')

        resp = mlapi.receive_message_from_queue()
        self.assertEqual('user776,routeabc', resp['Body'])
