import os
import json

import boto3

"""
Setup Steps:
    Verify email addresses
    Add triggers to Lambda function from SES Notifications tab
    Add permissions for Delete Contact, Get Contact, and Update Contact

Environment Variables:
    listName
"""

def remove_contacts(recipients):
    client = boto3.client("sesv2")
    for recipient in recipients:
        email_address = recipient['emailAddress']
        response = client.delete_contact(ContactListName=os.environ['listName'],
                                         EmailAddress=email_address)

def handle_transient_bounces(recipients):
    client = boto3.client("sesv2")
    list_name = os.environ['listName']

    for recipient in recipients:
        email_address = recipient['emailAddress']
        try:
            # Get current contact data
            response = client.get_contact(
                ContactListName=list_name,
                EmailAddress=email_address
            )

            attributes_data = response.get('AttributesData', '{}')
            attributes = json.loads(attributes_data) if attributes_data else {}

            bounce_count = int(attributes.get('TransientBounceCount', 0))
            bounce_count += 1
            attributes['TransientBounceCount'] = str(bounce_count)

            # If bounce count exceeds threshold, remove contact
            if bounce_count >= 5:
                 print(f"Removing {email_address} due to excessive transient bounces ({bounce_count})")
                 client.delete_contact(
                     ContactListName=list_name,
                     EmailAddress=email_address
                 )
            else:
                # Update contact with new count
                client.update_contact(
                    ContactListName=list_name,
                    EmailAddress=email_address,
                    AttributesData=json.dumps(attributes)
                )
                print(f"Updated {email_address} transient bounce count to {bounce_count}")

        except client.exceptions.NotFoundException:
            print(f"Contact {email_address} not found in list {list_name}, cannot update status.")
        except Exception as e:
            print(f"Error handling transient bounce for {email_address}: {str(e)}")


def lambda_handler(event, context):
    for record in event['Records']:
        message = json.loads(record['Sns']['Message'])
        if message['notificationType'] == 'Bounce': 
            if message['bounce']['bounceType'] == 'Permanent':
                remove_contacts(message['bounce']['bouncedRecipients'])
            else:
                handle_transient_bounces(message['bounce']['bouncedRecipients'])
        elif message['notificationType'] == 'Complaint':
            remove_contacts(message['complaint']['complainedRecipients'])
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
