import json
import boto3

def create_website_lead(message):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('leads')
    email = message.get("email")
    full_name = message.get("name")
    table.update_item(Key={"email":email},
                      UpdateExpression="set full_name=:fn",
                      ExpressionAttributeValues={":fn": full_name}
                     )
    # Success email removed as per request
    return (f"New student record created for {email} in leads", f"{full_name}\n<3 newLead")

def email_greg(subject, message):
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-east-1:532640115648:email-greg')
    print("emailing greg")
    topic.publish(Subject=subject, Message=message)

def lambda_handler(event, context):
    try:
        for record in event["Records"]:
            print(record)
            # Use json.loads instead of ast.literal_eval for better JSON handling
            message_body = json.loads(record["Sns"]["Message"])
            subject, message = create_website_lead(message_body)
            # Success email removed: email_greg(subject, message)

    except Exception as e:
        print(e)
        email_greg("Lead record creation failed", "<3 newLead")

    return {
        'statusCode': 200,
        'body': json.dumps('everything is ok')
    }
