import json
import os
import stripe

# Initialize Stripe with the secret key from environment variables
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

def lambda_handler(event, context):
    """
    AWS Lambda handler for creating a Stripe PaymentIntent.
    Expected event structure (POST):
    {
        "body": "{\"priceId\": \"price_12345\"}"
    }
    """
    # Enable CORS
    headers = {
        "Access-Control-Allow-Origin": "*", # Replace with your domain in production
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST, OPTIONS"
    }

    # Handle OPTIONS request (preflight)
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": headers,
            "body": ""
        }

    try:
        body = json.loads(event.get("body", "{}"))
        price_id = body.get("priceId")

        if not price_id:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"error": "Missing priceId"})
            }

        # 1. Retrieve the price to verify amount and currency
        # This prevents the frontend from manipulating the price.
        price = stripe.Price.retrieve(price_id, expand=['product'])

        course_name = price.product.name
        course_code = price.product.metadata.get('course_code', '')

        # 2. Create a PaymentIntent
        # For a PaymentIntent, we need the amount in the smallest currency unit (e.g., cents).
        intent = stripe.PaymentIntent.create(
            amount=price.unit_amount,
            currency=price.currency,
            automatic_payment_methods={"enabled": True},
            metadata={
                "price_id": price_id,
                "course_name": course_name,
                "course_code": course_code
            }
        )

        # 3. Return the client secret to the frontend
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "clientSecret": intent.client_secret
            })
        }

    except stripe.error.StripeError as e:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": str(e)})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": "Internal Server Error"})
        }
