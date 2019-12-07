import boto3

# def clean_aws():
    #     s3_bucket_name = data['options']['s3 bucket']
    #     print(f'\n\n=== A W S ===\n\nCleaning {s3_bucket_name}')
    #     s3 = tools.get_s3()
    #     s3_bucket = s3.Bucket(s3_bucket_name)
    #     for obj in s3_bucket.objects.all():
    #         if not obj.key.startswith('static'):
    #             obj.delete()
    
    
    
    
    # if production:
    #     print(f"Done!\nSending to S3...", end="")
    #     s3.Object(options['s3 bucket'], dest_path
    #         ).put(Body=js_string, 
    #               ContentType='text/javascript',
    #               CacheControl=f'max-age={CACHE_CONTROL_AGE}')
    
    
    
def handle_images(options, s3=None, production=None):
    image_src = options["local_images"]
    local_images = os.path.expanduser(image_src)
    if production:
        file_list = os.listdir(local_images)
        s3_bucket = s3.Bucket(options['s3 bucket'])
        for filename in file_list:
            extra_args = {'CacheControl': f'max-age={CACHE_CONTROL_AGE}'}
            if filename.endswith('.svg'):
                extra_args['ContentType'] = 'image/svg+xml'
            if filename.endswith('.jpg') or filename.endswith('jpeg'):
                extra_args['ContentType'] = 'image/jpeg'
            if filename.endswith('.png'):
                extra_args['ContentType'] = 'image/png'
            if filename.endswith('.gif'):
                extra_args['ContentType'] = 'image/gif'
            local_filename = os.path.join(local_images, filename)
            remote_filename = os.path.join(options["remote_images"], filename)
            if not filename.startswith('.'):
                print(f'Copying {local_filename} to {remote_filename}...', 
                      end='')
                obj = s3_bucket.Object(remote_filename)
                with open(local_filename, 'rb') as f:
                    obj.upload_fileobj(f, ExtraArgs=extra_args)
                print(' Done!')
    
    
def get_s3():
    return boto3.resource('s3')


def send_to_s3(s3, bucket, src, dest, metadata={}):
    with open(src, 'rb') as f:
        s3.Object(bucket, dest).put(Body=f, 
              ContentType=metadata['ContentType'],
              CacheControl=metadata['CacheControl'])