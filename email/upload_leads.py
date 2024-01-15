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
    except Exception as e:
        print("Error with file!")
        get_csv_data()
    print('\n\nField Names: ', header)
    field_name_answer = input('OK to continue? (Y/n) ')
    if field_name_answer == 'n':
        get_csv_data()
    return (header, rows)


def upload_to_ddb(ddb_client, field_names, csv_data):
    print(utils.get_ddb_tables(ddb_client))
    ddb_table = input('DynamoDB Table Name:')
    for lead_data in csv_data:
        query_string = f"INSERT INTO \"{ddb_table}\" value {{"
        for i in range(0, len(field_names)):
            query_string = (
                        query_string + 
                        f" '{field_names[i]}' : '{lead_data[i]}',")
        query_string = query_string[:-1] + "}"
        try:
            print(query_string)
            ddb_client.execute_statement(Statement=query_string)
        except DuplicateItemException:
            print(f"ERROR! Item {lead_data} already exists!")
        except ValidationException:
            print(f"VALIDATION ERROR! Item {lead_data} already exists!")


def menu(data):
    # \n\nManage:\n3. Contact Info\n4. Topics
    # \n\nChange:\n5. Topic Opt-In
    # \n\nDelete:\n6. Topic 
    ddb_client = client.get_client('dynamodb', data["options"])
    print("\n\n################\nDynamo DB Tables\n################\n\n")
    answer = "not zero" 
    while not answer == '0':
        if answer == '1':
            sanitized_answer = input("Have you sanitized all single quotes in your data? (y/N)")
            if sanitized_answer == 'y':
                field_names, csv_data = get_csv_data() 
                upload_to_ddb(ddb_client, field_names, csv_data)

        print("""\n\n########\n### Menu\n########\n
              \n\nImport:\n1. From CSV\n2. New Topic
              \n\n0. Quit\n\n""")
        answer = input("Your choice: ")

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='YAML data file', required=True)
    args = parser.parse_args()
    data = utils.load_yaml(args.data)
    menu(data)
    
