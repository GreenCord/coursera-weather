import base64
import boto3
import json
import threading

from simple_chalk import chalk
from utils.custom_logging import Logger

file = open("./data/device.json")
device = json.load(file)
file.close()


class SQSHandler(threading.Thread):

    def __init__(self, *args, **kwargs):
        self.logger = Logger("SQSHandler")
        self.queue_url = device["sqsUrl"]
   
    def getMessage(self):
        session = boto3.session.Session()
        sqs = session.client('sqs')
        
        response = sqs.receive_message(
            QueueUrl=self.queue_url,
            AttributeNames=[
                'SentTimeStamp'
            ],
            MaxNumberOfMessages=1,
            MessageAttributeNames=[
                'All'
            ],
            VisibilityTimeout=0,
            WaitTimeSeconds=5
        )
        
        if 'Messages' in response:
            message = response['Messages'][0]
            if 'Body' in message:
                body = base64.b64decode(message['Body'])

            receipt_handle = message['ReceiptHandle']

            sqs.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
            self.logger.info('Received and deleted message: %s' % message)
            self.logger.info('Returning message body %s' % body)
            return body
        else:
            self.logger.info('No messages in queue.')
            return None
