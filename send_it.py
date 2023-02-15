def send_it(options, client=None):
    if client is None:
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
        else:
            print(f'ERROR - Not uploading hidden file {filename}')


print((f'#####\nUploading {data["options"]["dist"]}'),
      (f'to {data["options"]["s3_bucket"]}...'))
send_it(data['options'])
print('Done!\n\n')
