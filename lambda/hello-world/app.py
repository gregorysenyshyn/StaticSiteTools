import json

def lambda_handler(event, context):
    """
    A simple "hello world" lambda function.
    """
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
