import argparse

import boto3

def createEmailList(client):
    list_name = input("List name: ")
    list_description = input("List Description (private): ")
    add_topic_answer = input("Add one or more topics? (y/n): ")
    if add_topic_answer == 'y':
        topics = get_topics(topics)
    response = client.create_contact_list(ContactListName=list_name,
                                          Topics=topics,
                                          Description=list_description)
    if response['ResponseMetaData']['HTTPStatusCode'] == '200':
        print('List Created Successfully!')
    else:
        print(response)

def get_topics(topics=None):
    if not topics:
        topics = []
    add_topic = True
    while add_topic is True:
        topic_name = input("Topic name: ")
        topic_display_name = input("Topic Display (public) Name: ")
        topic_description = input("Topic Description (public): ")
        opt_in_default = input("Opt into topic by default? (y/n): ")
        if opt_in_default == 'y':
            opt_in_default = 'OPT_IN'
        else:
            opt_in_default = 'OPT_OUT'
        topics.append({'TopicName': topic_name,
                       'DisplayName': topic_display_name,
                       'Description': topic_description,
                       'DefaultSubscriptionStatus': opt_in_default})
        another_topic = input("Add another topic? (y/n): ")
        if another_topic != 'y':
            add_topic = False
    return topics


def get_list_details(ses_client):
    return ses_client.list_contact_lists()


def get_list_name(ses_client):
    response = ses_client.list_contact_lists()
    return response["ContactLists"][0]["ContactListName"]


def add_simulator_emails():
    import boto3
    identity = input("Which AWS credentials? ")
    client = boto3.Session(profile_name=identity, region_name="us-east-1").client("sesv2")
    list_name = get_list_name(client)
    print('\nExisting Addresses')
    response = client.list_contacts(ContactListName=list_name)
    for contact in response['Contacts']:
        print(contact['EmailAddress'])
    print('\nAdding Simulator Emails')
    simulator_emails = ["bounce@simulator.amazonses.com",
                        "complaint@simulator.amazonses.com"]
    for email in simulator_emails:
        try:
            print(client.create_contact(ContactListName = list_name,
                                        EmailAddress = email))
        except:
            print(f"{email} already on list!")

    print('\nCurrent List Emails')
    response = client.list_contacts(ContactListName=list_name)
    for contact in response['Contacts']:
        print(contact['EmailAddress'])


if __name__ == '__main__':

    try:
        from shared import utils, client

    except ImportError:
        import sys
        sys.path.append(sys.path[0] + '/..')
        from shared import utils, client

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='YAML data file', required=True)
    args = parser.parse_args()
    data = utils.load_yaml(args.data)

    ses_client = client.get_client('sesv2', data["options"])
    contact_list_name = None
    try:
        contact_list_name = get_list_name(ses_client)
    except:
        pass
    if contact_list_name is not None:
        topics = ses_client.get_contact_list(ContactListName=contact_list_name)["Topics"]
        print(f"You already have a contact list named {contact_list_name} with topics:")
        for item in topics:
            print(item)
        add_topic_answer = input("Add one or more topics? (y/n): ")
        if add_topic_answer == 'y':
            topics = get_topics(topics)
            ses_client.update_contact_list(ContactListName=contact_list_name,
                                           Topics=topics)
    else:
        createEmailList(ses_client)

