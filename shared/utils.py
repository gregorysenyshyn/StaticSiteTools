import argparse

import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

def load_yaml(data):
    with open(data) as f:
        return yaml.load(f, Loader=Loader)

### DDB

def get_ddb_tables(ddb_client):
    response = ddb_client.list_tables()
    return response['TableNames']


### SES v2

def get_list_name(ses_client):
    response = ses_client.list_contact_lists()
    return response["ContactLists"][0]["ContactListName"]


def add_topic(list_name, ses_client):
    topics = ses_client.get_contact_list(
                           ContactListName=list_name)["Topics"]
    add_topic = True
    while add_topic is True:
        topic_name = input("Topic name: ")
        topic_display_name = input("Topic Display (public) Name: ")
        topic_description = input("Topic Description (public): ")
        opt_in_default = input("Opt into topic by default? (Y/n): ")
        if opt_in_default == 'n':
            opt_in_default = 'OPT_OUT'
        else:
            opt_in_default = 'OPT_IN'
        topics.append({'TopicName': topic_name,
                       'DisplayName': topic_display_name,
                       'Description': topic_description,
                       'DefaultSubscriptionStatus': opt_in_default})
        another_topic = input("Add another topic? (y/N): ")
        if another_topic != 'y':
            add_topic = False
    ses_client.update_contact_list(ContactListName=list_name,
                                   Topics=topics)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='YAML data file', required=True)
    args = parser.parse_args()
    data = load_yaml(args.data)
    options = data['options']
