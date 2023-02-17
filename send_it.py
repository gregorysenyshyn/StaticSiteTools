import os
import glob

import server_tools as st
from shared.utils import get_client

def send_it(options, client=None):
    if client is None:
        client = get_client(options, 's3')
    for filename in glob.glob(f'{options["dist"]}/**', recursive=True):
        if not filename.startswith('.'):
            if not os.path.isdir(filename):
                destname = filename[len(options['dist'])+1:]
                if destname.endswith('.html'):
                    destname = destname[:-5]
                    st.handle_page(filename, destname, options, client)
                elif destname.startswith('js/') and destname.endswith('.js'):
                    st.handle_js(filename, destname, options, client)
                elif destname.startswith('css/') and destname.endswith('.css'):
                    st.handle_css(filename, destname, options, client)
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
        build(data)
    else:
        raise SystemExit('Please build with --production before uploading!')

    check = input('Ready to send? (Y/n) ')
    if not check == 'n':
        print((f'#####\nUploading {data["options"]["dist"]}'),
              (f'to {data["options"]["s3_bucket"]}...'))
        send_it(data['options'])
        print('Done!\n\n')
