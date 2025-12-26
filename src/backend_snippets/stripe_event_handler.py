import json
import os
import boto3
from botocore.exceptions import ClientError

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
ses_client = boto3.client("sesv2")

def lambda_handler(event, context):
    """
    Handles Stripe Events via EventBridge.
    Target Event: payment_intent.succeeded
    """
    print("Received event:", json.dumps(event))

    # EventBridge payload structure for Stripe Partner Events:
    # event['detail'] contains the Stripe event object.
    # event['detail']['data']['object'] contains the PaymentIntent.

    try:
        detail = event.get("detail", {})
        event_type = detail.get("type")

        if event_type == "payment_intent.succeeded":
            # The Stripe Event object is directly in 'detail'
            # The actual resource (PaymentIntent) is in detail['data']['object']
            payment_intent = detail.get("data", {}).get("object", {})
            if payment_intent:
                handle_payment_intent_succeeded(payment_intent)
            else:
                print("No payment intent object found in event detail.")
        else:
            print(f"Unhandled event type: {event_type}")

    except Exception as e:
        print(f"Error processing event: {str(e)}")
        # In EventBridge, raising an exception triggers the retry policy / DLQ.
        raise e

    return {
        "statusCode": 200,
        "body": json.dumps({"status": "success"})
    }

def handle_payment_intent_succeeded(payment_intent):
    """
    Process successful payment intent.
    1. Create record in RegistrationTable
    2. Send Email
    """
    payment_id = payment_intent.get("id")
    amount = payment_intent.get("amount")
    currency = payment_intent.get("currency")
    metadata = payment_intent.get("metadata", {})

    # Extract email - try receipt_email first, then verify with charges
    email = payment_intent.get("receipt_email")
    name = "Student" # Default

    if not email and payment_intent.get("charges") and payment_intent["charges"].get("data"):
        charge = payment_intent["charges"]["data"][0]
        billing_details = charge.get("billing_details", {})
        email = billing_details.get("email")
        name = billing_details.get("name") or name

    # Fallback to metadata if email is still missing
    if not email:
        print(f"No email found for PaymentIntent {payment_id}")
        return

    course_name = metadata.get("course_name", "Course")
    course_code = metadata.get("course_code", "")

    # 1. Update DynamoDB
    table_name = os.environ.get("REGISTRATION_TABLE")
    if not table_name:
        print("REGISTRATION_TABLE env var not set")
        return

    table = dynamodb.Table(table_name)

    try:
        # Only create if it doesn't exist to prevent overwriting a completed registration
        # Note: stripe.util.datetime.utcnow() was used before, but stripe library might not be fully configured/needed.
        # We'll use standard datetime.
        from datetime import datetime
        created_at = int(datetime.utcnow().timestamp())

        table.put_item(
            Item={
                "payment_id": payment_id,
                "email": email,
                "name": name,
                "course_name": course_name,
                "course_code": course_code,
                "amount": amount,
                "currency": currency,
                "status": "PENDING",
                "created_at": created_at
            },
            ConditionExpression="attribute_not_exists(payment_id)"
        )
        print(f"Created pending registration for {payment_id}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print(f"Registration record already exists for {payment_id}. Skipping creation.")
            # Idempotency: assumed processed.
            return
        else:
            raise

    # 2. Send Email
    send_invite_email(email, name, course_name, payment_id)

def send_invite_email(email, name, course_name, payment_id):
    """
    Sends the registration invite email via SES.
    """
    api_url = os.environ.get("API_URL_FOR_EMAIL") or "https://asyncacademy.ca"

    registration_link = f"{api_url}/register?payment_id={payment_id}"

    template_data = {
        "name": name,
        "course_name": course_name,
        "registration_link": registration_link
    }

    sender = os.environ.get("SENDER_EMAIL") or "contact@asyncacademy.ca"
    sender_arn = os.environ.get("SENDER_ARN") # Optional

    try:
        kwargs = {
            'FromEmailAddress': f"Async Academy <{sender}>",
            'Destination': {'ToAddresses': [email]},
            'ReplyToAddresses': [sender],
            'Content': {
                'Template': {
                    'TemplateName': 'course-registration-invite',
                    'TemplateData': json.dumps(template_data)
                }
            }
        }
        if sender_arn:
            kwargs['FromEmailAddressIdentityArn'] = sender_arn

        ses_client.send_email(**kwargs)
        print(f"Sent invite email to {email}")

    except Exception as e:
        print(f"Failed to send email: {str(e)}")
