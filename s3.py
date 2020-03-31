import os
import glob
import json
import argparse
import datetime

import boto3
from botocore.exceptions import ClientError


CACHE_CONTROL_AGE = '604800'  # 1 week
PROFILE_NAME = 'mffw'


def handle_page(filename, destname):
    client = get_client('s3')
    extra_args = {'CacheControl': f'max-age={CACHE_CONTROL_AGE}',
                  'ContentType': 'text/html'}
    upload_file(filename, client, DATA['options']['bucket'],
                destname, extra_args)


def handle_css(filename, destname):
    client = get_client('s3')
    extra_args = {'CacheControl': f'max-age={CACHE_CONTROL_AGE}',
                  'ContentType': 'text/css'}
    upload_file(filename, client, DATA['options']['bucket'],
                destname, extra_args)


def handle_js(filename, destname):
    client = get_client('s3')
    extra_args = {'CacheControl': f'max-age={CACHE_CONTROL_AGE}',
                  'ContentType': 'text/javascript'}
    upload_file(filename, client, DATA['options']['bucket'],
                destname, extra_args)


def handle_image(filename, destname):
    client = get_client('s3')
    extra_args = {'CacheControl': f'max-age={CACHE_CONTROL_AGE}'}
    if filename.endswith('.svg'):
        extra_args['ContentType'] = 'image/svg+xml'
    elif filename.endswith('.jpg') or filename.endswith('jpeg'):
        extra_args['ContentType'] = 'image/jpeg'
    elif filename.endswith('.png'):
        extra_args['ContentType'] = 'image/png'
    elif filename.endswith('.gif'):
        extra_args['ContentType'] = 'image/gif'
    upload_file(filename, client, DATA['options']['bucket'],
                destname, extra_args)


