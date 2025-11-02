import requests
import sys
import argparse
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared import utils

def test_api_endpoints(endpoints):
    """Tests a list of API endpoints and prints a summary of the results."""
    print("Testing API endpoints...")
    failures = 0
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint)
            if response.status_code == 200:
                print(f"  SUCCESS: {endpoint} ({response.status_code})")
            else:
                print(f"  FAILURE: {endpoint} ({response.status_code})")
                failures += 1
        except requests.exceptions.RequestException as e:
            print(f"  ERROR: {endpoint} ({e})")
            failures += 1

    if failures > 0:
        print(f"\n{failures} API endpoint tests failed.")
        sys.exit(1)
    else:
        print("\nAll API endpoint tests passed.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='YAML data file')
    args = parser.parse_args()
    data = utils.load_yaml(args.data)

    if 'api_endpoints' in data:
        test_api_endpoints(data['api_endpoints'])
    else:
        print("No API endpoints found in the data file.")
