import boto3
import argparse
import sys
sys.path.append(sys.path[0] + '/..')
from shared.utils import load_yaml
from shared.client import get_client



"""
Steps:
    Get verfied email arn
    Api with Lambda Proxy Integration
    Give Lambda function "SendEmail" permission from SESv2
"""



def set_up_contact_form(cf_data, options):
    sesv2_client = get_client('sesv2', options)
    email = f"{cf_data['email_address']}@{options['s3_bucket']}"
    print(f'\nChecking status of {email}...')
    try:
        response = sesv2_client.get_email_identity(EmailIdentity=email)
        if response['VerifiedForSendingStatus']:
            print(f'{email} is verified for sending!')
        else:
            print(f'{email} NOT verified for sending!  Check your email to verify!')
        check_dkim(response, options)
    except sesv2_client.exceptions.NotFoundException:
        print(f'{email} identity not found.')
        answer = input('\n Set up email address now? (Y/n) ')
        if not answer == 'n':
            set_up_email_address(email, options)
    except Exception as e:
        # Fallback for other errors or if get_email_identity failed for other reasons
        print(f"Error checking email identity: {e}")
        answer = input('\n Set up email address now? (Y/n) ')
        if not answer == 'n':
            set_up_email_address(email, options)
            

def set_up_email_address(email_address, options):
    sesv2_client = get_client('sesv2', options)
    print(f"Creating email identity for {email_address}...")
    try:
        sesv2_client.create_email_identity(EmailIdentity=email_address)
        print(f"Verification email sent to {email_address}. Please check your inbox.")
    except Exception as e:
        print(f"Failed to create email identity: {e}")


def check_dkim(response, options):
    if 'DkimAttributes' in response and 'Tokens' in response['DkimAttributes']:
        tokens = response['DkimAttributes']['Tokens']
        # TODO: Implement DKIM check
        pass
    else:
        # handle cases where DkimAttributes or Tokens are missing
        pass





if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='YAML data file')
    args = parser.parse_args()
    if args.data:
        data = load_yaml(args.data)
        cf_data = data['contact_form']
        options = data['options']

        set_up_contact_form(cf_data, options)
    else:
        parser.print_help()
