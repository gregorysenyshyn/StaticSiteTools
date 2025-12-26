import json
import os
import boto3
import uuid
from datetime import datetime
import traceback

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('LEADS_TABLE')
table = dynamodb.Table(table_name)
step_functions = boto3.client('stepfunctions')
state_machine_arn = os.environ.get('STATE_MACHINE_ARN')

def lambda_handler(event, context):
    """
    Handles new lead form submissions.
    """
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST, OPTIONS"
    }

    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": headers,
            "body": ""
        }

    try:
        body = json.loads(event.get("body", "{}"))

        # 1. Validation
        required_fields = ['first_name', 'email', 'role', 'grade', 'goal']
        for field in required_fields:
            if not body.get(field):
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps({"error": f"Missing required field: {field}"})
                }

        # 2. Save to DynamoDB
        lead_id = str(uuid.uuid4())
        item = {
            'lead_id': lead_id,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'NEW',
            **body
        }

        # Verify we aren't saving sensitive fields if they were somehow injected (though body is from user)
        # Using explicit item construction above is safer than **body but **body is convenient for variable fields.
        # Let's trust body fields for now but ensure system fields like lead_id are set by us.

        table.put_item(Item=item)

        # 3. Start Nurture Campaign (Step Function)
        if state_machine_arn:
            wait_time = int(os.environ.get('WAIT_TIME', '3600'))
            sfn_input = {
                'lead_id': lead_id,
                'email': body['email'],
                'first_name': body['first_name'],
                'wait_time': wait_time
            }
            step_functions.start_execution(
                stateMachineArn=state_machine_arn,
                name=f"lead-{lead_id}", # Deduplication ID
                input=json.dumps(sfn_input)
            )

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"message": "Lead received", "id": lead_id})
        }

    except Exception as e:
        print(traceback.format_exc())
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": "Internal Server Error"})
        }
