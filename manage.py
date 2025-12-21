#!/usr/bin/env python3

import os
import sys
import time
import glob
import click
import subprocess
import boto3
import yaml

# Ensure we can import from local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from shared import utils
from shared.client import get_client
from website import tools
from website.test_api import test_api_endpoints

# Configure PyYAML to ignore CloudFormation tags
def cfn_constructor(loader, node):
    return str(node.value)

for tag in ['!Ref', '!Sub', '!GetAtt', '!Equals', '!Not', '!If', '!Join', '!Select', '!Split', '!FindInMap', '!Base64', '!Cidr', '!And', '!Or', '!Condition']:
    yaml.add_constructor(tag, cfn_constructor, Loader=yaml.SafeLoader)
    yaml.add_constructor(tag, cfn_constructor, Loader=yaml.FullLoader) # In case FullLoader is used

def load_config(config_file):
    """Loads the YAML configuration file."""
    if not os.path.exists(config_file):
        click.echo(f"Error: Configuration file {config_file} not found.")
        sys.exit(1)
    return utils.load_yaml(config_file)

def parse_template_parameters(template_file='template.yaml'):
    """
    Parses template.yaml to find parameters marked with NoEcho: true.
    Returns a list of parameter names that should be treated as secrets.
    """
    click.echo(f"Parsing template for secrets: {os.path.abspath(template_file)}")
    if not os.path.exists(template_file):
        click.echo(f"Warning: {template_file} not found. Cannot infer secrets.")
        return []

    try:
        with open(template_file, 'r') as f:
            template = yaml.load(f, Loader=yaml.SafeLoader)

        secrets = []
        if 'Parameters' in template:
            for param_name, properties in template['Parameters'].items():
                if properties.get('NoEcho') is True:
                    secrets.append(param_name)

        if not secrets:
            click.echo("No parameters with 'NoEcho: true' found in template.")
        else:
            click.echo(f"Found secret parameters: {secrets}")

        return secrets
    except Exception as e:
        click.echo(f"Warning: Failed to parse {template_file}: {e}")
        return []

def get_stack_outputs(stack_name, region, options):
    """Retrieves outputs from a CloudFormation stack."""
    # Use get_client to ensure we use the correct profile if specified
    client = get_client('cloudformation', options)
    try:
        response = client.describe_stacks(StackName=stack_name)
    except client.exceptions.ClientError as e:
        click.echo(f"Error fetching stack {stack_name}: {e}")
        return {}

    outputs = {}
    if 'Stacks' in response and len(response['Stacks']) > 0:
        for output in response['Stacks'][0].get('Outputs', []):
            outputs[output['OutputKey']] = output['OutputValue']
    return outputs

def ensure_secrets(secrets_list, options, env):
    """
    Ensures that required secrets exist in AWS Secrets Manager.
    If missing, prompts the user to create them.
    Returns a dict of parameter overrides using dynamic references (ARNs).
    """
    if not secrets_list:
        return {}

    click.echo("\nVerifying Secrets in AWS Secrets Manager...")
    client = get_client('secretsmanager', options)

    # Use aws_profile_name as project_name, default to 'website' if missing
    project_name = options.get('aws_profile_name', 'website')
    secret_overrides = {}

    for secret_key in secrets_list:
        # Construct the secret name convention: /project/env/Key
        secret_name = f"/{project_name}/{env}/{secret_key}"

        try:
            response = client.describe_secret(SecretId=secret_name)
            click.echo(f"  Found secret: {secret_name}")
            secret_arn = response['ARN']
        except client.exceptions.ResourceNotFoundException:
            click.echo(f"  MISSING secret: {secret_name}")
            value = click.prompt(f"  Enter value for {secret_key}", hide_input=True)

            click.echo(f"  Creating secret {secret_name}...")
            response = client.create_secret(Name=secret_name, SecretString=value)
            click.echo("  Secret created.")
            secret_arn = response['ARN']
        except client.exceptions.ClientError as e:
            click.echo(f"  Error checking secret {secret_name}: {e}")
            sys.exit(1)

        # Construct the dynamic reference string for CloudFormation using full ARN
        # {{resolve:secretsmanager:SECRET_ARN}}
        secret_overrides[secret_key] = f"{{{{resolve:secretsmanager:{secret_arn}}}}}"

    click.echo("All secrets verified.\n")
    return secret_overrides

