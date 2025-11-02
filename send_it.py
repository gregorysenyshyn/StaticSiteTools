import boto3
from botocore.exceptions import ClientError

import os
import glob
import json
import time
import argparse


from shared import utils
from shared.client import get_client
from website.utils import get_distribution_id
from website.test_api import test_api_endpoints
from website.deploy_lambda import package_lambda, deploy_lambda


def handle_page(filename, destname, options, client):
    extra_args = {'CacheControl': f'max-age={options["cache_control_age"]}',
                  'ContentType': 'text/html'}
    upload_file(filename, destname, extra_args, options, client)


def handle_css(filename, destname, options, client):
    extra_args = {'CacheControl': f'max-age={options["cache_control_age"]}',
                  'ContentType': 'text/css'}
    upload_file(filename, destname, extra_args, options, client)


def handle_js(filename, destname, options, client):
    extra_args = {'CacheControl': f'max-age={options["cache_control_age"]}',
                  'ContentType': 'text/javascript'}
    upload_file(filename, destname, extra_args, options, client)


def handle_image(filename, destname, options, client):
    extra_args = {'CacheControl': f'max-age={options["cache_control_age"]}'}
    if filename.endswith('.svg'):
        extra_args['ContentType'] = 'image/svg+xml'
    elif filename.endswith('.jpg') or filename.endswith('jpeg'):
        extra_args['ContentType'] = 'image/jpeg'
    elif filename.endswith('.png'):
        extra_args['ContentType'] = 'image/png'
    elif filename.endswith('.gif'):
        extra_args['ContentType'] = 'image/gif'
    upload_file(filename, destname, extra_args, options, client)


def upload_file(filename, destname, extra_args, options, client):
    print(f'Copying {filename} to {options["s3_bucket"]}/{destname}...',
          end='')
    with open(filename, 'rb') as f:
        client.upload_fileobj(f,
                              options['s3_bucket'],
                              destname,
                              ExtraArgs=extra_args)
    print(' Done!')


def clean(options, client, images=False):
    response = client.list_objects(Bucket=options['s3_bucket'])
    if 'Contents' in response:
        for item in response['Contents']:
            if not item['Key'].startswith(options['images']) or images:
                print(f'removing {item["Key"]}... ', end='')
                client.delete_object(Bucket=options['s3_bucket'],
                                     Key=item['Key'])
                print(' Done!')


def send_it(options, client):
    for filename in glob.glob(f'{options["dist"]}/**', recursive=True):
        if not filename.startswith('.'):
            if not os.path.isdir(filename):
                destname = filename[len(options['dist'])+1:]
                if destname.endswith('.html'):
                    destname = destname[:-5]
                    handle_page(filename, destname, options, client)
                elif destname.startswith('js/') and destname.endswith('.js'):
                    handle_js(filename, destname, options, client)
                elif destname.startswith('css/') and destname.endswith('.css'):
                    handle_css(filename, destname, options, client)
                elif destname.startswith('images/'):
                    pass
        else:
            print(f'ERROR - Not uploading hidden file {filename}')

def prompt_user(question):
    """Prompts the user for a yes/no answer."""
    answer = input(f'{question} (Y/n) ')
    return not answer.lower() == 'n'

def build_production(data):
    """Builds the production version of the site."""
    if prompt_user('Create new production build?'):
        data['options']['production'] = True
        import build
        build.build(data)

def upload_to_s3(data):
    """Uploads the distribution files to S3."""
    if prompt_user('Ready to send?'):
        print(f'#####\nUploading {data["options"]["dist"]} to {data["options"]["s3_bucket"]}...')
        s3_client = get_client('s3', data['options'])
        send_it(data['options'], s3_client)
        print('Done!\n')

def invalidate_cdn(data):
    """Creates a CloudFront invalidation."""
    if prompt_user("\nCreate CDN invalidation?"):
        cf_client = get_client("cloudfront", data['options'])
        distribution_id = get_distribution_id(cf_client, data['options']['s3_bucket'])
        if distribution_id:
            print(f"\nCreating invalidation for all files in distribution {distribution_id}", end="")
            response = cf_client.create_invalidation(
                            DistributionId=distribution_id,
                            InvalidationBatch={ 'Paths': {
                                "Quantity": 1,
                                "Items": ["/*"] },
                                "CallerReference": str(time.time())
                            }
                            )
            print(" Done!")
            print("\nWaiting for invalidation to complete... ", end="")
            waiter = cf_client.get_waiter('invalidation_completed')
            waiter.wait(DistributionId=distribution_id,
                        Id=response['Invalidation']['Id'])
            print("Done!")
        else:
            print("Could not find distribution ID.")


def check_website_settings(data):
    """Checks the website settings."""
    if prompt_user('\nCheck website settings?'):
        from website.setup import check
        check(data['options'])

def run_api_tests(data):
    """Runs the API tests."""
    if prompt_user('\nRun API tests?'):
        if 'api_endpoints' in data:
            test_api_endpoints(data['api_endpoints'])
        else:
            print("No API endpoints found in the data file.")

def deploy_lambda_functions(data):
    """Deploys the Lambda functions."""
    if prompt_user('\nDeploy Lambda functions?'):
        if 'lambda_functions' in data:
            for function in data['lambda_functions']:
                zip_path = package_lambda(function['path'], function['name'])
                deploy_lambda(zip_path, function, data['options'])
        else:
            print("No Lambda functions found in the data file.")

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='YAML data file')
    args = parser.parse_args()
    data = utils.load_yaml(args.data)

    build_production(data)
    upload_to_s3(data)
    invalidate_cdn(data)
    run_api_tests(data)
    deploy_lambda_functions(data)
    check_website_settings(data)
