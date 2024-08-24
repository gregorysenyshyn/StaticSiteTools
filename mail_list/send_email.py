import time
import json
import argparse

import boto3
from botocore.exceptions import ClientError

EMAILS_PER_SECOND = 14

try:
    from shared import utils, client

except ImportError:
    import sys
    sys.path.append(sys.path[0] + '/..')
    from shared import utils, client

########
# Topics
########

def list_topics(ses_client, list_name):
    topics = ses_client.get_contact_list(ContactListName=list_name)["Topics"]
    x = 0
    for topic in topics:
        print(f"{x}. {topic['DisplayName']} - {topic['Description']}")
        x += 1
    return topics


###########
# Templates
###########

def list_templates(ses_client, next_token=None):
    if next_token is None:
        response = ses_client.list_email_templates()
        print("\n\nTemplates Available:")
    else:
        response = ses_client.list_email_templates(NextToken=next_token)
    avail_templates = response["TemplatesMetadata"]
    if "NextToken" in response:
        next_token = response["NextToken"]
    for template in avail_templates:
        print(f'{template["TemplateName"]}')
        if next_token is not None:
            next_answer = input("\nThere are more templates.  See more? (Y/n) ")
            if not next_answer == "n":
                print("\n")
                list_templates(ses_client, next_token)
            else:
                return


def change_templates(ses_client, templates):
    list_templates(ses_client)
    print("\n\nTemplates Currently Selected:")
    if templates: 
        for template in templates:
            print(template)
    else: 
        print("None selected")
    template_answer = "not zero"

    while not template_answer == "0":
        print("\n1. Add Template to Selection")
        print("\n2. Remove Template from Selection")
        print("\n3. Available Templates")
        print("\n0. Back")
        template_answer = input("\nYour Choice? ")
        if template_answer == "1":
            new_template = input("Template name to add? ")
            templates.append(new_template)
        elif template_answer == "2":
            template_to_remove = input("Template name to remove? ")
            templates = [item for (index, item) in enumerate(templates
                                                             ) if not item == template_to_remove]
        elif template_answer == "3":
            list_templates(ses_client)


def create_template(ses_client):
    subject_filename = "subject.txt"
    txt_email_filename = "email.txt"
    html_email_filename = "email.html"

    template_answer = "not zero"
    while not template_answer == "0":
        print(f"""
              \nChange: 
              \n1. Subject File Name ({subject_filename})
              \n2. TXT File Name ({txt_email_filename})
              \n3. HTML File Name ({html_email_filename})
              \n\n0. Ready to Create Template
              """)
        template_answer = input("Your choice? ")
        if template_answer == "1":
            subject_filename = input("New filename? ")
        elif template_answer == "2":
            txt_email_filename = input("New filename? ")
        elif template_answer == "3":
            html_email_filename = input("New filename? ")
        
    with open(subject_filename, "r") as subject:
        subject_string = subject.read()
    with open(txt_email_filename, "r") as txt:
        txt_string = txt.read()
    with open(html_email_filename, "r") as html:
        html_string = html.read()

    view = input("View subject string? (Y/n) ")
    if not view == "n":
        print(subject_string)
    view = input("View txt string? (Y/n) ")
    if not view == "n":
        print(f"TXT String: {txt_string}")
    view = input("View HTML string? (Y/n)")
    if not view == "n":
        print(html_string)

    keep_going = input("Continue? (y/N) ")
    if not keep_going == "y":
        return
    else:
        template_name = input("\nSave template by giving it a name (temp if blank): ")
        if not template_name:
            template_name = "temp"
        ses_client.create_email_template(TemplateName=template_name,
                                         TemplateContent={
                                             'Subject': subject_string,
                                             'Text': txt_string,
                                             'Html': html_string })
        print("Template Uploaded!\n") 
        return template_name

                