def check_stack_status(stack_name, options):
    """Checks the status of the stack and offers to delete if stuck."""
    click.echo(f"Checking status of stack {stack_name}...")
    client = get_client('cloudformation', options)
    try:
        response = client.describe_stacks(StackName=stack_name)
        if 'Stacks' in response and len(response['Stacks']) > 0:
            status = response['Stacks'][0]['StackStatus']
            # Expanded list of failed/stuck states
            failed_states = [
                'ROLLBACK_COMPLETE',
                'ROLLBACK_FAILED',
                'CREATE_FAILED',
                'REVIEW_IN_PROGRESS',
                'DELETE_FAILED'
            ]
            if status in failed_states:
                click.echo(f"\nWarning: Stack {stack_name} is in {status} state.")
                if click.confirm("Do you want to delete this stack before redeploying?", default=True):
                    click.echo(f"Deleting stack {stack_name}...")
                    client.delete_stack(StackName=stack_name)
                    click.echo("Deletion initiated. Waiting for stack to be deleted...")
                    waiter = client.get_waiter('stack_delete_complete')
                    waiter.wait(StackName=stack_name)
                    click.echo("Stack deleted.")
    except client.exceptions.ClientError:
        # Stack doesn't exist, which is fine
        click.echo("Stack does not exist (clean state).")
        pass

def build_site(data):
    """Builds the static website using website.tools."""
    print('\nStarting build!')
    t0 = time.time()

    print('\n\n=== C L E A N ===')
    if 'dist' in data['options']:
        print(f'cleaning {data["options"]["dist"]}...', end='')
        tools.clean(data['options']['dist'])
        print(' Done!')

    print('\n\n=== J S ===')
    if 'js' in data:
        for dest_path in data['js']['paths']:
            tools.handle_js(data, dest_path)

    print('\n\n=== C S S ===')
    if 'scss' in data:
        for dest_path in data['scss']['paths']:
            tools.handle_scss(data, dest_path)

    print('\n\n=== H T M L ===')
    t1 = time.time()
    if 'html' in data:
        for pageset in data['html']:
            tools.build_pageset(pageset, data['options'])
    print(f'Built all pages in {round(float(time.time() - t1), 4)} seconds')

    print('\n\n=== I M A G E S ===')
    if 'images' in data['options']:
        tools.handle_images(data['options'])

    print('\n\n=== A U D I O ===')
    if 'audio' in data['options']:
        tools.handle_audio(data['options'])

    print('\n\n=== C O P Y ===')
    if 'copy' in data:
        tools.copy_files(data['copy'])

    print('\n\n=== M I S C ===')
    # Symlink .htaccess for non-production (Local) if needed,
    # though AWS S3 doesn't use .htaccess.
    # The original build.py did this for local apache testing.
    if not data['options'].get('production', False):
        if 'htaccess' in data['options']:
            print('Creating symlink for .htaccess...', end='')
            try:
                subprocess.run(['ln', '-s',
                                os.path.join(os.getcwd(), data['options']['htaccess']),
                                data['options']['dist']], check=False)
                print(' Done!')
            except Exception as e:
                print(f' Failed: {e}')

    print('\n\n=== Entire build done in',
          f'{round(float(time.time() - t0), 4)} seconds ===')

def upload_file(filename, destname, extra_args, options, client):
    print(f'Copying {filename} to {options["s3_bucket"]}/{destname}...', end='')
    with open(filename, 'rb') as f:
        client.upload_fileobj(f,
                              options['s3_bucket'],
                              destname,
                              ExtraArgs=extra_args)
    print(' Done!')

def handle_upload_item(filename, destname, options, client):
    # Determine ContentType and CacheControl
    extra_args = {'CacheControl': f'max-age={options.get("cache_control_age", 3600)}'}

    if filename.endswith('.html'):
        extra_args['ContentType'] = 'text/html'
    elif filename.endswith('.css'):
        extra_args['ContentType'] = 'text/css'
    elif filename.endswith('.js'):
        extra_args['ContentType'] = 'text/javascript'
    elif filename.endswith('.svg'):
        extra_args['ContentType'] = 'image/svg+xml'
    elif filename.endswith('.jpg') or filename.endswith('jpeg'):
        extra_args['ContentType'] = 'image/jpeg'
    elif filename.endswith('.png'):
        extra_args['ContentType'] = 'image/png'
    elif filename.endswith('.gif'):
        extra_args['ContentType'] = 'image/gif'

    upload_file(filename, destname, extra_args, options, client)

