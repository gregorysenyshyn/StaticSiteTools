import boto3
from botocore.exceptions import ClientError

import os
import glob
import json
import time
import click


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


def build_production(data):
    """Builds the production version of the site."""
    if click.confirm('Create new production build?', default=True):
        data['options']['production'] = True
        import build
        build.build(data)


def upload_to_s3(data):
    """Uploads the distribution files to S3."""
    if click.confirm('Ready to send?', default=True):
        print(f'#####\nUploading {data["options"]["dist"]} to {data["options"]["s3_bucket"]}...')
        s3_client = get_client('s3', data['options'])
        send_it(data['options'], s3_client)
        print('Done!\n')


def invalidate_cdn(data):
    """Creates a CloudFront invalidation."""
    if click.confirm("\nCreate CDN invalidation?", default=True):
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


def run_api_tests(data):
    """Runs the API tests."""
    if click.confirm('\nRun API tests?', default=True):
        if 'api_endpoints' in data:
            test_api_endpoints(data['api_endpoints'])
        else:
            print("No API endpoints found in the data file.")


def check_website_settings(data):
    """Checks the website settings."""
    if click.confirm('\nCheck website settings?', default=True):
        from website.setup import check
        check(data['options'])


def update_lambda_function(data):
    """Submenu for updating Lambda functions."""
    if 'lambda_functions' not in data:
        click.echo("No Lambda functions found in the data file.")
        return

    lambdas = data['lambda_functions']
    click.echo("\nSelect a Lambda function to update:")
    for idx, func in enumerate(lambdas, 1):
        click.echo(f"{idx}. {func['name']}")

    choice = click.prompt("\nEnter selection", type=int, default=0)

    if 1 <= choice <= len(lambdas):
        selected_func = lambdas[choice - 1]
        click.echo(f"\nDetails for {selected_func['name']}:")
        click.echo(f"  Path: {selected_func.get('path', 'N/A')}")
        click.echo(f"  Runtime: {selected_func.get('runtime', 'python3.9')}")
        click.echo(f"  Handler: {selected_func.get('handler', 'N/A')}")
        click.echo(f"  Role: {selected_func.get('role', 'N/A')}")

        if click.confirm(f"\nDeploy {selected_func['name']}?", default=True):
            zip_path = package_lambda(selected_func['path'], selected_func['name'])
            deploy_lambda(zip_path, selected_func, data['options'])
    else:
        click.echo("Invalid selection.")


@click.command()
@click.option('--data', required=True, help='YAML data file')
def main(data):
    """Main entry point with interactive menu."""
    data_content = utils.load_yaml(data)

    while True:
        click.echo("\nMain Menu:")
        click.echo("1. Create and upload a new production build")
        click.echo("2. Update a lambda function")
        click.echo("3. Exit")

        choice = click.prompt("Please select an option", type=click.Choice(['1', '2', '3']))

        if choice == '1':
            build_production(data_content)
            upload_to_s3(data_content)
            invalidate_cdn(data_content)
            run_api_tests(data_content)
            check_website_settings(data_content)
        elif choice == '2':
            update_lambda_function(data_content)
        elif choice == '3':
            click.echo("Goodbye!")
            break


if __name__ == '__main__':
    main()
