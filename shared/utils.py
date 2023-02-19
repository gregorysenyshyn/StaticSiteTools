import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

def load_yaml(data):
    with open(data) as f:
        return yaml.load(f, Loader=Loader)

def get_list_name(ses_client):
    response = ses_client.list_contact_lists()
    return response["ContactLists"][0]["ContactListName"]

