import os
import json
import boto3
import urllib.request
import urllib.error
import traceback

"""
Environment Variables:

VERIFIED_EMAIL
EMAIL_ARN
GOOGLE_RECAPTCHA_KEY
GOOGLE_API_KEY
GOOGLE_PROJECT_ID
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

        recaptcha_payload = json.dumps({"event":
                                {"token": token,
                                 "siteKey": os.environ["GOOGLE_RECAPTCHA_KEY"],
                                 "expectedAction": "contact"}}).encode('utf-8')

        # Use environment variable for Project ID
        project_id = os.environ.get('GOOGLE_PROJECT_ID')
        if not project_id:
            raise ValueError("GOOGLE_PROJECT_ID environment variable is not set")

        url = f"https://recaptchaenterprise.googleapis.com/v1/projects/{project_id}/assessments?key={os.environ['GOOGLE_API_KEY']}"
        req = urllib.request.Request(url, data=recaptcha_payload, headers={'Content-Type': 'application/json'})

        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))

        if data.get("riskAnalysis", {}).get("score", 0) > 0.5:
            send_email(name, phone, email, message)

        return {'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*'
                },
                'body': 'message sent'}

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"GOOGLE API HTTP ERROR: {e.code} - {e.reason}")
        print(f"ERROR BODY: {error_body}")
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps("Error processing request.")
        }

    except Exception as err:
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps("That's a problem!")
        }
