import os
import json
import boto3
import urllib3
import traceback

"""
Environment Variables:

VERIFIED_EMAIL
EMAIL_ARN
GOOGLE_RECAPTCHA_KEY
GOOGLE_API_KEY
"""

def send_email(name, phone, email, message):
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
                    'Data': f'Async Academy contact form message', 
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
        body = json.loads(event["body"])
        name = body.get("name")
        phone = body.get("phone")
        email = body.get("email")
        message = body.get("message")
        token = body.get("token")
            
        recaptcha_body = json.dumps({"event":
                                {"token": token,
                                 "siteKey": os.environ["GOOGLE_RECAPTCHA_KEY"],
                                 "expectedAction": "contact"}})
        http = urllib3.PoolManager()
        response = http.request(method="POST",
                                url=f"https://recaptchaenterprise.googleapis.com/v1/projects/async-academy-412723/assessments?key={os.environ['GOOGLE_API_KEY']}",
                                body=recaptcha_body)
        data = json.loads(response.data.decode('UTF-8'))
        print(data)
        if data["riskAnalysis"]["score"] > 0.5:
            send_email(name, phone, email, message)
            
        return {'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*'
                },
                'body': 'message sent'}
        
    except Exception as err:
        print(traceback.print_exc())
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps("That's a problem!")
        }
