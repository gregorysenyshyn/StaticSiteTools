import click
import os
import zipfile
import boto3
import sys
import tempfile
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared import utils

def create_zip_file(function_path, zip_filename):
    """Creates a zip file for the lambda function."""
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(function_path):
            for file in files:
                zipf.write(os.path.join(root, file),
                           os.path.relpath(os.path.join(root, file),
                                           os.path.join(function_path, '..')))

def deploy(config, dry_run):
    """Packages and deploys AWS Lambda functions."""
    if 'lambda_functions' not in config:
        click.echo("No 'lambda_functions' found in the data file.")
        return

    lambda_client = boto3.client('lambda',
                                 region_name=config['options']['aws_region_name'])

    for function_config in config['lambda_functions']:
        function_path = function_config['path']
        function_name = function_config['name']
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_filename = os.path.join(temp_dir, f"{function_name}.zip")

            click.echo(f"Packaging {function_name} from {function_path}...")
            create_zip_file(function_path, zip_filename)
        click.echo(f"Package created at {zip_filename}")

        if not dry_run:
            click.echo(f"Deploying {function_name} to AWS Lambda...")
            with open(zip_filename, 'rb') as f:
                zipped_code = f.read()

            try:
                lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zipped_code
                )
                click.echo(f"Successfully deployed {function_name}.")
            except lambda_client.exceptions.ResourceNotFoundException:
                click.echo(f"Function {function_name} not found. Creating a new one.")
                lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime=function_config['runtime'],
                    Role=function_config['role'],
                    Handler=function_config['handler'],
                    Code={'ZipFile': zipped_code},
                )
                click.echo(f"Successfully created and deployed {function_name}.")
            except Exception as e:
                click.echo(f"Error deploying {function_name}: {e}")
        else:
            click.echo(f"Skipping deployment for {function_name} (dry run).")


@click.command()
@click.option('--data', help='YAML data file', required=True)
@click.option('--dry-run', is_flag=True, help='Do not deploy, just package.')
def main(data, dry_run):
    """Packages and deploys AWS Lambda functions."""
    config = utils.load_yaml(data)
    deploy(config, dry_run)

if __name__ == '__main__':
    main()
