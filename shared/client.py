import boto3

def get_client(service, options):
    session = boto3.Session(profile_name=options["aws_profile_name"],
                            region_name=options["aws_region_name"])
    return session.client(service)

def get_resource(service, options):
    session = boto3.Session(profile_name=options["aws_profile_name"],
                            region_name=options["aws_region_name"])
    return session.resource(service)
