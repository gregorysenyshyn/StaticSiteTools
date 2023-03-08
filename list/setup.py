import argparse

import boto3

try:
    from shared import utils, client

except ImportError:
    import sys
    sys.path.append(sys.path[0] + '/..')
    from shared import utils, client


def createEmailList(client):
    list_name = input("List name: ")
    list_description = input("List Description (private): ")
    topics = []
    add_topic_answer = input("Add one or more topics? (y/n): ")
    if add_topic_answer == 'y':
        topics = add_topic(topics)
    response = client.create_contact_list(ContactListName=list_name,
                                          Topics=topics,
                                          Description=list_description)
    if response['ResponseMetaData']['HTTPStatusCode'] == '200':
        print('List Created Successfully!')
    else:
        print(response)


def add_topic(topics):
    add_topic = True
    while add_topic is True:
        topic_name = input("Topic name: ")
        topic_display_name = input("Topic Display (public) Name: ")
        topic_description = input("Topic Description (public): ")
        opt_in_default = input("Opt into topic by default? (Y/n): ")
        if opt_in_default == 'y':
            opt_in_default = 'OPT_IN'
        else:
            opt_in_default = 'OPT_OUT'
        topics.append({'TopicName': topic_name,
                       'DisplayName': topic_display_name,
                       'Description': topic_description,
                       'DefaultSubscriptionStatus': opt_in_default})
        another_topic = input("Add another topic? (y/N): ")
        if another_topic != 'y':
            add_topic = False
    return topics


def make_list_entry(ses_client, list_name, email):
    try:
        print(client.create_contact(ContactListName = list_name,
                                    EmailAddress = email))
    except:
        print(f"{email} already on list!")


def check_list_entry(ses_client, list_name, email):
    response = ses_client.get_contact(ContactListName = list_name,
                                      EmailAddress = email)
    try:
        print(f"\n\nemail: {response['EmailAddress']}")
        if 'TopicPreferences' in response:
            for topic in response['TopicPreferences']:
                print(f"{topic['TopicName']}: {topic['SubscriptionStatus']}")
        if 'TopicDefaultPreferences' in response:
            for topic in response['TopicDefaultPreferences']:
                print(f"{topic['TopicName']}: {topic['SubscriptionStatus']}")
        print(f"Unsubscribe All: {response['UnsubscribeAll']}")
    except Exception as e:
        print(response)
        print(e)


def add_simulator_emails():
    identity = input("Which AWS credentials? ")
    ses_client = boto3.Session(profile_name=identity, region_name="us-east-1").client("sesv2")
    list_name = utils.get_list_name(ses_client)
    print('\nExisting Addresses')
    response = ses_client.list_contacts(ContactListName=list_name)
    for contact in response['Contacts']:
        print(contact['EmailAddress'])
    answer = input("Add emails?\n1. AWS Simulator\n2. Another email")
    if answer == "1":
        print('\nAdding Simulator Emails')
        simulator_emails = ["bounce@simulator.amazonses.com",
                            "complaint@simulator.amazonses.com"]
        for email in simulator_emails:
            make_list_entry(ses_client, list_name, email)
    elif answer == "2":
        new_email = input("email address to add? ")
        make_list_entry(ses_client, list_name, email)


def export_list():
    import csv

    ses_client = boto3.Session(profile_name=data["options"]["aws_profile_name"],
                               region_name="us-east-1").client("sesv2")
    list_name = utils.get_list_name(ses_client)
    response = ses_client.list_contacts(ContactListName=list_name,
                                                 Filter={
                                                     "FilteredStatus": "OPT_IN",
                                                     "TopicFilter": {
                                                         "TopicName": "now-playing",
                                                         "UseDefaultIfPreferenceUnavailable": True
                                                         }
                                                     }
                                                 )
    contacts = response["Contacts"]
    next_token = response["NextToken"]
    count = 0
    while next_token:
        response = ses_client.list_contacts(ContactListName=list_name,
                                            Filter={
                                                "FilteredStatus": "OPT_IN",
                                                "TopicFilter": {
                                                    "TopicName": "now-playing",
                                                    "UseDefaultIfPreferenceUnavailable": True
                                                    }
                                                },
                                            NextToken=next_token
                                           )
        if "NextToken" in response:
            next_token = response["NextToken"]
        else:
            next_token = None
        count += len(response["Contacts"])
        print(f"Got {len(response['Contacts'])} Contacts - {count} total")
        contacts.extend(response["Contacts"])
    with open('export.csv', 'w', newline='') as f:
        csvwriter = csv.writer(f)
        for contact in contacts:
            print(f"Writing {contact['EmailAddress']}")
            csvwriter.writerow([contact["EmailAddress"]])





def menu(data):
    ses_client = client.get_client('sesv2', data["options"])
    list_name = utils.get_list_name(ses_client)

    if list_name is not None:
        print("###########################")
        print(f"\n\nYou already have a contact list named {list_name}")
        answer = "not zero" 
        while not answer == "0":
            print("\n\n###########################")

            if answer == '1':
                new_email = input("email address: ").lower()
                try:
                    ses_client.create_contact(ContactListName=list_name,
                                              EmailAddress=new_email)
                except ses_client.exceptions.AlreadyExistsException:
                    print(f"{new_email} already on list!")

            elif answer == '2':
                topics = ses_client.get_contact_list(
                                       ContactListName=list_name)["Topics"]
                topics = add_topic(topics)
                ses_client.update_contact_list(ContactListName=list_name,
                                               Topics=topics)

            elif answer == '3':
                email = input("email address to check for? ").lower()
                check_list_entry(ses_client, list_name, email)

            elif answer == '4':
                topics = ses_client.get_contact_list(
                                       ContactListName=list_name)["Topics"]
                for item in topics:
                    print(item)

            elif answer == '5':
                email = input("email address to check for? ")
                topic = input("Topic to change? ")
                direction = input("in or out? (i/o) ")
                if direction == 'i':
                    direction = "OPT_IN"
                elif direction == 'o':
                    direction = "OPT_OUT"
                ses_client.update_contact(
                        ContactListName=list_name,
                        EmailAddress=email,
                        TopicPreferences=[{
                            "TopicName": topic,
                            "SubscriptionStatus": direction
                            }]
                        )
            elif answer == '6':
                print("Current Topics:\n")
                response = ses_client.get_contact_list(
                                       ContactListName=list_name)
                topics = response["Topics"]
                for topic in topics:
                    print(f"{topic['TopicName']}")

                topic_to_delete = input("Delete which topic? ")
                new_topics = [topic for topic in topics if topic["TopicName"] != topic_to_delete]
                ses_client.update_contact_list(ContactListName=list_name,
                                               Topics=new_topics)
                print("Done!")


            print("""### Menu
                  \n\nAdd:\n1. New Contact\n2. New Topic
                  \n\nManage:\n3. Contact Info\n4. Topics
                  \n\nChange:\n5. Topic Opt-In
                  \n\nDelete:\n6. Topic 
                  \n\n0. Quit\n\n""")
            answer = input("Your choice: ")
    else:
        create_answer = input("Create new email list? (Y/n) ")
        if not create_answer == 'n':
            createEmailList(ses_client)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='YAML data file', required=True)
    args = parser.parse_args()
    data = utils.load_yaml(args.data)

    menu(data)
