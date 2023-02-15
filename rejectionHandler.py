import os
import json

import boto3

def remove_contacts(recipients):
    client = boto3.client("sesv2")
    for recipient in recipients:
        email_address = recipient['emailAddress']
        response = client.delete_contact(ContactListName=os.environ['listName'],
                                         EmailAddress=email_address)

def lambda_handler(event, context):
    for record in event['Records']:
        message = json.loads(record['Sns']['Message'])
        if message['notificationType'] == 'Bounce':
            remove_contacts(message['bounce']['bouncedRecipients'])
        elif message['notificationType'] == 'Complaint':
            remove_contacts(message['complaint']['complainedRecipients'])
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

