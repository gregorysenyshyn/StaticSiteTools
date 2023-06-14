import os 
import json
import argparse
import datetime

import sys
sys.path.append(sys.path[0] + '/..')
from shared import utils
from shared.client import get_client

from botocore.exceptions import ClientError

# S3 Settings

def check_buckets(bucket_name, s3_client):
    response = s3_client.list_buckets()
    bucket_list = []
    for item in response["Buckets"]:
        bucket_list.append(item["Name"])
    bucket_names = [bucket_name, f"www.{bucket_name}"]
    for bucket_name in bucket_names:
        if bucket_name not in bucket_list:
            ans = input(f"No bucket named {bucket_name} exists! Create it? (y/n) ")
            if ans == 'y':
                s3_client.create_bucket(Bucket=bucket_name)
        check_bucket_policy(bucket_name, s3_client)


def check_bucket_policy(bucket_name, s3_client):
    print(f'\nChecking {bucket_name} Bucket Policy')
    try:
        response = s3_client.get_bucket_policy_status(Bucket=bucket_name)
        if response['PolicyStatus']['IsPublic']:
            print(f'{bucket_name} is public')
        else:
            print(f'{bucket_name} is NOT public')
            response = s3_client.get_bucket_policy(Bucket=bucket_name)
            print(f'Policy:\n{response["Policy"]}')
            new_policy = input('Reset bucket policy? (Y/n) ')
            if not new_policy == 'n':
                reset_bucket_policy(bucket_name, s3_client)
    except ClientError as e:
        print(e)
        new_policy = input('Reset bucket policy? (Y/n) ')
        if not new_policy == 'n':
            reset_bucket_policy(bucket_name, s3_client)


def reset_bucket_policy(bucket_name, s3_client):
    bucket_policy = {
        'Version': '2012-10-17',
        'Statement': [{
            'Sid': 'AddPerm',
            'Effect': 'Allow',
            'Principal': '*',
            'Action': ['s3:GetObject'],
            f'Resource': f'arn:aws:s3:::{bucket_name}/*'
        }]
    }
 
    s3_client.put_bucket_policy(Bucket=bucket_name,
                             Policy=json.dumps(bucket_policy))


def confirm_website_settings(options, s3_client):
    print("\nChecking domain details...")
    domain_details = get_domain_details(options)
    zone_id = get_hosted_zone_id(options)
    zone_details = get_hosted_zone_details(zone_id, options)
    zone_nameservers = zone_details['DelegationSet']['NameServers']
    for nameserver in domain_details['Nameservers']:
        if nameserver['Name'] in zone_nameservers:
            print(f'Nameserver {nameserver["Name"]} linked properly')
        else:
            #TO DO - Create record if not found
            raise Exception('ERROR! Nameserver '
                            f'{nameserver["name"]} not linked')
    bucket = options['s3_bucket']
    try:
        response = s3_client.get_bucket_website(Bucket=bucket)
        check_index_and_error_pages(response, options)
    except ClientError:
        print(f'\nERROR: no website config for {bucket}\nSet up website? (Y/n) ',
                end='')
        answer = input()
        if not answer == 'n':
            index_name = input('Index page name? (index): ')
            if index_name == '':
                index_name = 'index'
            error_name = input('Error page name? (error): ')
            if error_name == '':
                error_name = 'error'
            set_up_website(options, s3_client,
                           index_name=index_name, error_name=error_name)
    bucket = f'www.{options["s3_bucket"]}'
    try:
        response = s3_client.get_bucket_website(Bucket=bucket)
        print(f'{bucket} currently redirecting all requests to',
              f'{response["RedirectAllRequestsTo"]["HostName"]} over',
              f'{response["RedirectAllRequestsTo"]["Protocol"]}')
    except:
        print(f'\nERROR: no website config for {bucket}\nSet up redirect? (Y/n) ',
              end='')
        answer = input()
        if not answer == 'n':
            print('\nSetting up website redirect... ')
            s3_client.put_bucket_website(
                Bucket=bucket,
                WebsiteConfiguration={
                    'RedirectAllRequestsTo': {
                        'HostName': options['s3_bucket'],
                        'Protocol': 'https'
                        }})
            response = s3_client.get_bucket_website(Bucket=bucket)
            print(f'{bucket} will now redirect all requests to ',
                  f'{response["RedirectAllRequestsTo"]["HostName"]} over ',
                  f'{response["RedirectAllRequestsTo"]["Protocol"]}')