def get_cloudfront_config(client, endpoint):
    client = get_client('cloudfront')
    response = client.create_distribution(
        DistributionConfig={
            'CallerReference': datetime.now(),
            # 'Aliases': {
            #     'Quantity': 0,
            #     'Items': [
            #         # 'string',
            #     ]
            # },
            'DefaultRootObject': 'index',
            'Origins': {
                'Quantity': 1,
                'Items': [
                    {
                        'Id': '0',
                        'DomainName': endpoint,
                        # 'CustomHeaders': {
                        #     'Quantity': 123,
                        #     'Items': [
                        #         {
                        #             'HeaderName': 'string',
                        #             'HeaderValue': 'string'
                        #         },
                        #     ]
                        # },
                        # 'S3OriginConfig': {
                        #     'OriginAccessIdentity': 'string'
                        # },
                        # 'CustomOriginConfig': {
                        #     'HTTPPort': 123,
                        #     'HTTPSPort': 123,
                        #     'OriginProtocolPolicy': 'http-only'|'match-viewer'|'https-only',  # noqa
                        #     'OriginSslProtocols': {
                        #         'Quantity': 123,
                        #         'Items': [
                        #             'SSLv3'|'TLSv1'|'TLSv1.1'|'TLSv1.2',
                        #         ]
                        #     },
                        #     'OriginReadTimeout': 123,
                        #     'OriginKeepaliveTimeout': 123
                        # }
                    },
                ]
            },
            'DefaultCacheBehavior': {
                'TargetOriginId': 'string',
                'ForwardedValues': {
                    'QueryString': True|False,
                    'Cookies': {
                        'Forward': 'none'|'whitelist'|'all',
                        'WhitelistedNames': {
                            'Quantity': 123,
                            'Items': [
                                'string',
                            ]
                        }
                    },
                    'Headers': {
                        'Quantity': 123,
                        'Items': [
                            'string',
                        ]
                    },
                    'QueryStringCacheKeys': {
                        'Quantity': 123,
                        'Items': [
                            'string',
                        ]
                    }
                },
                'TrustedSigners': {
                    'Enabled': True|False,
                    'Quantity': 123,
                    'Items': [
                        'string',
                    ]
                },
                'ViewerProtocolPolicy': 'allow-all'|'https-only'|'redirect-to-https',
                'MinTTL': 123,
                'AllowedMethods': {
                    'Quantity': 123,
                    'Items': [
                        'GET'|'HEAD'|'POST'|'PUT'|'PATCH'|'OPTIONS'|'DELETE',
                    ],
                    'CachedMethods': {
                        'Quantity': 123,
                        'Items': [
                            'GET'|'HEAD'|'POST'|'PUT'|'PATCH'|'OPTIONS'|'DELETE',
                        ]
                    }
                },
                'SmoothStreaming': True|False,
                'DefaultTTL': 123,
                'MaxTTL': 123,
                'Compress': True|False,
                'LambdaFunctionAssociations': {
                    'Quantity': 123,
                    'Items': [
                        {
                            'LambdaFunctionARN': 'string',
                            'EventType': 'viewer-request'|'viewer-response'|'origin-request'|'origin-response',
                            'IncludeBody': True|False
                        },
                    ]
                },
                'FieldLevelEncryptionId': 'string'
            },
            'CacheBehaviors': {
                'Quantity': 123,
                'Items': [
                    {
                        'PathPattern': 'string',
                        'TargetOriginId': 'string',
                        'ForwardedValues': {
                            'QueryString': True|False,
                            'Cookies': {
                                'Forward': 'none'|'whitelist'|'all',
                                'WhitelistedNames': {
                                    'Quantity': 123,
                                    'Items': [
                                        'string',
                                    ]
                                }
                            },
                            'Headers': {
                                'Quantity': 123,
                                'Items': [
                                    'string',
                                ]
                            },
                            'QueryStringCacheKeys': {
                                'Quantity': 123,
                                'Items': [
                                    'string',
                                ]
                            }
                        },
                        'TrustedSigners': {
                            'Enabled': True|False,
                            'Quantity': 123,
                            'Items': [
                                'string',
                            ]
                        },
                        'ViewerProtocolPolicy': 'allow-all'|'https-only'|'redirect-to-https',
                        'MinTTL': 123,
                        'AllowedMethods': {
                            'Quantity': 123,
                            'Items': [
                                'GET'|'HEAD'|'POST'|'PUT'|'PATCH'|'OPTIONS'|'DELETE',
                            ],
                            'CachedMethods': {
                                'Quantity': 123,
                                'Items': [
                                    'GET'|'HEAD'|'POST'|'PUT'|'PATCH'|'OPTIONS'|'DELETE',
                                ]
                            }
                        },
                        'SmoothStreaming': True|False,
                        'DefaultTTL': 123,
                        'MaxTTL': 123,
                        'Compress': True|False,
                        'LambdaFunctionAssociations': {
                            'Quantity': 123,
                            'Items': [
                                {
                                    'LambdaFunctionARN': 'string',
                                    'EventType': 'viewer-request'|'viewer-response'|'origin-request'|'origin-response',
                                    'IncludeBody': True|False
                                },
                            ]
                        },
                        'FieldLevelEncryptionId': 'string'
                    },
                ]
            },
            'CustomErrorResponses': {
                'Quantity': 123,
                'Items': [
                    {
                        'ErrorCode': 123,
                        'ResponsePagePath': 'string',
                        'ResponseCode': 'string',
                        'ErrorCachingMinTTL': 123
                    },
                ]
            },
            'Comment': 'string',
            'Logging': {
                'Enabled': True|False,
                'IncludeCookies': True|False,
                'Bucket': 'string',
                'Prefix': 'string'
            },
            'PriceClass': 'PriceClass_100'|'PriceClass_200'|'PriceClass_All',
            'Enabled': True|False,
            'ViewerCertificate': {
                'CloudFrontDefaultCertificate': True|False,
                'IAMCertificateId': 'string',
                'ACMCertificateArn': 'string',
                'SSLSupportMethod': 'sni-only'|'vip',
                'MinimumProtocolVersion': 'SSLv3'|'TLSv1'|'TLSv1_2016'|'TLSv1.1_2016'|'TLSv1.2_2018',
                'Certificate': 'string',
                'CertificateSource': 'cloudfront'|'iam'|'acm'
            },
            'Restrictions': {
                'GeoRestriction': {
                    'RestrictionType': 'blacklist'|'whitelist'|'none',
                    'Quantity': 123,
                    'Items': [
                        'string',
                    ]
                }
            },
            'WebACLId': 'string',
            'HttpVersion': 'http1.1'|'http2',
            'IsIPV6Enabled': True|False
        }
    )


def create_cdn_distribution():
    client = get_client('s3')
    response = client.get_bucket_location(Bucket=DATA['options']['bucket'])
    zone = response['LocationConstraint']
    endpoint = f'{DATA["options"]["bucket"]}.s3-website.{zone}.amazonaws.com'
    print(endpoint)


def get_cdn_distribution():
    client = get_client('cloudfront')
    response = client.list_distributions()
    if response['DistributionList']['Quantity'] == 0:
        print('No distributions found! Create one? (y/n) ', end='')
        create = input()
        if create == 'y':
            create_cdn_distribution()
        else:
            print('No distribution for website')


def get_bucket_policy():
    bucket_policy = {
        'Version': '2012-10-17',
        'Statement': [{
            'Sid': 'AddPerm',
            'Effect': 'Allow',
            'Principal': '*',
            'Action': ['s3:GetObject'],
            f'Resource': f'arn:aws:s3:::{DATA["options"]["bucket"]}/*'
        }]
    }
    return json.dumps(bucket_policy)