def delete_templates(ses_client):
    list_templates(ses_client)
    template_choice = input("Delete which template? ")
    ses_client.delete_email_template(TemplateName=template_choice)
    another = input("Delete another template? (y/N) ")
    if another == "y":
        delete_templates(ses_client)

###############
# Email Sending
###############

def get_contacts(ses_client, list_name, topic, next_token):
    filter_params = { "FilteredStatus": "OPT_IN",
                      "TopicFilter": {
                          "TopicName": topic,
                          "UseDefaultIfPreferenceUnavailable": True}}
    print("Getting Contacts... ", end="")
    if next_token:
        response = ses_client.list_contacts(ContactListName=list_name, Filter=filter_params,
                                            PageSize=14, NextToken=next_token)
        print("but wait!  There's more!")
    else:
        response = ses_client.list_contacts(ContactListName=list_name, Filter=filter_params,
                                            PageSize=14)
        print("That's all the contacts I have!")
    if "NextToken" in response:
        return (response["Contacts"], response["NextToken"])
    else:
        return (response["Contacts"], None)


def check_config_set(ses_client, template_name):
    try:
        response = ses_client.get_configuration_set(ConfigurationSetName=template_name)
    except ses_client.exceptions.NotFoundException:
        ses_client.create_configuration_set(
                ConfigurationSetName=template_name,
                ReputationOptions={'ReputationMetricsEnabled': True },
                SendingOptions={'SendingEnabled': True},
                SuppressionOptions={'SuppressedReasons': ['BOUNCE', 'COMPLAINT']})


def send_email(ses_client, list_options, list_name, contacts,
                        template_name, topic, template_data=None):
    content = {"Template": {'TemplateName': template_name,
                            'TemplateData': template_data}}
    check_config_set(ses_client, template_name)
    response = ses_client.send_email(
                        FromEmailAddress=list_options["email_address"],
                        FromEmailAddressIdentityArn=list_options["email_arn"],
                        Destination={'ToAddresses': contacts},
                        ReplyToAddresses=[list_options["email_address"]],
                        Content=content,
                        ConfigurationSetName=template_name,
                        ListManagementOptions={'ContactListName': list_name,
                                               'TopicName': topic})
    return response


def send_email_to_topic(ses_client, list_options, list_name, templates, topic):
    '''
    Multiple items in templates will equally distribute emails between templates
    '''

    contact_email = list_options["email_address"]

    loop = True
    next_token = None
    template_index = 0
    while loop:

        raw_contacts, next_token = get_contacts(ses_client, list_name, topic, next_token)
        for contact in raw_contacts:

            contact_email = contact["EmailAddress"]
            print(f"Sending email to {contact_email}")
            send_email(ses_client, list_options, list_name, [contact_email], 
                       templates[template_index], topic)

            if template_index == len(templates) - 1:
                template_index = 0
            else:
                template_index += 1

        if not next_token:
            loop = False