def check_index_and_error_pages(response, options, index_name='index',
                                error_name='error'):
    dist_files = os.listdir(options['dist'])

    index_document = ''
    if response['IndexDocument']['Suffix'] == index_name:
        index_document = response['IndexDocument']['Suffix']
        print(f'\nIndex Document "{index_document}": ', end='')
        find_in_dist(index_document, dist_files)
    error_document = ''
    if 'ErrorDocument' in response and response['ErrorDocument']['Key'] == error_name:
        error_document = response['ErrorDocument']['Key']
        print(f'Error Document "{error_document}": ', end='')
        find_in_dist(error_document, dist_files)

def find_in_dist(key, dist_files):
        if f'{key}.html' in dist_files:
            print('Exists!')
        else:
            print("Doesn't Exist!")


def set_up_website(options, s3_client, index_name='index', error_name='error'):
    print('\nSetting up website... ')
    s3_client.put_bucket_website(
        Bucket=options['s3_bucket'],
        WebsiteConfiguration={
            'IndexDocument': {'Suffix': index_name},
            'ErrorDocument': {'Key': error_name}
        })
    response = s3_client.get_bucket_website(Bucket=options['s3_bucket'])
    check_index_and_error_pages(response, options, index_name, error_name)


# Route53 Settings

def get_domain_details(options):
    domain_client = get_client('route53domains', options)
    return domain_client.get_domain_detail(DomainName=options['s3_bucket'])


def get_hosted_zone_id(options):
    r53_client = get_client('route53', options)
    zones = r53_client.list_hosted_zones()
    for zone in zones['HostedZones']:
        if str(zone['Name']).startswith(options['s3_bucket']):
            return zone['Id'].split('/')[-1]


def get_hosted_zone_details(zone_id, options):
    r53_client = get_client('route53', options)
    return r53_client.get_hosted_zone(Id=zone_id)


def create_cname_record(options, validation, zone):
    r53_client = get_client('route53', options)
    response = r53_client.change_resource_record_sets(
            HostedZoneId=zone,
            ChangeBatch={'Comment': 'SST',
                'Changes': [{
                 'Action': 'UPSERT',
                 'ResourceRecordSet': {
                    'Name': validation['ResourceRecord']['Name'],
                    'Type': 'CNAME',
                    'TTL': 15,
                    'ResourceRecords': [{'Value': (validation['ResourceRecord']
                                         ['Value'])}]}}]})
    waiter = r53_client.get_waiter('resource_record_sets_changed')
    waiter.wait(Id=response['ChangeInfo']['Id'])
    check_dns(options, validation)


def get_record_sets(zone_id, options):
    r53_client = get_client('route53', options)
    return r53_client.list_resource_record_sets(HostedZoneId=zone_id)


def create_a_record(zone_id, record_name, options, dns_name):
    r53_client = get_client('route53', options)
    if record_name.startswith('www'):
        response = r53_client.change_resource_record_sets(
                      HostedZoneId=zone_id,
                      ChangeBatch={
                          'Changes': [{
                              'Action': 'CREATE',
                              'ResourceRecordSet': {
                                  'Name': record_name,
                                  'Type': 'A',
                                  'AliasTarget': {
                                      'HostedZoneId': 'Z3AQBSTGFYJSTF',
                                      'EvaluateTargetHealth': False,
                                      'DNSName': dns_name
                                  }
                              }
                          }]
                      }
                   )
    else:
        response = r53_client.change_resource_record_sets(
                      HostedZoneId=zone_id,
                      ChangeBatch={
                          'Changes': [{
                              'Action': 'CREATE',
                              'ResourceRecordSet': {
                                  'Name': record_name,
                                  'Type': 'A',
                                  'AliasTarget': {
                                      'HostedZoneId': 'Z2FDTNDATAQYW2',
                                      'EvaluateTargetHealth': False,
                                      'DNSName': dns_name
                                  }
                              }
                          }]
                      }
                   )
    return response['ChangeInfo']['Status']


# CloudFront Settings


