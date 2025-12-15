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
    email = "@".join([cf_data['email_address'], options['s3_bucket']])
    print(f'\nChecking status of {email}...')
    try:
        response = sesv2_client.get_email_identity(email)
        if response['VerifiedForSendingStatus']:
            print(f'{email} is verified for sending!')
        else:
            print(f'{email} NOT verified for sending!  Check your email to verify!')
        check_dkim(response, options)
    except:
        answer = input('\n Set up email address now? (Y/n) ')
        if not answer == 'n':
            set_up_email_address(email, options)
            

def set_up_email_address(email_address, options):
    sesv2_client = get_client('sesv2', options)
    pass
    # TODO


def check_dkim(response, options):
    tokens = response['DkimAttributes']['Tokens']
    print(f"\nDKIM CNAME records for {options['s3_bucket']}:")
    for token in tokens:
        print(f"Name: {token}._domainkey.{options['s3_bucket']}")
        print(f"Value: {token}.dkim.amazonses.com")


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='YAML data file')
    args = parser.parse_args()
    data = load_yaml(args.data)
    cf_data = data['contact_form']
    options = data['options']

    set_up_contact_form(cf_data, options)
