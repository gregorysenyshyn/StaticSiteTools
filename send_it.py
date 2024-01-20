import boto3
from botocore.exceptions import ClientError

import os
import glob
import json
import time
import argparse


from shared import utils
from shared.client import get_client


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

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='YAML data file')
    args = parser.parse_args()
    data = utils.load_yaml(args.data)

    check = input('Create new production build? (Y/n) ')
    if not check == 'n':
        data['options']['production'] = True
        import build
        build.build(data)

    answer = input('Ready to send? (Y/n) ')
    if not answer == 'n':
        print((f'#####\nUploading {data["options"]["dist"]}'),
              (f'to {data["options"]["s3_bucket"]}...'))
        s3_client = get_client('s3', data['options'])
        send_it(data['options'], s3_client)
        print('Done!\n')

    answer = input("\nCreate CDN invalidation? (Y/n)")
    if not answer == 'n':
        cf_client = get_client("cloudfront", data['options'])
        distribution_id = None
        print("\nGetting distribution ID...")
        response = cf_client.list_distributions()
        for item in response['DistributionList']['Items']:
            if data['options']['s3_bucket'] in item['Aliases']['Items']:
                distribution_id = item['Id']
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


    answer = input('\nCheck website settings? (Y/n) ')
    if not answer == 'n':
        from website.setup import check
        check(data['options'])