def check_cdn_distribution(options):
    cf_client = get_client('cloudfront', options)
    distribution_arn = ''
    response = cf_client.list_distributions()
    if response['DistributionList']['Quantity'] == 0:
        create = input('No distributions found! Create one? (Y/n) ')
        if not create == 'n':
            distribution_arn = create_cdn_distribution(options)
        else:
            raise SystemExit('No distributions!')
    else:
        aliases = ""
        for item in response['DistributionList']['Items']:
            for alias in item['Aliases']['Items']:
                if (alias == options['s3_bucket'] or
                    alias == f"www.{options['s3_bucket']}"):
                    aliases += f'{alias} '
                    distribution_arn = response['DistributionList']['Items'][0]['ARN']

        if aliases:
            print(f'CDN distribution exists for {aliases}')
        else:
            create = input(f"No distributions found for {options['s3_bucket']}! "
                           'Create one? (Y/n) ')
            if not create == 'n':
                distribution_arn = create_cdn_distribution(options)
            else:
                raise SystemExit('No distributions!')
    if not distribution_arn:
        raise SystemExit('No distributions!')
    return distribution_arn


def create_cdn_distribution(options):
    s3_client = get_client('s3', options)
    response = s3_client.get_bucket_location(Bucket=options['s3_bucket'])
    zone = response['LocationConstraint']
    if not zone:
        zone = options["aws_region_name"]
    endpoint = f'{options["s3_bucket"]}.s3.{zone}.amazonaws.com'

    cf_client = get_client('cloudfront', options)
    oai = get_oai(cf_client, options)
    print("\nChecking SSL Certificate...")
    cert_arn = get_acm_certificate(options)
    check_certificate_records(cert_arn, options)
    check_certificate_validation(options, cert_arn)
    cf_config = get_cloudfront_config(options, endpoint, oai, cert_arn)
    try:
        print("\nCreating CDN Distribution...")
        response = cf_client.create_distribution(DistributionConfig=cf_config)
        return response['Distribution']['ARN']
    except Exception as e:
        print(e)


def get_cloudfront_config(options, endpoint, oai,
                          cert_arn, index_name='index'):
    return {'CallerReference': str(datetime.datetime.now()),
            'Aliases': {
                'Quantity': 2,
                'Items': [
                    options['s3_bucket'],
                    f"www.{options['s3_bucket']}",
                ]
            },
            "Origins": {
                "Quantity": 1,
                "Items": [
                    {"DomainName": endpoint,
                     'Id': f'S3-{options["s3_bucket"]}',
                     "S3OriginConfig": {
                         "OriginAccessIdentity": ("origin-access-identity/"
                                                  f"cloudfront/{oai['Id']}")}}
                ]},
            "Comment": 'Autogenerated',
            "Enabled": True,
            "DefaultRootObject": index_name,
            "DefaultCacheBehavior": {
                "TargetOriginId":  f'S3-{options["s3_bucket"]}',
                'TrustedSigners': {'Enabled': False, 'Quantity': 0},
                'ViewerProtocolPolicy': 'redirect-to-https',
                'MinTTL': 300,
                'AllowedMethods': {
                    'Quantity': 3,
                    'Items': ['GET', 'HEAD', 'OPTIONS']},
                "ForwardedValues": {
                    "QueryString": False,
                    "Cookies": {"Forward": "none"}
                    },
                },
            "PriceClass": "PriceClass_All",
            "ViewerCertificate": {"CloudFrontDefaultCertificate": False,
                                  "ACMCertificateArn": cert_arn,
                                  "SSLSupportMethod": "sni-only"}
            }


def create_oai(cf_client, options):
    oai = cf_client.create_cloud_front_origin_access_identity(
            CloudFrontOriginAccessIdentityConfig={
                'CallerReference': str(datetime.datetime.now()),
                'Comment': options['s3_bucket']})
    return oai


def get_oai(cf_client, options):
    oai = None
    oai_list = cf_client.list_cloud_front_origin_access_identities()
    if not oai_list['CloudFrontOriginAccessIdentityList']['IsTruncated']:
        if 'Items' in oai_list['CloudFrontOriginAccessIdentityList']:
            for item in oai_list['CloudFrontOriginAccessIdentityList']['Items']:
                if item['Comment'] == options['s3_bucket']:
                    oai = item
                else:
                    oai = create_oai(cf_client, options)
        else:
            oai_answer = input('No OAI found.  Create one? (Y/n) ')
            if not oai_answer == 'n':
                oai = create_oai(cf_client, options)
            else:
                raise SystemExit('No Origin Access Identities!'
                                 ' Can\'t set up distribution')
    else:
        raise SystemExit('OAI Results Truncated!'
                         ' Implement more functionality to proceed!')
    return oai


# ACM Settings

