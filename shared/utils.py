import argparse

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


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='YAML data file', required=True)
    args = parser.parse_args()
    data = load_yaml(args.data)
    options = data['options']
