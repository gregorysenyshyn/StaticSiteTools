#!/usr/bin/env python3

import os
import time
import argparse
import subprocess

from website import tools

def build(data):

    print('\nStarting build!')
    t0 = time.time()

    print('\n\n=== C L E A N ===')
    print(f'cleaning {data["options"]["dist"]}...', end='')
    tools.clean(data['options']['dist'])
    print(' Done!')

    print('\n\n=== J S ===')
    for dest_path in data['js']['paths']:
        tools.handle_js(data, dest_path)

    print('\n\n=== C S S ===')
    for dest_path in data['scss']['paths']:
        tools.handle_scss(data, dest_path)

    print('\n\n=== H T M L ===')
    t1 = time.time()
    for pageset in data['html']:
        tools.build_pageset(pageset, data['options'])
    print(f'Built all pages in {round(float(time.time() - t1), 4)} seconds')

    print('\n\n=== I M A G E S ===')
    tools.handle_images(data['options'])

    print('\n\n=== A U D I O ===')
    tools.handle_audio(data['options'])

    print('\n\n=== M I S C ===')
    if not data['options']['production']:
        print('Creating symlink for .htaccess...', end='')
        subprocess.run(['ln', '-s',
                        os.path.join(os.getcwd(),
                                     data['options']['htaccess']),
                        data['options']['dist']])
        print(' Done!')

    print('\n\n=== Entire build done in',
          f'{round(float(time.time() - t0), 4)} seconds ===')


if __name__ == '__main__':

    try:
        from shared import utils, client

    except ImportError:
        import sys
        sys.path.append(sys.path[0] + '/..')
        from shared import utils, client

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='YAML data file')
    parser.add_argument('--production',
                        action='store_true',
                        help='Include analytics, etc.')
    args = parser.parse_args()
    data = utils.load_yaml(args.data)
    if args.production:
        data['options']['production'] = True
    build(data)