def upload_to_s3(data):
    """Uploads the dist directory to S3."""
    options = data['options']
    dist_dir = options['dist']
    bucket = options['s3_bucket']

    print(f'\n#####\nUploading {dist_dir} to {bucket}...')
    s3_client = get_client('s3', options) # uses shared.client

    # Walk through dist directory
    for filename in glob.glob(f'{dist_dir}/**', recursive=True):
        if os.path.isdir(filename):
            continue
        if os.path.basename(filename).startswith('.'):
            continue

        # Calculate destination key
        destname = filename[len(dist_dir)+1:]

        # Strip .html extension for clean URLs on S3/CloudFront
        if destname.endswith('.html'):
            destname = destname[:-5]

        # Determine if we should handle this file (mimicking send_it.py logic logic roughly, but cleaner)
        # send_it.py had specific checks for html, js/, css/, images/.
        # We'll just upload everything in dist unless it's hidden.
        handle_upload_item(filename, destname, options, s3_client)

    print('Done!\n')

def invalidate_cloudfront(data, distribution_id):
    """Invalidates the CloudFront cache."""
    print(f"\nCreating invalidation for distribution {distribution_id}...", end="")
    cf_client = get_client("cloudfront", data['options'])
    response = cf_client.create_invalidation(
        DistributionId=distribution_id,
        InvalidationBatch={
            'Paths': {
                'Quantity': 1,
                'Items': ["/*"]
            },
            'CallerReference': str(time.time())
        }
    )
    print(" Done!")
    print("Waiting for invalidation to complete... ", end="")
    waiter = cf_client.get_waiter('invalidation_completed')
    waiter.wait(DistributionId=distribution_id, Id=response['Invalidation']['Id'])
    print("Done!")

# --- Core Deployment Logic Helpers ---

def perform_sam_deploy(env, stack_name, data):
    """Executes SAM build and deploy."""

    # Check stack status and offer cleanup
    check_stack_status(stack_name, data['options'])

    # Identify secrets dynamically from template.yaml (NoEcho: true)
    # Merge with any explicitly defined secrets in config
    inferred_secrets = parse_template_parameters()
    configured_secrets = data.get('secrets', [])

    # Combine lists, removing duplicates
    all_secrets = list(set(inferred_secrets + configured_secrets))

    # Verify secrets and get dynamic references
    secret_overrides = ensure_secrets(all_secrets, data['options'], env)

    click.echo(f"Building SAM application for {env}...")
    try:
        subprocess.check_call(['sam', 'build', '--use-container'])
    except subprocess.CalledProcessError:
        click.echo("SAM Build failed.")
        sys.exit(1)

    click.echo(f"Deploying SAM stack: {stack_name}...")
    deploy_cmd = [
        'sam', 'deploy',
        '--stack-name', stack_name,
        '--parameter-overrides', f'Environment={env}',
        '--resolve-s3', # Let SAM manage the deployment bucket
        '--capabilities', 'CAPABILITY_IAM'
    ]

    # Combine config parameters and secret overrides
    # secret overrides take precedence if conflict
    combined_overrides = {}
    if 'parameters' in data and data['parameters']:
        combined_overrides.update(data['parameters'])
    combined_overrides.update(secret_overrides)

    if combined_overrides:
        # Construct the overrides list
        overrides_list = []
        for key, value in combined_overrides.items():
            overrides_list.append(f"{key}={value}")

        # Debug output
        click.echo(f"Passing overrides: {overrides_list}")

        # Insert into command
        param_idx = deploy_cmd.index('--parameter-overrides')
        for item in overrides_list:
            deploy_cmd.insert(param_idx + 2, item)

    # Add region if specified in config, otherwise default to us-east-1
    region = data['options'].get('aws_region_name', 'us-east-1')
    deploy_cmd.extend(['--region', region])

    # Add profile if specified in config
    if 'aws_profile_name' in data['options']:
        deploy_cmd.extend(['--profile', data['options']['aws_profile_name']])

    try:
        subprocess.check_call(deploy_cmd)
    except subprocess.CalledProcessError:
        click.echo("SAM Deploy failed.")
        sys.exit(1)

