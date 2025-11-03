import boto3
from botocore.exceptions import ClientError

def get_distribution_id(cf_client, bucket_name):
    """Gets the distribution ID for a given bucket name."""
    distribution_id = None
    response = cf_client.list_distributions()
    for item in response['DistributionList']['Items']:
        if "Items" in item["Aliases"]:
            if bucket_name in item['Aliases']['Items']:
                distribution_id = item['Id']
    return distribution_id
