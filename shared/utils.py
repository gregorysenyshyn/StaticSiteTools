import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

def load_yaml(data):
    with open(data) as f:
        return yaml.load(f, Loader=Loader)
