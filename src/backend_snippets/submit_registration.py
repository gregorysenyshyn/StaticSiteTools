import json
import os
import boto3
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('REGISTRATION_TABLE')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """
    Handles registration form submissions.
    """
    # CORS Headers
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

        # Validation
        required_fields = [
            'oen', 'first_name', 'last_name', 'dob', 'gender', 'grade',
            'status_in_canada', 'student_email', 'preferred_name', 'parent_first_name',
            'parent_last_name', 'parent_email', 'parent_phone',
            'street_address', 'city', 'province', 'postal_code',
            'main_school', 'main_board'
        ]

        missing_fields = [field for field in required_fields if not body.get(field)]

        if missing_fields:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"error": f"Missing required fields: {', '.join(missing_fields)}"})
            }

        payment_id = body.get('payment_id')
        if not payment_id:
             # If no payment_id, generate a unique ID (fallback, though payment_id is preferred)
             payment_id = f"manual_{uuid.uuid4().hex}"

        # Prevent overwriting of system-controlled fields by removing them from body if present
        sensitive_fields = ['status', 'timestamp']
        safe_body = {k: v for k, v in body.items() if k not in sensitive_fields}

        # Prepare Item
        item = {
            'payment_id': payment_id,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'SUBMITTED',
            **safe_body
        }

        # Save to DynamoDB
        table.put_item(Item=item)

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"message": "Registration submitted successfully", "id": payment_id})
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": "Internal Server Error"})
        }
