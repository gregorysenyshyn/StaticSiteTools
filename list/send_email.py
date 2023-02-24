import time
import argparse

import boto3

try:
    from shared import utils, client

except ImportError:
    import sys
    sys.path.append(sys.path[0] + '/..')
    from shared import utils, client


def list_topics(ses_client, list_name):
    topics = ses_client.get_contact_list(ContactListName=list_name)["Topics"]
    x = 0
    for topic in topics:
        print(f"{x}. {topic['DisplayName']} - {topic['Description']}")
        x += 1
    return topics


def list_templates(ses_client, next_token=None):
    if next_token is None:
        response = ses_client.list_email_templates()
    else:
        response = ses_client.list_email_templates(NextToken=next_token)
    if next_token is None:
        print("\n\nCurrent Templates:")
    templates = response["TemplatesMetadata"]
    if "NextToken" in response:
        next_token = response["NextToken"]
    for template in templates:
        print(f'{template["TemplateName"]}')
        if next_token is not None:
            next_answer = input("\nThere are more templates.  See more? (Y/n) ")
            if next_answer != "n":
                print("\n")
                list_templates(ses_client, next_token)


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


def get_contacts(ses_client, list_name, topic, next_token):
    filter_params = { "FilteredStatus": "OPT_IN",
                      "TopicFilter": {
                          "TopicName": topic,
                          "UseDefaultIfPreferenceUnavailable": False}}
    print("Getting Contacts... ", end="")
    if next_token:
        response = ses_client.list_contacts(ContactListName=list_name,
                                            Filter=filter_params,
                                            PageSize=14,
                                            NextToken=next_token)
        print("but wait!  There's more!")
    else:
        response = ses_client.list_contacts(ContactListName=list_name,
                                            Filter=filter_params,
                                            PageSize=14)
        print("That's all the contacts I have!")
    if "NextToken" in response:
        return (response["Contacts"], response["NextToken"])
    else:
        return (response["Contacts"], None)


def send_email(ses_client, list_options, list_name, contacts, content, topic):
    print("Sending emails to:")
    for contact in contacts:
        print(contact)
    response = ses_client.send_email(
                        FromEmailAddress=list_options["email_address"],
                        FromEmailAddressIdentityArn=list_options["email_arn"],
                        Destination={'ToAddresses': contacts},
                        ReplyToAddresses=[list_options["email_address"]],
                        Content=content,
                        ConfigurationSetName=list_options["config_set"],
                        ListManagementOptions={'ContactListName': list_name,
                                               'TopicName': topic})


def send_email_to_topic(ses_client, list_options, list_name, 
                        template_name, topic):

    content = {"Template": {'TemplateName': template_name,
                            'TemplateData': '{}'}}
    contact_email = list_options["email_address"]

    loop = True
    next_token = None
    while loop:
        raw_contacts, next_token = get_contacts(ses_client, list_name, 
                                                topic, next_token)
        contacts = []
        for contact in raw_contacts:
            contact_email = contact["EmailAddress"]
            print(f"Adding {contact_email} to batch")
            contacts.append(contact_email)
        if len(contacts) > 0:
            t1 = time.time()
            send_email(ses_client, list_options, list_name,
                       contacts, content, topic)
            sleep_time = 1-((time.time() - t1)/60)
            print(f"Sleeping for {sleep_time} seconds")
            time.sleep(sleep_time)
            print("OK... I'm awake!")

        if not next_token:
            loop = False


def menu(data):
    ses_client = client.get_client('sesv2', data["options"])
    list_options = data["list"]
    contact_list_name = utils.get_list_name(ses_client)
    assert contact_list_name is not None, ("\n\nYou don't have a contact list.",
                                       "Please set one up with setup.py")

    answer = "not zero" 
    topic = None
    while not answer == "0":
        print(f"""\n\n### Menu ###
                  \n\n1. Send test email 
                  \n\n2. Send email to topic
                  \n\n3. Change Topic (Currently: {topic})
                  \n\n4. Create Template
                  \n\n5. Delete Template
                  \n\n0. Quit\n\n""")
        answer = input("Your choice: ")
        print("\n\n")
        if answer == "1":
            template_name = create_template(ses_client)
            send_email_to_topic(ses_client, list_options, contact_list_name, 
                                template_name, topic)
            if template_name == "temp":
                ses_client.delete_email_template(TemplateName="temp")
        if answer == "2":
            print("\n\nPlease choose a template: ")
            list_templates(ses_client)
            template_name = input("Template name? ")
            if template_name:
                send_email_to_topic(ses_client, list_options, contact_list_name, 
                                    template_name, topic)
        elif answer == "3":
            topics = list_topics(ses_client, contact_list_name)
            topic = input("Which topic number? ")
            topic = topics[int(topic)]["TopicName"]
        elif answer == "4":
            create_template(ses_client)
        elif answer == "5":
            delete_templates(ses_client)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='YAML data file', required=True)
    args = parser.parse_args()
    data = utils.load_yaml(args.data)
    menu(data)

