import csv
import time
import json
import argparse

import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

try:
    from shared import utils, client

except ImportError:
    import sys
    sys.path.append(sys.path[0] + '/..')
    from shared import utils, client


def get_csv_data():
    header = None
    rows = None
    csv_path = input('CSV file path: ')
    try:
        with open(csv_path, "r") as f:
            reader = csv.reader(f)
            all_rows = list(reader)
            header = all_rows[0]
            rows = all_rows[1:]
            print(rows)
    except Exception as e:
        print("Error with file!", e)
    print('\n\nField Names: ', header)
    field_name_answer = input('OK to continue? (Y/n) ')
    if field_name_answer == 'n':
        raise Exception("Cancelled!")
    return (header, rows)

def print_ddb_tables(ddb_client):
    print("\n\n################\nDynamo DB Tables\n################\n\n")
    print(utils.get_ddb_tables(ddb_client))


def upload_to_ddb(ddb_client, field_names, csv_data):
    print_ddb_tables(ddb_client)
    ddb_table = input('DynamoDB Table Name: ')
    for lead_data in csv_data:
        print(lead_data)

        query_string = f"INSERT INTO {ddb_table} value {{"
        for i in range(0, len(field_names)):
            query_string = (query_string + 
                            f" '{field_names[i]}' : '{lead_data[i]}',")
        query_string = query_string[:-1] + "}"

        try:
            print(query_string)
            ddb_client.execute_statement(Statement=query_string)
        except ClientError as e:
            if e.response['Error']['Code'] == "DuplicateItemException":
                print(f"ERROR! Item {lead_data} already exists!")
            elif e.response['Error']['Code'] == "ValidationException":
                print(f"VALIDATION ERROR! {lead_data}")
                print(e)
            continue_answer = input("Continue? (y/N) ")
            if not continue_answer == "y":
                return


def add_ses_contact(contact, list_name, ses_client, topic_name=None, contact_attributes=None):
    topic = topic_name if topic_name else contact.get("topic")
    topic_preferences = []
    if topic:
        topic_preferences = [{'TopicName': topic, 'SubscriptionStatus': 'OPT_IN'}]

    try:
        ses_client.create_contact(
            ContactListName=list_name,
            EmailAddress=contact["email"],
            TopicPreferences=topic_preferences
        )
        print(f"Added contact {contact['email']} to topic '{topic}'")
    except ClientError as e:
        print(f"Error adding contact {contact['email']}: {e}")


def sync_with_ses(ddb_client):
    ses_client = client.get_client('sesv2', data["options"])
    list_name = utils.get_list_name(ses_client)

    selected_topic_name = None
    while not selected_topic_name:
        contact_list = ses_client.get_contact_list(ContactListName=list_name)
        topics = contact_list.get("Topics", [])
        print(f"\nAvailable Topics for list '{list_name}':")
        for i, t in enumerate(topics):
            print(f"{i + 1}. {t['TopicName']} (Display: {t.get('DisplayName', 'N/A')})")

        choice = input("\nSelect topic number, or 'n' to create a new topic: ")

        if choice.lower() == 'n':
            utils.add_topic(list_name, ses_client)
            continue

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(topics):
                selected_topic_name = topics[idx]['TopicName']
            else:
                print("Invalid number. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number or 'n'.")

    print(f"Selected Topic: {selected_topic_name}")

    print_ddb_tables(ddb_client)
    ddb_table = input('DynamoDB Table Name: ')
    ddb_resource = client.get_resource('dynamodb', data["options"])
    table = ddb_resource.Table(ddb_table)

    scan_kwargs = {
        'ProjectionExpression': 'email, #fn, #ln, #st',
        'ExpressionAttributeNames': {"#fn": "first", "#ln": "last", "#st": "step"}
    }

    print("\nDo you want to filter the scan? (e.g., only process items where step=1)")
    filter_attr = input("Enter attribute name to filter by (or press Enter to scan all): ").strip()
    if filter_attr:
        filter_value = input(f"Enter value for '{filter_attr}': ").strip()
        if filter_value.isdigit():
            if input(f"Treat '{filter_value}' as a number? (y/N) ").lower() == 'y':
                filter_value = int(filter_value)

        scan_kwargs['FilterExpression'] = Attr(filter_attr).eq(filter_value)
        print(f"Filtering scan: {filter_attr} == {filter_value}")

    print("Starting DynamoDB scan...")
    done = False
    start_key = None
    total_scanned = 0

    while not done:
        if start_key:
            scan_kwargs['ExclusiveStartKey'] = start_key

        response = table.scan(**scan_kwargs)
        start_key = response.get('LastEvaluatedKey', None)
        done = start_key is None

        items = response.get('Items', [])
        total_scanned += len(items)
        print(f"Scanned page, processing {len(items)} items...")

        for contact in items:
            email = contact.get('email')
            if not email:
                continue

            try:
                ses_client.get_contact(
                    ContactListName=list_name,
                    EmailAddress=email
                )
            except ClientError as e:
                if e.response['Error']['Code'] == "NotFoundException":
                    add_ses_contact(contact, list_name, ses_client, topic_name=selected_topic_name)
                else:
                    print(f"Error checking contact {email}: {e}")

    print(f"\nSync complete. Total items processed: {total_scanned}")

# def quickfix():
#     ddb_client = client.get_client('dynamodb', data["options"])
#     table_name = 'leads_meta'
#     response = ddb_client.scan(TableName=table_name)
#     csv_data = get_csv_data()
#     count = 0
#     count2 = 0
#     for item in response["Items"]:
#         email = item["email"]["S"]
#         if email in csv_data:
#             query_string = " ".join([f"UPDATE \"{table_name}\"",
#                                     "SET stage=1",
#                                     f"WHERE email='{email}'"])
#         else:
#             query_string = " ".join([f"UPDATE \"{table_name}\"",
#                                     "SET stage=0",
#                                     f"WHERE email='{email}'"])
#         ddb_client.execute_statement(Statement=query_string)





def menu(data):
    ddb_client = client.get_client('dynamodb', data["options"])
    answer = "not zero" 
    while not answer == '0':
        if answer == '1':
            sanitized_answer = input("Have you sanitized all single quotes in your data? (y/N) ")
            if sanitized_answer == 'y':
                field_names, csv_data = get_csv_data() 
                upload_to_ddb(ddb_client, field_names, csv_data)
        elif answer == '2':
            sync_with_ses(ddb_client)


        print("""\n\n########\n### Menu\n########\n
              \n\nImport:\n1. From CSV
              \n\n2. Sync with SES
              \n\n0. Quit\n\n""")
        answer = input("Your choice: ")

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='YAML data file', required=True)
    args = parser.parse_args()
    data = utils.load_yaml(args.data)
    menu(data)
    
