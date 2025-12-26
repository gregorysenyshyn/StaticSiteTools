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

            # Check risk score (0.0 is risky, 1.0 is safe)
            # Adjust threshold as needed
            if data.get("riskAnalysis", {}).get("score", 0) > 0.5:
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

                elif action == "landing_lead":
                    # 1. Send to studentLead topic for DB storage
                    # Using json.dumps to ensure the consumer receives valid JSON string
                    topic_lead = sns.Topic('arn:aws:sns:us-east-1:532640115648:studentLead')
                    topic_lead.publish(Message=json.dumps(body))

                    # 2. Notify Greg via email
                    topic_email = sns.Topic('arn:aws:sns:us-east-1:532640115648:email-greg')

                    first_name = body.get("first_name", "N/A")
                    last_name = body.get("last_name", "N/A")
                    email = body.get("email", "N/A")
                    role = body.get("role", "N/A")
                    grade = body.get("grade", "N/A")
                    goal = body.get("goal", "N/A")

                    email_subject = f"New Landing Page Lead: {first_name} {last_name}"
                    email_body = (
                        f"Name: {first_name} {last_name}\n"
                        f"Role: {role}\n"
                        f"Email: {email}\n"
                        f"Grade: {grade}\n"
                        f"Goal: {goal}\n"
                        f"Consent: {body.get('consent')}"
                    )

                    topic_email.publish(Subject=email_subject, Message=email_body)

                elif action == "olEmailList":
                    topic = sns.Topic('arn:aws:sns:us-east-1:532640115648:ontarioLiteracyEmailSignup')
                    topic.publish(Subject=f"Ontario Literacy Email Signup",
                                  Message=json.dumps(body))


    except Exception as e:
        logging.exception("Here's your problem")
        sns = boto3.resource('sns')
        topic = sns.Topic('arn:aws:sns:us-east-1:532640115648:email-greg')

        topic.publish(Subject="Error in recaptchaChecker",
                      Message=f"{event}\n\n<3 recaptchaChecker")
