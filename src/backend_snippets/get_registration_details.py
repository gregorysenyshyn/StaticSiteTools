import json
import os
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")

def lambda_handler(event, context):
    """
    Retrieves registration details based on payment_id.
    GET /registration-details?payment_id=...
    """

    # Enable CORS
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "GET, OPTIONS"
    }

    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": headers,
            "body": ""
        }

    payment_id = event.get("queryStringParameters", {}).get("payment_id")

    if not payment_id:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "Missing payment_id"})
        }

    table_name = os.environ.get("REGISTRATION_TABLE")
    if not table_name:
         return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": "Configuration error"})
        }

    table = dynamodb.Table(table_name)

    try:
        response = table.get_item(Key={"payment_id": payment_id})
        item = response.get("Item")

        if not item:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"error": "Registration not found"})
            }

        # Return only safe fields
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "course_name": item.get("course_name"),
                "course_code": item.get("course_code"),
                "email": item.get("email"),
                "student_name": item.get("name"),
                "status": item.get("status")
            })
        }

    except ClientError as e:
        print(e)
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": "Internal Server Error"})
        }
