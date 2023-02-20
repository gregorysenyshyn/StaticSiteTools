import os
import json
import boto3
import traceback
from urllib import request
from urllib.parse import parse_qs, urlencode

"""
Lambda Proxy

Environment Variables:

VERIFIED_EMAIL
EMAIL_ARN
THANK_YOU_ADDRESS
ERROR_ADDRESS
"""

def send_email(body):
    client = boto3.client('sesv2')
    response = client.send_email(
        FromEmailAddress=os.environ['VERIFIED_EMAIL'],
        FromEmailAddressIdentityArn=os.environ['EMAIL_ARN'],
        Destination={
        'ToAddresses': [
            os.environ['VERIFIED_EMAIL']
        ]},
      ReplyToAddresses=[
          body["email"][0].replace(" ", "")
        ],
        Content={
            'Simple': {
                'Subject': {
                    'Data': f'Ontario Literacy contact form: {body["reason"][0]}', 
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': f"Message from {body['name'][0]} - {body['phone'][0]}\n{body['message'][0]}",
                        'Charset': 'UTF-8'}
                }
            }
        }
    )
    
def lambda_handler(event, context):
    try:
        body = parse_qs(event["body"], strict_parsing=True)
        send_email(body)
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