def perform_site_deploy(env, config_file, stack_name):
    """Fetches outputs, builds site, uploads, invalidates, and tests."""
    data = load_config(config_file)
    region = data['options'].get('aws_region_name', 'us-east-1')

    click.echo("Retrieving Stack Outputs...")
    # Pass options so get_client uses the correct profile
    outputs = get_stack_outputs(stack_name, region, data['options'])

    bucket_name = outputs.get('WebsiteBucketName')
    api_url = outputs.get('ApiUrl')
    distribution_id = outputs.get('CloudFrontDistributionId')
    website_url = outputs.get('WebsiteURL')

    if not bucket_name:
        click.echo("Error: Could not find WebsiteBucketName in stack outputs.")
        sys.exit(1)

    click.echo(f"  Bucket: {bucket_name}")
    click.echo(f"  API URL: {api_url}")
    click.echo(f"  CloudFront ID: {distribution_id}")
    click.echo(f"  Website URL: {website_url}")

    # Update Configuration
    data['options']['s3_bucket'] = bucket_name
    data['options']['api_url'] = api_url
    data['options']['production'] = (env == 'prod')

    # Build and Upload
    build_site(data)
    upload_to_s3(data)

    # Invalidate CloudFront
    if distribution_id:
        invalidate_cloudfront(data, distribution_id)

    # Run API Tests
    if api_url:
        if 'api_endpoints' in data:
            updated_endpoints = []
            for endpoint in data['api_endpoints']:
                updated_endpoints.append(endpoint.replace('REPLACE_WITH_SAM_OUTPUT_API_URL', api_url))
            test_api_endpoints(updated_endpoints)
        else:
             click.echo("No api_endpoints defined in config, skipping tests.")

def get_env_details(env):
    if env == 'dev':
        return 'data-dev.yaml', 'dev'
    else:
        return 'data.yaml', 'prod'

# --- CLI Commands ---

@click.group()
def cli():
    """Management script for building and deploying the website."""
    pass

@cli.command()
@click.option('--config', default='data-dev.yaml', help='Configuration file to use.')
def build_local(config):
    """Builds the website for local development."""
    data = load_config(config)
    data['options']['production'] = False

    if 'api_url_local' in data['options']:
         data['options']['api_url'] = data['options']['api_url_local']

    build_site(data)

@cli.command()
@click.option('--env', type=click.Choice(['dev', 'prod']), prompt=True, help='Target environment.')
def deploy_infra(env):
    """Deploys ONLY the SAM infrastructure."""
    config_file, stack_name = get_env_details(env)

    if not os.path.exists(config_file) and not os.path.exists('data.yaml'):
         click.echo(f"Config file for {env} not found.")
         return

    # Load config to get profile
    data = load_config(config_file if os.path.exists(config_file) else 'data.yaml')
    perform_sam_deploy(env, stack_name, data)

@cli.command()
@click.option('--env', type=click.Choice(['dev', 'prod']), prompt=True, help='Target environment.')
def deploy_site(env):
    """Deploys ONLY the website code (Build -> Upload -> Invalidate)."""
    config_file, stack_name = get_env_details(env)

    if not os.path.exists(config_file):
        if os.path.exists('data.yaml'):
            config_file = 'data.yaml'
        else:
            click.echo(f"Config file for {env} not found.")
            return

    perform_site_deploy(env, config_file, stack_name)

@cli.command()
@click.option('--env', type=click.Choice(['dev', 'prod']), prompt=True, help='Target environment.')
def deploy_all(env):
    """Interactive wizard to deploy infrastructure and/or website."""

    config_file, stack_name = get_env_details(env)

    if not os.path.exists(config_file):
        if os.path.exists('data.yaml'):
            config_file = 'data.yaml'
        else:
            click.echo(f"Config file for {env} not found.")
            return

    # Load config to get profile for SAM deploy
    data = load_config(config_file)

    # 1. SAM Deploy
    if click.confirm('Deploy Infrastructure (SAM)?', default=True):
        perform_sam_deploy(env, stack_name, data)

    # 2. Site Deploy (Build/Upload/Invalidate/Test)
    if click.confirm('Build and Upload Site?', default=True):
         perform_site_deploy(env, config_file, stack_name)

# Alias for backward compatibility / ease of use
cli.add_command(deploy_all, name='deploy')

if __name__ == '__main__':
    cli()
