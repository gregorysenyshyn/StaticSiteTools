import os
import json

import boto3

def send_email(subject, message):
    client = boto3.client('sesv2')
    response = client.send_email(
        FromEmailAddress=os.environ['VERIFIED_EMAIL'],
        FromEmailAddressIdentityArn=os.environ['EMAIL_ARN'],
        Destination={
        'ToAddresses': [
            os.environ['VERIFIED_EMAIL']
        ]},

        Content={
            'Simple': {
                'Subject': {
                    'Data': f'{subject}', 
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': f"{message}",
                        'Charset': 'UTF-8'}
                }
            }
        }
    )

def lambda_handler(event, context):
    try:
        for record in event["Records"]:
            send_email(record['Sns']['Subject'],
                       record['Sns']['Message'])

    except Exception as e:
        print(e)
        send_email("Error in emailGreg", "uh-oh!")

