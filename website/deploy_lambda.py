import os
import zipfile
import subprocess
import argparse
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared import utils
from shared.client import get_client

def package_lambda(function_path, function_name):
    """Packages a Lambda function into a zip file."""
    print(f"Packaging Lambda function: {function_name}")
    requirements_path = os.path.join(function_path, 'requirements.txt')
    if os.path.exists(requirements_path):
        print("Installing dependencies...")
        subprocess.check_call(['pip', 'install', '-r', requirements_path, '-t', function_path])

    zip_path = f'/tmp/{function_name}.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(function_path):
            for file in files:
                zf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), function_path))

    print(f"Lambda function packaged: {zip_path}")
    return zip_path

def deploy_lambda(zip_path, function_details, options, dry_run=False):
    """Deploys a Lambda function to AWS."""
    function_name = function_details['name']
    print(f"Deploying Lambda function: {function_name}")
    if dry_run:
        print("Dry run: Skipping actual deployment to AWS.")
        return

    lambda_client = get_client('lambda', options)
    with open(zip_path, 'rb') as f:
        zipped_code = f.read()

    try:
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zipped_code
        )
        print("Lambda function updated successfully.")
    except lambda_client.exceptions.ResourceNotFoundException:
        print("Lambda function not found. Creating a new one...")
        lambda_client.create_function(
            FunctionName=function_name,
            Runtime=function_details.get('runtime', 'python3.9'),
            Role=function_details['role'],
            Handler=function_details.get('handler', 'main.lambda_handler'),
            Code={'ZipFile': zipped_code}
        )
        print("Lambda function created successfully.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='YAML data file')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without deploying to AWS')
    args = parser.parse_args()
    data = utils.load_yaml(args.data)

    if 'lambda_functions' in data:
        for function in data['lambda_functions']:
            if function.get('deploy', True):
                zip_path = package_lambda(function['path'], function['name'])
                deploy_lambda(zip_path, function, data['options'], args.dry_run)
    else:
        print("No Lambda functions found in the data file.")
