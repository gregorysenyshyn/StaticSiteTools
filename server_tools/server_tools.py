import os
import glob
import json
import argparse
import datetime

import boto3
from botocore.exceptions import ClientError

import shared.clients.get_client as get_client


def handle_page(filename, destname, options, client=None):
    if client is None:
        client = get_client(options, 's3')
    extra_args = {'CacheControl': f'max-age={options["cache_control_age"]}',
                  'ContentType': 'text/html'}
    upload_file(filename, destname, extra_args, options, client)


def handle_css(filename, destname, options, client=None):
    if client is None:
        client = get_client(options, 's3')
    extra_args = {'CacheControl': f'max-age={options["cache_control_age"]}',
                  'ContentType': 'text/css'}
    upload_file(filename, destname, extra_args, options, client)


def handle_js(filename, destname, options, client=None):
    if client is None:
        client = get_client(options, 's3')
    extra_args = {'CacheControl': f'max-age={options["cache_control_age"]}',
                  'ContentType': 'text/javascript'}
    upload_file(filename, destname, extra_args, options, client)


def handle_image(filename, destname, options, client=None):
    if client is None:
        client = get_client(options, 's3')
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


def upload_file(filename, destname, extra_args, options, client=None):
    client = get_client(options, 's3')
    print(f'Copying {filename} to {options["s3_bucket"]}/{destname}...',
          end='')
    with open(filename, 'rb') as f:
        client.upload_fileobj(f,
                              options['s3_bucket'],
                              destname,
                              ExtraArgs=extra_args)
    print(' Done!')


def clean(options, images=False, client=None):
    if client is None:
        client = (options, 's3')
    response = client.list_objects(Bucket=options['s3_bucket'])
    if 'Contents' in response:
        for item in response['Contents']:
            if not item['Key'].startswith(options['images']) or images:
                print(f'removing {item["Key"]}... ', end='')
                client.delete_object(Bucket=options['s3_bucket'],
                                     Key=item['Key'])
                print(' Done!')
