import os
import json

import boto3
import stripe

def get_course_code(product_code):
    reg_form = None
    course_code = None
    if product_code == os.environ.get('AMG_2O_PC'):
        reg_form = os.environ.get('AMG_2O_RF')
        course_code = 'amg-2o'
    elif product_code == os.environ.get('PPL_2O_PC'):
        reg_form = os.environ.get('PPL_2O_RF')
        course_code = 'ppl-2o'
    elif product_code == os.environ.get('PPL_3O_PC'):
        reg_form = os.environ.get('PPL_3O_RF')
        course_code = 'ppl-3o'
    elif product_code == os.environ.get('PPL_4O_PC'):
        reg_form = os.environ.get('PPL_4O_RF')
        course_code = 'ppl-4o'
    return (course_code, reg_form)

def lambda_handler(event, context):
    stripe.api_key = os.environ.get('STRIPE_PRIVATE_KEY')
    if event["type"] == "checkout.session.completed":
        session_id = event["data"]["object"]["id"]

        response = stripe.checkout.Session.list_line_items(session_id)
        product_code = response["data"][0]["price"]["product"]
        course_code, reg_form = get_course_code(product_code)
        email = event["data"]["object"]["customer_details"]["email"]
        name = event["data"]["object"]["customer_details"]["name"]
        template_data = {"name": name, "course_code": course_code, "reg_form": reg_form}


        ses_client = boto3.client('sesv2')
        response = ses_client.send_email(FromEmailAddress='Asynchronous Academy <contact@asyncacademy.ca>',
                                         FromEmailAddressIdentityArn='arn:aws:ses:us-east-1:532640115648:identity/contact@asyncacademy.ca',
                                         Destination={
                                             'ToAddresses': [email],
                                             'BccAddresses': ['registration@asyncacademy.ca']
                                         },
                                         ReplyToAddresses=['contact@asyncacademy.ca'],
                                         Content={
                                            'Template': {
                                                'TemplateName': 'welcome-reg-form',
                                                'TemplateData': json.dumps(template_data)
                                            }
                                         }
                   )
    return {
        'statusCode': 200,
        'body': json.dumps('success')
    }