def check_bucket_policy():
    client = get_client('s3')
    print('\nChecking Bucket Policy')
    response = client.get_bucket_policy_status(
                Bucket=DATA['options']['bucket'])
    if response['PolicyStatus']['IsPublic']:
        print(f'{DATA["options"]["bucket"]} is public')
    else:
        print(f'{DATA["options"]["bucket"]} is NOT public')
        response = client.get_bucket_policy(
                  Bucket=DATA['options']['bucket'])
        print(f'Policy:\n{response["Policy"]}')
        new_policy = input('Reset bucket policy? (y/n) ', end='')
        if new_policy == 'y':
            client.put_bucket_policy(Bucket=DATA['options']['bucket'],
                                     Policy=get_bucket_policy())


def set_up_website(index_name='index', error_name='error'):
    client = get_client('s3')
    print('Setting up website... ', end='')
    client.put_bucket_website(
        Bucket=DATA['options']['bucket'],
        WebsiteConfiguration={
            'IndexDocument': {'Suffix': index_name},
            'ErrorDocument': {'Key': error_name}
        })
    print(f'Done!\nIndex set to {index_name}\nError set to {error_name}')


def check_index_and_error_pages(response):
    dist_files = os.listdir(DATA['options']['dist'])

    index_document = response["IndexDocument"]["Suffix"]
    print(f'Index Document: {index_document}: ', end='')
    if f'{index_document}.html' in dist_files:
        print('Exists!')
    else:
        print("Doesn't Exist!")

    error_document = response["ErrorDocument"]["Key"]
    print(f'Error Document: {error_document}: ', end='')
    if f'{error_document}.html' in dist_files:
        print('Exists!')
    else:
        print("Doesn't Exist!")


def confirm_website_settings():
    client = get_client('s3')
    bucket = DATA['options']['bucket']
    try:
        response = client.get_bucket_website(Bucket=bucket)
    except ClientError:
        print('ERROR: no website config\nSet up website? (y/n)', end='')
        answer = input()
        if answer == 'y':
            set_up_website(client, bucket)
    else:
        check_index_and_error_pages(response)


def upload_file(filename, destname, extra_args):
    client = get_client('s3')
    print(f'Copying {filename} to {DATA["options"]["bucket"]}/{destname}...',
          end='')
    with open(filename, 'rb') as f:
        client.upload_fileobj(f,
                              DATA['options']['bucket'],
                              destname,
                              ExtraArgs=extra_args)
    print(' Done!')


def send_it(options):
    client = get_client('s3')
    for filename in glob.glob(f'{options["dist"]}/**', recursive=True):
        if not filename.startswith('.'):
            if not os.path.isdir(filename):
                destname = filename[len(options['dist'])+1:]
                if destname.endswith('.html'):
                    destname = destname[:-5]
                    handle_page(filename, client, destname, options['bucket'])
                elif destname.startswith('js/'):
                    handle_js(filename, client, destname, options['bucket'])
                elif destname.startswith('css/'):
                    handle_css(filename, client, destname, options['bucket'])
                elif destname.startswith('images/'):
                    handle_image(filename, client, destname, options['bucket'])
        else:
            print(f'ERROR - Not uploading hidden file {filename}')


def clean():
    client = get_client('s3')
    response = client.list_objects(Bucket=DATA['options']['bucket'])
    if 'Contents' in response:
        for item in response['Contents']:
            print(f'removing {item["Key"]}... ', end='')
            client.delete_object(Bucket=DATA['options']['bucket'],
                                 Key=item['Key'])
            print(' Done!')


def get_client(client_type):
    session = boto3.Session(profile_name=PROFILE_NAME)
    client = session.client(client_type)
    return client


if __name__ == '__main__':

    import tools

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='YAML data file', required=True)
    parser.add_argument('--clean',
                        help=('Clean AWS Bucket (including images)'
                              ' before uploading'),
                        action='store_true')
    args = parser.parse_args()
    DATA = tools.load_yaml(args.data)

    # print('\n#####\nWebsite Settings:')
    # confirm_website_settings(CLIENT, DATA['options']['bucket'])
    # check_bucket_policy(CLIENT)
    # print('\n#####')

    get_cdn_distribution()

    # if args.clean:
    #     print(f'#####\nCleaning {DATA["options"]["bucket"]}...', end='')
    #     clean(DATA['options']['bucket'], CLIENT)
    #     print('Done!')

    # print((f'Uploading {DATA["options"]["dist"]}'),
    #       (f'to {DATA["options"]["bucket"]}...'))
    # send_it(DATA['options'])
