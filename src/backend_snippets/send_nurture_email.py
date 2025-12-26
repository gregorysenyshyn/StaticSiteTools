import json
import os
import boto3

ses = boto3.client('sesv2')
verified_email = os.environ.get('VERIFIED_EMAIL')
sender_name = os.environ.get('SENDER_NAME', 'Async Academy')
email_arn = os.environ.get('EMAIL_ARN')

def get_email_content(email_type, name):
    if email_type == "welcome":
        subject = "Welcome to Async Academy!"
        body = f"""Hi {name},

Thanks for requesting information about Async Academy!

We specialize in flexible, asynchronous high school credits that fit your schedule. Whether you are looking to catch up, get ahead, or just need a course that works around your life, we are here to help.

Do you have any specific questions about our courses or how the asynchronous model works?

Best,
The Async Academy Team
"""
    elif email_type == "followup":
        subject = "Here is your Async Academy Course Guide"
        body = f"""Hi {name},

I wanted to follow up and share a bit more about how our courses work.

- **Fully Accredited:** All our credits count towards your OSSD.
- **100% Online:** No Zoom calls, no fixed schedule.
- **Fast Track:** Finish a course in as little as 4 weeks.

If you are ready to get started, you can browse our full course calendar here: https://asyncacademy.ca/policies/course-calendar

Let me know if you need help choosing a course!

Best,
The Async Academy Team
"""
    else:
        subject = "Update from Async Academy"
        body = f"Hi {name},\n\nThanks for staying in touch!"

    return subject, body

def lambda_handler(event, context):
    """
    Sends a nurture email based on the input event.
    Expected Input: { "email": "...", "first_name": "...", "type": "welcome" | "followup" }
    """
    try:
        email = event.get('email')
        first_name = event.get('first_name', 'there')
        email_type = event.get('type', 'welcome')

        subject, body = get_email_content(email_type, first_name)

        # Construct "Friendly Name <email>" if sender_name is available
        from_address = f"{sender_name} <{verified_email}>" if sender_name else verified_email

        response = ses.send_email(
            FromEmailAddress=from_address,
            # FromEmailAddressIdentityArn is removed to allow friendly name format
            # as long as the underlying identity (verified_email) is verified.
            Destination={
                'ToAddresses': [email]
            },
            Content={
                'Simple': {
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': body,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            }
        )
        return {"status": "sent", "message_id": response['MessageId']}

    except Exception as e:
        print(f"Error sending email: {str(e)}")
        # We raise the error so Step Functions knows to retry or fail
        raise e