def drip_campaign(ses_client, list_options, data, list_name, templates, topic):
    '''
    db field "step" corresponds to templates index (i.e. templates["db_step"])
    and increments after send
    '''
    topic_preference = None
    render_test_complete = False
    contact_list = ses_client.get_contact_list(ContactListName=list_name)

    for topic_data in contact_list["Topics"]:
        if topic_data["TopicName"] == topic:
            topic_preference = topic_data["DefaultSubscriptionStatus"]

    ddb_client = client.get_client("dynamodb", data["options"])
    response = ddb_client.list_tables()
    print("\n\n",response["TableNames"])
    table_name = input("Which table? ")
    response = ddb_client.scan(TableName=table_name)

    for item in response["Items"]:
        stage = 0
        email = ""
        template_data = ""

        try:
            if "stage" in item:
                stage = int(item["stage"]["N"])
            email = item["email"]["S"]
            template_data =f'{{ \"first\":\"{item["first"]["S"]}\",  \"last\":\"{item["last"]["S"]}\" }}'
        except Exception as e:
            print(e)

        if not render_test_complete:
            for template in templates:
                response = ses_client.test_render_email_template(
                                TemplateName=template,
                                TemplateData=template_data
                            )
                print(response["RenderedTemplate"])
                continue_answer = input("Continue? (Y/n) ")
                if continue_answer == "n":
                    print("Aborting!")
                    return
            render_test_complete = True
            print("\n\n######  Test Render Complete!\n\n")

        contact = None
        tries = 0
        while not contact and tries < 2:
            try:
                contact = ses_client.get_contact(ContactListName = list_name, EmailAddress = email)
                if "TopicPreferences" in contact:
                    for topic_data in contact["TopicPreferences"]:
                        if topic_data["TopicName"] == topic:
                            topic_preference = topic_data["SubscriptionStatus"]
            except ClientError as e:
                tries += 1
                if e.response['Error']['Code'] == 'NotFoundException':
                    print(f"Creating new SES contact for {email}")
                    try: 
                        ses_client.create_contact(ContactListName = list_name, EmailAddress = email)
                    except ClientError as e:
                        if e.response['Error']['Code'] == 'TooManyRequestsException':
                            time.sleep(1)
                            ses_client.create_contact(ContactListName = list_name, EmailAddress = email)


        print(f"{email} - {topic}: {topic_preference}...", end=" ")
            
        if topic_preference == "OPT_IN":
            print("Sending...", end=" ")
            response = send_email(ses_client, list_options, list_name, [email], 
                            templates[stage], topic, template_data)
            if response["MessageId"]:
                print(" success")
            else:
                print(" ERROR!!!!")

            stage += 1
            query_string = " ".join([f"UPDATE \"{table_name}\"",
                                    f"SET stage={stage}",
                                    f"WHERE email='{email}'"])
            ddb_client.execute_statement(Statement=query_string)
        else:
            print("SKIPPING!")


def menu(data):
    ses_client = client.get_client('sesv2', data["options"])
    list_options = data["list"]
    contact_list_name = utils.get_list_name(ses_client)
    assert contact_list_name is not None, ("\n\nYou don't have a contact list.",
                                       "Please set one up with setup.py")

    answer = "not zero" 
    topic = None
    templates = []
    while not answer == "0":
        print(f"\n\n### Current Selections ###")
        print(f"\nCurrent Topic: {topic}")
        print("Current Templates:")
        if templates:
            for i in range(len(templates)):
                print(templates[i])
        print("""\n\n### Menu ###
                 \n\n1. Send manual email 
                 \n\n2. Send email to topic
                 \n\n3. Send drip campaign email
                 \n\n4. Change Topic
                 \n\n5. Change Templates
                 \n\n6. Upload Template
                 \n\n7. Delete Template
                 \n\n0. Quit\n\n""")
        answer = input("Your choice: ")
        print("\n\n")
        if answer == "1":
            if topic is None:
                print("Please add a topic!")
                return
            print("Topic is only for list management validation, not sending.")
            contacts = input("Test email address: ")
            if len(templates) < 1:
                print("No template! Please select a template!")
                return

            send_email(ses_client, list_options, contact_list_name, [contacts],
                       templates[0], topic)
        if answer == "2":
            if templates and topic:
                send_email_to_topic(ses_client, list_options, contact_list_name, 
                                    templates, topic)
            else:
                print("Please set template and topic first!")
        elif answer == "3":
            if templates and topic:
                drip_campaign(ses_client, list_options, data, contact_list_name, templates, topic)
            else:
                print("Please set template and topic first!")
        elif answer == "4":
            topics = list_topics(ses_client, contact_list_name)
            topic = input("Which topic number? ")
            topic = topics[int(topic)]["TopicName"]
        elif answer == "5":
            change_templates(ses_client, templates)
        elif answer == "6":
            create_template(ses_client)
        elif answer == "7":
            delete_templates(ses_client)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='YAML data file', required=True)
    args = parser.parse_args()
    data = utils.load_yaml(args.data)
    menu(data)

