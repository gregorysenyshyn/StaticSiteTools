import csv
import time
import json
import argparse

import boto3
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


def add_ses_contact(contact, list_name, ses_client, contact_attributes=None):
    try: 
        response = ses_client.create_contact(
                                ContactListName=list_name,
                                EmailAddress=contact["email"],
                                TopicPreferences=[
                                    {'TopicName': contact["topic"],
                                    'SubscriptionStatus': 'OPT_IN'}]
                                )
    except ClientError as e:
        if e.response['Error']['Code'] == "BadRequestException":
            print(f"Topic {contact['topic']} not found.  Creating new topic.")
            utils.add_topic(topics)
            add_ses_contact(contact, list_name, ses_client)


def sync_with_ses(ddb_client):
    # TODO Add topic selection and refine ddb scan query
    ses_client = client.get_client('sesv2', data["options"])
    list_name = utils.get_list_name(ses_client)
    topics = ses_client.get_contact_list(
                           ContactListName=list_name)["Topics"]
    print(f"\n\nTopics:\n{topics}")
    topic_answer = input("Topic name, or 'n' for new topic")
    if topic_answer == "n":
        topics = utils.add_topic(topics, ses_client)




    print_ddb_tables(ddb_client)
    ddb_table = input('DynamoDB Table Name: ')
    ddb_resource = client.get_resource('dynamodb', data["options"])
    table = ddb_resource.Table(ddb_table)
    ddb_response = table.scan(ProjectionExpression='email, #fn, #ln, #st',
                              ExpressionAttributeNames={"#fn":"first",
                                                        "#ln":"last",
                                                        "#st":"step"})
    contacts = ddb_response['Items']
    for contact in contacts:
        try:
            response = ses_client.get_contact(
                                      ContactListName = list_name,
                                      EmailAddress = contact['email'])
        except ClientError as e:
            if e.response['Error']['Code'] == "NotFoundException":
                print(f"Adding contact {contact['email']}")
                add_ses_contact(contact, list_name, ses_client)

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
    
