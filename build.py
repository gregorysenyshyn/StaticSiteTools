#!/usr/bin/env python3

import time
import argparse

import tools

def build(data):

    print('\nStarting build!')
    t0 = time.time()
    
    data = tools.load_yaml(data)
    
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
    for pageset in data['html']['pagesets']:
        tools.build_pageset(pageset, data['options'])
    print(f'Built all pages in {round(float(time.time() - t1), 4)} seconds')

    print('\n\n=== I M A G E S ===')
    tools.handle_images(data['options']) 

    print('\n\n=== Entire build done in',
          f'{round(float(time.time() - t0), 4)} seconds ===')

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help = 'YAML data file')
    args = parser.parse_args()
    
    build(args.data)