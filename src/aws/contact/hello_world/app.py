import os
import json
import boto3
import requests
import traceback

def get_recaptcha_score (token):
    google_project_id = os.environ['GOOGLE_PROJECT_ID']
    google_api_key = os.environ['GOOGLE_API_KEY']
    recaptcha_api_key = os.environ["RECAPTCHA_API_KEY"]
    token = token[0]
    print(token)
    recaptcha_url = f"https://recaptchaenterprise.googleapis.com/v1/projects/{google_project_id}/assessments?key={google_api_key}"
    recaptcha_data = f'{{"event":{{"token":"{token}","siteKey":"{recaptcha_api_key}","expectedAction":"submit"}} }}'.encode('ascii')
    print(recaptcha_url)
    print(recaptcha_data)
    headers = {"Content-type": "application/json", "charset": "utf-8"}
    req = request.Request(url=recaptcha_url, data=recaptcha_data)
    # try:
    #     with request.urlopen(req) as f:
    #         print(f.read().decode('utf-8'))
    #     return f.read(0).decode('utf-8')
    # except Exception as e:
    #     print(e.reason)
    #     print(traceback.print_exc())
    return token


def send_email():
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
                        'Charset': 'UTF-8'},
                }
            }
        }
    )
    return {
        'statusCode': 302,
        'headers': {
            'Location': 'https://ontarioliteracy.ca/thank-you'
        },
        'body': json.dumps('Message sent')
    }

def lambda_handler(event, context):
    try:
        body = parse_qs(event["body"], strict_parsing=True)
        score = get_recaptcha_score(body["g-recaptcha-response"])
        print(score)
        return {'statusCode': 200, 'body': score}

    except Exception as err:
        print(traceback.print_exc())
        return {
            'statusCode': 500,
            'headers': {
                'Location': 'https://ontarioliteracy.ca/uh-oh'
            },
            'body': json.dumps("That's a problem!")
        }
