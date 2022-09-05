import argparse

import boto3

def createEmailList(client):
    list_name = input("List name: ")
    list_description = input("List Description (private): ")
    topics = []
    add_topic = False
    add_topic_answer = input("Add one or more topics? (y/n): ")
    if add_topic_answer == 'y':
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
    response = client.create_contact_list(ContactListName=list_name,
                                          Topics=topics,
                                          Description=list_description)
    if response['ResponseMetaData']['HTTPStatusCode'] == '200':
        print('List Created Successfully!')
    else:
        print(response)


def get_client(options, client_type):
    session = boto3.Session(profile_name=options['aws_profile_name'])
    if client_type == 'acm':
        client = session.client(client_type, region_name='us-east-1')
    else:
        client = session.client(client_type)
    return client


if __name__ == '__main__':

    import tools

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='YAML data file', required=True)
    parser.add_argument('--create-list', help='create new email list',
                        action='store_true')
    args = parser.parse_args()
    data = tools.load_yaml(args.data)

    ses_client = get_client(data['options'], 'sesv2')

    if args.create_list:
        createEmailList(ses_client)

