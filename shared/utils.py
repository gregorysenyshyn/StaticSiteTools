import click
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
        topic_name = click.prompt("Topic name")
        topic_display_name = click.prompt("Topic Display (public) Name")
        topic_description = click.prompt("Topic Description (public)")
        if click.confirm("Opt into topic by default?", default=True):
            opt_in_default = 'OPT_IN'
        else:
            opt_in_default = 'OPT_OUT'
        topics.append({'TopicName': topic_name,
                       'DisplayName': topic_display_name,
                       'Description': topic_description,
                       'DefaultSubscriptionStatus': opt_in_default})
        if not click.confirm("Add another topic?", default=False):
            add_topic = False
    ses_client.update_contact_list(ContactListName=list_name,
                                   Topics=topics)


@click.command()
@click.option('--data', help='YAML data file', required=True)
def main(data):
    """This script contains utility functions for the other scripts."""
    data = load_yaml(data)
    options = data['options']


if __name__ == '__main__':
    main()
