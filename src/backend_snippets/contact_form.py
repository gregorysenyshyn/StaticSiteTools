import os
import json
import boto3
import urllib.request
import urllib.error
import traceback
import re

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
          email
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

def validate_input(body):
    """
    Validates the input body for required fields and formats.
    Returns (True, None) if valid, or (False, error_message) if invalid.
    """
    required_fields = ['name', 'email', 'message', 'token']
    missing_fields = [field for field in required_fields if not body.get(field)]

    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"

    email = body.get('email', '').strip()
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False, "Invalid email format"

    return True, None

def lambda_handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*'
    }

    try:
        if not event.get("body"):
             return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps("Empty request body")
            }

        body = json.loads(event["body"])

        # Input Validation
        is_valid, error_msg = validate_input(body)
        if not is_valid:
             return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps(error_msg)
            }

        # Sanitize inputs
        name = body.get("name", "").strip()
        phone = body.get("phone", "").strip()
        email = body.get("email", "").strip()
        message = body.get("message", "").strip()
        token = body.get("token", "").strip()

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
            return {
                'statusCode': 200,
                'headers': headers,
                'body': 'message sent'
            }
        else:
             print(f"Recaptcha failed for {email} with score {data.get('riskAnalysis', {}).get('score')}")
             return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps("Recaptcha verification failed")
            }

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"GOOGLE API HTTP ERROR: {e.code} - {e.reason}")
        print(f"ERROR BODY: {error_body}")
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps("Error processing request.")
        }

    except Exception as err:
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps("That's a problem!")
        }
