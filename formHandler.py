import json
import boto3
import logging

def lambda_handler(event, context):
    sns_client = boto3.client("sns")
    print(event)
    try:
        sns_client.publish(
            TopicArn='arn:aws:sns:us-east-1:532640115648:webForm',
            Message=event["body"]
        )
        body = json.loads(event["body"])
        if body["action"] in ["callback"]:
            message = {"conversion_type": "lead", "query_string_parameters": event["queryStringParameters"]}
            sns_client.publish(
            TopicArn='arn:aws:sns:us-east-1:532640115648:conversionToGA',
               Message=json.dumps(message)
            )
    except Exception as e:
        logging.exception("Here's your problem")
        sns_client.publish(
            TopicArn='arn:aws:sns:us-east-1:532640115648:email-greg',
            Subject='formHandler Error - ',
            Message=json.dumps({"error": str(e)})
        )
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps('Error')
        }

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST'
        },
        'body': json.dumps('Success')
    }

