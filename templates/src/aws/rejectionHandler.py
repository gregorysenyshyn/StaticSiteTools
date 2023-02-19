import os
import json

import boto3

"""
Setup Steps:
    Verify email addresses
    Add triggers to Lambda function from SES Notifications tab
    Add permissions for Delete Contact

Environment Variables:
    listName
"""

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
            if message['bounce']['bounceType'] == 'Permanent':
                remove_contacts(message['bounce']['bouncedRecipients'])
            else:
                # TODO: What to do with Transient bounces?
                print(message['bounce'])
        elif message['notificationType'] == 'Complaint':
            remove_contacts(message['complaint']['complainedRecipients'])
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

