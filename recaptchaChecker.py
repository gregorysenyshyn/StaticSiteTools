import os
import json
import logging
import urllib3

import boto3

def lambda_handler(event, context):
    print(event)
    try:
        for record in event["Records"]:
            body = json.loads(record["Sns"]["Message"])
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
            print(data)
            if data["riskAnalysis"]["score"] > 0.5:
                sns = boto3.resource('sns')

                if action == "contact":
                    topic = sns.Topic('arn:aws:sns:us-east-1:532640115648:email-greg')
                    name = body.get("name")
                    email = body.get("email")
                    phone = body.get("phone")
                    message = body.get("message")
                    topic.publish(Subject=f"Async Academy Contact Form Message",
                                  Message=f"{name} - {email} - {phone}\n\n{message}")

                elif action == "callback":
                    topic = sns.Topic('arn:aws:sns:us-east-1:532640115648:studentLead')
                    topic.publish(Message=str(body))
                    name = body.get("name")
                    email = body.get("email")
                    topic = sns.Topic('arn:aws:sns:us-east-1:532640115648:email-greg')
                    topic.publish(Subject=f"Async Academy Callback Request",
                                  Message=f"{name} - {email}")
                    
                    

    except Exception as e:
        logging.exception("Here's your problem")
        sns = boto3.resource('sns')
        topic = sns.Topic('arn:aws:sns:us-east-1:532640115648:email-greg')

        topic.publish(Subject="Error in recaptchaChecker",
                      Message="<3 recaptchaChecker")

