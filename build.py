#!/usr/bin/env python3

import os
import time
import click
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
    if 'js' in data:
        for dest_path in data['js']['paths']:
            tools.handle_js(data, dest_path)

    print('\n\n=== C S S ===')
    if 'scss' in data:
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

    print('\n\n=== C O P Y ===')
    if 'copy' in data:
        tools.copy_files(data['copy'])
    

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


@click.command()
@click.option('--data', help='YAML data file')
@click.option('--production', is_flag=True, help='Include analytics, etc.')
def main(data, production):
    """This script builds the website."""
    try:
        from shared import utils
    except ImportError:
        import sys
        sys.path.append(sys.path[0] + '/..')
        from shared import utils

    data = utils.load_yaml(data)
    if production:
        data['options']['production'] = True
    else:
        data['options']['production'] = False
    build(data)


if __name__ == '__main__':
    main()
