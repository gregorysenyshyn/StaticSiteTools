import os
import json
import boto3
import traceback
from urllib.parse import parse_qs 

"""
Environment Variables:

VERIFIED_EMAIL
EMAIL_ARN
THANK_YOU_ADDRESS
ERROR_ADDRESS
"""

def send_email(name, phone, email, reason, message):
    client = boto3.client('sesv2')
    response = client.send_email(
        FromEmailAddress=os.environ['VERIFIED_EMAIL'],
        FromEmailAddressIdentityArn=os.environ['EMAIL_ARN'],
        Destination={
        'ToAddresses': [
            os.environ['VERIFIED_EMAIL']
        ]},
      ReplyToAddresses=[
          email.replace(" ", "")
        ],
        Content={
            'Simple': {
                'Subject': {
                    'Data': f'École Violet contact form: {reason}', 
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': f"Message from {name} - {phone}\n{message}",
                        'Charset': 'UTF-8'}
                }
            }
        }
    )
    
def lambda_handler(event, context):
    try:
        body = parse_qs(event["body"], strict_parsing=True)
        name, phone, email, reason, message = "Not Provided"
        if "name" in body:
            name = body["name"][0]
        if "phone" in body:
            phone = body["phone"][0]
        if "email" in body:
            email = body["email"][0]
        if "reason" in body:
            reason = body["reason"][0]
        if "message" in body:
            message = body["message"][0]
            
        send_email(name, phone, email, reason, message)
        return {
            'statusCode': 302,
            'headers': {
                'Location': os.environ['THANK_YOU_ADDRESS']
            }
    }
        return {'statusCode': 200, 'body': 'message sent'}
        

    except Exception as err:
        print(traceback.print_exc())
        return {
            'statusCode': 302,
            'headers': {
                'Location': os.environ['ERROR_ADDRESS']
            },
            'body': json.dumps("That's a problem!")
        }


