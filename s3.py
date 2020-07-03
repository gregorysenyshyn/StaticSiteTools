import os
import glob
import json
import argparse
import datetime

import boto3
from botocore.exceptions import ClientError


def handle_page(filename, destname, options, client=None):
    if client == None:
        client = get_client(options, 's3')
    extra_args = {'CacheControl': f'max-age={options["cache_control_age"]}',
                  'ContentType': 'text/html'}
    upload_file(filename, destname, extra_args, options, client)


def handle_css(filename, destname, options, client=None):
    if client == None:
        client = get_client(options, 's3')
    extra_args = {'CacheControl': f'max-age={options["cache_control_age"]}',
                  'ContentType': 'text/css'}
    upload_file(filename, destname, extra_args, options, client)


def handle_js(filename, destname, options, client=None):
    if client == None:
        client = get_client(options, 's3')
    extra_args = {'CacheControl': f'max-age={options["cache_control_age"]}',
                  'ContentType': 'text/javascript'}
    upload_file(filename, destname, extra_args, options, client)


def handle_image(filename, destname, options, client=None):
    if client == None:
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


def get_cloudfront_config(client, endpoint):
    client = get_client(options, 'cloudfront')
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


def create_cdn_distribution(options):
    client = get_client(options, 's3')
    response = client.get_bucket_location(Bucket=options['s3_bucket'])
    zone = response['LocationConstraint']
    endpoint = f'{options["s3_bucket"]}.s3-website.{zone}.amazonaws.com'
    print(endpoint)


def get_cdn_distribution():
    client = get_client(options, 'cloudfront')
    response = client.list_distributions()
    if response['DistributionList']['Quantity'] == 0:
        print('No distributions found! Create one? (y/n) ', end='')
        create = input()
        if create == 'y':
            create_cdn_distribution()
        else:
            print('No distribution for website')


def get_bucket_policy(options):
    bucket_policy = {
        'Version': '2012-10-17',
        'Statement': [{
            'Sid': 'AddPerm',
            'Effect': 'Allow',
            'Principal': '*',
            'Action': ['s3:GetObject'],
            f'Resource': f'arn:aws:s3:::{options["s3_bucket"]}/*'
        }]
    }
    return json.dumps(bucket_policy)


def check_bucket_policy(options, client=None):
    if client == None:
        client = get_client(options, 's3')
    print('\nChecking Bucket Policy')
    response = client.get_bucket_policy_status(
                Bucket=DATA['options']['s3_bucket'])
    if response['PolicyStatus']['IsPublic']:
        print(f'{DATA["options"]["s3_bucket"]} is public')
    else:
        print(f'{DATA["options"]["s3_bucket"]} is NOT public')
        response = client.get_bucket_policy(
                  Bucket=DATA['options']['s3_bucket'])
        print(f'Policy:\n{response["Policy"]}')
        new_policy = input('Reset bucket policy? (y/n) ', end='')
        if new_policy == 'y':
            client.put_bucket_policy(Bucket=DATA['options']['s3_bucket'],
                                     Policy=get_bucket_policy())


def set_up_website(index_name='index', error_name='error'):
    client = get_client(options, 's3')
    print('Setting up website... ', end='')
    client.put_bucket_website(
        Bucket=DATA['options']['s3_bucket'],
        WebsiteConfiguration={
            'IndexDocument': {'Suffix': index_name},
            'ErrorDocument': {'Key': error_name}
        })
    print(f'Done!\nIndex set to {index_name}\nError set to {error_name}')


def check_index_and_error_pages(response, options):
    dist_files = os.listdir(options['dist'])

    index_document = response["IndexDocument"]["Suffix"]
    print(f'Index Document "{index_document}": ', end='')
    if f'{index_document}.html' in dist_files:
        print('Exists!')
    else:
        print("Doesn't Exist!")

    try:
        error_document = response["ErrorDocument"]["Key"]
        print(f'Error Document "{error_document}": ', end='')
        if f'{error_document}.html' in dist_files:
            print('Exists!')
        else:
            print("Doesn't Exist!")
    except KeyError as e:
        print(repr(e))


def confirm_website_settings(options, client=None):
    if client == None:
        client = get_client(options, 's3')
    bucket = options['s3_bucket']
    try:
        response = client.get_bucket_website(Bucket=bucket)
    except ClientError:
        print('ERROR: no website config\nSet up website? (y/n)', end='')
        answer = input()
        if answer == 'y':
            set_up_website(client, bucket)
    else:
        check_index_and_error_pages(response, options)


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


def send_it(options, client=None):
    if client == None:
        client = get_client(options, 's3')
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
                #subprocess.run(['aws', 's3', 'sync',
                #    ##TODO os.path.join?
                #               options['dist'],
                #               f's3://{options["s3_bucket"]}',
                #               '--delete'])
        else:
            print(f'ERROR - Not uploading hidden file {filename}')


def clean(options, images=False, client=None):
    if client == None:
        client = get_client(options, 's3')
    response = client.list_objects(Bucket=options['s3_bucket'])
    if 'Contents' in response:
        for item in response['Contents']:
            if not item['Key'].startswith(options['images']) or images == True:
                print(f'removing {item["Key"]}... ', end='')
                client.delete_object(Bucket=options['s3_bucket'],
                                     Key=item['Key'])
                print(' Done!')


def get_client(options, client_type):
    session = boto3.Session(profile_name=options['aws_profile_name'])
    client = session.client(client_type)
    return client


if __name__ == '__main__':

    import tools

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='YAML data file', required=True)
    parser.add_argument('--clean',
                        help=('Clean AWS Bucket (excluding images)'
                              ' before uploading'),
                        action='store_true')
    args = parser.parse_args()
    data = tools.load_yaml(args.data)

    s3_client = get_client(data['options'], 's3')

    if args.clean:
        print(f'\n\n#####\nCleaning s3://{data["options"]["s3_bucket"]}...')
        clean(data['options'], client=s3_client)
        print('All Clean!\n\n')

    print((f'#####\nUploading {data["options"]["dist"]}'),
          (f'to {data["options"]["s3_bucket"]}...'))
    send_it(data['options'])

    print('\n#####\nWebsite Settings:')
    confirm_website_settings(data['options'], s3_client)
    check_bucket_policy(options, s3_client)
    print('\n#####')
    # get_cdn_distribution()
