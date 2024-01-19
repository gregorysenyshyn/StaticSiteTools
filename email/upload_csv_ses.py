import csv
import time
import json
import argparse

import boto3

try:
    from shared import utils, client

except ImportError:
    import sys
    sys.path.append(sys.path[0] + '/..')
    from shared import utils, client

"""
csv format 1:
    email, first, last
"""


def import_simple(csv_reader, options):
    ses_client = client.get_client("sesv2", options)
    list_name = utils.get_list_name(ses_client)
    for row in csv_reader:
        email = row[0]
        attributes = json.dumps({ "first": row[1], "last": row[2] })
        print(f"Creating contact for {email}")
        try:
            ses_client.create_contact(ContactListName=list_name,
                                      EmailAddress=email,
                                      AttributesData=attributes)
            time.sleep(1)
        except ses_client.exceptions.AlreadyExistsException:
            print(f"Contact for {email} already exists!")
    print("Finished Successfully!")


def upload_contacts(csv_name, csv_format, options):
    with open(csv_name, "r") as f:
        reader = csv.reader(f)
        if csv_format == 1:
            import_simple(reader, options)


def list_contacts():
    ses_client = client.get_client("sesv2", options)
    list_name = utils.get_list_name(ses_client)
    print(ses_client.list_contacts(ContactListName=list_name))


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='YAML data file', required=True)
    args = parser.parse_args()
    data = utils.load_yaml(args.data)
    options = data['options']
