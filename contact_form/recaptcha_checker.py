import os
import ast
import json
import urllib3

import boto3

def lambda_handler(event, context):
    try:
        for record in event["Records"]:
            body = ast.literal_eval(record["Sns"]["Message"])
            token = body.get("token")
            action = body.get("action")
            
            recaptcha_body = json.dumps({"event":
                                    {"token": token,
                                     "siteKey": os.environ["SITEKEY"],
                                     "expectedAction": action}})
            http = urllib3.PoolManager()
            response = http.request(method="POST",
                                    url=f"https://recaptchaenterprise.googleapis.com/v1/projects/{os.environ['PROJECT_ID']}/assessments?key={os.environ['API_KEY']}",
                                    body=recaptcha_body)
            data = json.loads(response.data.decode('UTF-8'))
            if data["riskAnalysis"]["score"] > 0.5:
                sns = boto3.resource('sns')

                if action == "contact":
                    topic = sns.Topic('arn:aws:sns:us-east-1:532640115648:email-greg')
                    name = body.get("name")
                    email = body.get("email")
                    phone = body.get("phone")
                    message = body.get("message")
                    topic.publish(Subject=f"Async Academy Contact Form Message",
                                  Message=f"{body['name']} - {body['email']} - {body['phone']}\n\n{body['message']}")

                elif action == "partner_request":
                    topic = sns.Topic('arn:aws:sns:us-east-1:532640115648:partner-request')
                    topic.publish(Message=str(body))
                    

    except Exception as e:
        print(e)
        sns = boto3.resource('sns')
        topic = sns.Topic('arn:aws:sns:us-east-1:532640115648:email-greg')

        topic.publish(Subject="Error in recaptchaChecker",
                      Message="<3 recaptchaChecker")