def get_acm_certificate(options):

    cert_arn = ''
    client = get_client('acm', options)
    cert_list = client.list_certificates()
    if len(cert_list['CertificateSummaryList']) > 0:
        for item in cert_list['CertificateSummaryList']:
            if str(item['DomainName']).endswith(options['s3_bucket']):
                cert_arn = item['CertificateArn']
    else:
        ans = input('No SSL certificate found! Create one? (y/n) ')
        if ans == 'y':
            cert_arn = request_acm_certificate(options)

    return cert_arn


def request_acm_certificate(options):
    client = get_client('acm', options)
    cert_arn = client.request_certificate(
            DomainName=f'{options["s3_bucket"]}',
            ValidationMethod='DNS',
            SubjectAlternativeNames=[f'www.{options["s3_bucket"]}'])
    return cert_arn['CertificateArn']


def check_certificate_records(cert_arn, options):
    zone = get_hosted_zone_id(options)
    r53_client = get_client('route53', options)

    acm_client = get_client('acm', options)
    response = acm_client.describe_certificate(CertificateArn=cert_arn)
    validations = response["Certificate"]["DomainValidationOptions"]

    for validation in validations:
        record = r53_client.test_dns_answer(HostedZoneId=zone,
                  RecordName=validation['ResourceRecord']['Name'],
                   RecordType='CNAME')
        if len(record['RecordData']) < 1:
            record_q = input(('No CNAME Validation Record Found for'
                                f' {validation["ResourceRecord"]["Name"]}.'
                                '  Create one (y/n)? '))
            if record_q == 'y':
                create_cname_record(options, validation, zone)
            else:
                raise SystemExit('DNS-Validated Certificate'
                                 ' needed to continue')
        else:
            print( f' {validation["ResourceRecord"]["Name"]}'
                    'DNS Validation CNAME Record found')


def check_certificate_validation(options, cert_arn):
    acm_client = get_client('acm', options)
    certificate = acm_client.describe_certificate(CertificateArn=cert_arn)
    for item in certificate['Certificate']['DomainValidationOptions']:
        if str(item['DomainName']).endswith(options['s3_bucket']):
            if item['ValidationStatus'] == 'SUCCESS':
                print("SSL Certificate Validated!")
            else:
                print('Waiting up to 40 minutes for certificate validation...')
                waiter = acm_client.get_waiter('certificate_validated')
                waiter.wait(CertificateArn=cert_arn)


def check_dns(cdn_arn, options):
    print('\nRetrieving A records:')
    zone_id = get_hosted_zone_id(options)
    records = get_record_sets(zone_id, options)
    a_records = {}
    for record in records['ResourceRecordSets']:
        if record['Type'] == 'A':
            a_records[record['Name'][0:-1]] = record

    if options['s3_bucket'] in a_records:
        print(f'{options["s3_bucket"]} in A records')
    else:
        print(f'{options["s3_bucket"]} NOT in A records')
        response = input('Create record now? (Y/n): ')
        if not response == 'n':
            print('\nCreating A record')
            cf_client = get_client('cloudfront', options)
            distribution = cf_client.get_distribution(
                                            Id=str(cdn_arn).split('/')[-1])
            status = create_a_record(zone_id,
                                    options['s3_bucket'],
                                    options,
                                    distribution['Distribution']['DomainName'])
            print(f'A record status: {status}')
    if f'www.{options["s3_bucket"]}' in a_records:
        print(f'www.{options["s3_bucket"]} in A records')
    else:
        print(f'www.{options["s3_bucket"]} NOT in A records')
        response = input('Create record now? (Y/n): ')
        if not response == 'n':
            client = get_client('s3', options)
            region = client.get_bucket_location(
                         Bucket=f'www.{options["s3_bucket"]}'
                            )
            region = region['LocationConstraint']
            if not region:
                region = 'us-east-1'
            dns_name = f's3-website-{region}.amazonaws.com'
            status = create_a_record(zone_id, f'www.{options["s3_bucket"]}',
                                     options, dns_name)
            print(f'A record status: {status}')


def check(options):
    s3_client = get_client('s3', options)

    print('\n#####\n\nWebsite Settings:')
    check_buckets(options['s3_bucket'], s3_client)
    confirm_website_settings(options, s3_client)

    print('\n#####\n ')
    print('Checking CDN Distribution...\n')
    cdn_arn = check_cdn_distribution(options)

    print('\n#####\n ')
    print('Checking DNS Records...\n')
    check_dns(cdn_arn, options)

    print('\nCheck Complete!\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='YAML data file', required=True)
    args = parser.parse_args()
    options = utils.load_yaml(args.data)['options']
    check(options)

            
