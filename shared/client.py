import boto3

def get_client(service, options):
    session_args = {}
    if 'aws_profile_name' in options:
        session_args['profile_name'] = options['aws_profile_name']
    if 'aws_region_name' in options:
        session_args['region_name'] = options['aws_region_name']

    session = boto3.Session(**session_args)
    return session.client(service)
