#!/usr/bin/env python3

import os
import glob
import time
import shutil
import itertools
import subprocess

from jinja2 import BaseLoader
from jinja2 import Environment

import sass
import yaml
import boto3
import htmlmin
import mistune 
import frontmatter
from termcolor import colored

CACHE_CONTROL_AGE=86400


# ####### #
#  UTILS  #
# ####### #


class GlobLoader(BaseLoader):
    '''
    Uses glob from standard library to load files. Paths can be excluded by
    prepending an exclamation mark. Path expansion with ** works in Python 3.5+
    '''

    def __init__(self, paths):
        '''
        paths must be a list
        '''
        files = [self.concat_paths(item) for item in paths]
        self.files = list(itertools.chain.from_iterable(files))


    @classmethod
    def concat_paths(cls, paths_to_concat):
        '''
        Concatenates paths from lists or named individually
        '''
        positive_match = []
        negative_match = []
        if isinstance(paths_to_concat, list):
            for item in paths_to_concat:
                cls.append_path_to_list(item, positive_match, negative_match)
        elif isinstance(paths_to_concat, str):
            cls.append_path_to_list(paths_to_concat,
                                    positive_match,
                                    negative_match)
        return list(set(positive_match) - set(negative_match))


    @staticmethod
    def append_path_to_list(path_to_append, positive_match, negative_match):
        '''
        Sorts paths into positive and negative matches with correct path names
        '''
        if path_to_append.startswith('!'):
            negative_match += glob.glob(path_to_append[1:])
        else:
            positive_match += glob.glob(path_to_append)


    def get_source(self, environment, template):
        for item in self.files:
            if os.path.basename(item) == template:
                mtime = os.path.getmtime(item)
                with open(item, 'r') as f:
                    return (f.read(),
                            item,
                            lambda: mtime == os.path.getmtime(item))


def get_s3():
    return boto3.resource('s3')


def send_to_s3(s3, bucket, src, dest, metadata={}):
    with open(src, 'rb') as f:
        s3.Object(bucket, dest).put(Body=f, 
              ContentType=metadata['ContentType'],
              CacheControl=metadata['CacheControl'])


def search_include_paths(target_filename, include_paths):
    for include_path in include_paths:
        search_file = os.path.join(include_path, target_filename)
        if os.path.isfile(search_file):
            return search_file
    raise FileNotFoundError(f"Can't find {target_filename}")


def concat_files(glob_paths, include_paths=None):
    '''Takes a list of filenames and combines the contents of those files into
    one string
    '''
    files = []
    for path in glob_paths:
        globbed_paths = glob.glob(path)
        if globbed_paths:
            for file in globbed_paths:
                if os.path.isfile(file):
                    files.append(file)
        elif include_paths:
            files.append(search_include_paths(path, include_paths))
        else:
            raise FileNotFoundError("Can't find {0}".format(path))
    return_string = ''
    for current_file in files:
        with open(current_file, 'r') as f:
            return_string += f.read()
    return return_string


def clean(path):
    '''Delete files generated by build script'''
    for root, dirs, files in os.walk(os.path.expanduser(path)):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            if os.path.islink(os.path.join(root, d)):
                os.unlink(os.path.join(root, d))
            else:
                shutil.rmtree(os.path.join(root, d))


def copy_files(files_to_copy):
    for dest_path in files_to_copy:
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
        file_list = GlobLoader(files_to_copy[dest_path]).files
        for file in file_list:
            print((f'Copying {os.path.basename(file)} to {dest_path}'
                    '...'), end="")
            shutil.copyfile(file, os.path.join(dest_path,
                                               os.path.basename(file)))
            print(' Done!')



# #### #
#  JS  #
# #### #


def handle_js(js_paths, js_include_paths, options, s3=None, production=False):
    for dest_path in js_paths:
        t1 = time.time()
        print('Generating {0}...'.format(dest_path), end="")
        js_string = concat_files(js_paths[dest_path], js_include_paths)
        if production:
            print(f"Done!\nSending to S3...", end="")
            s3.Object(options['s3 bucket'], dest_path
                ).put(Body=js_string, 
                      ContentType='text/javascript',
                      CacheControl=f'max-age={CACHE_CONTROL_AGE}')
        else:
            os.makedirs(os.path.join(options['prod'],
                                     os.path.split(dest_path)[0]), 
                        exist_ok=True)
            with open(os.path.join(options['prod'], dest_path), 'w') as f:
                    f.write(js_string)
        print(' Done in {0} seconds'.format(round(float(time.time() - t1), 4)))


# ###### #
#  CSS   #
# ###### #


def write_css_file(destination, scss_string, options=None, s3=None, production=False):
    if production:
        print(f"Done!\nSending to S3...", end="")
        css_string = sass.compile(string=scss_string, 
                                  output_style='compressed')
        s3.Object(options['s3 bucket'], destination
                ).put(Body=css_string,
                      ContentType='text/css',
                      CacheControl=f'max-age={CACHE_CONTROL_AGE}')
    else:
        with open(destination, 'w') as f:
            f.write(sass.compile(string=scss_string))


def handle_scss(scss_paths, scss_include_paths, options=None, s3=None, production=False):
    for dest_path in scss_paths:
        t1 = time.time()
        print('Generating {0}...'.format(dest_path), end="")
        scss_string = concat_files(scss_paths[dest_path], scss_include_paths)
        if production: 
            write_css_file(dest_path,
                           scss_string,
                           options,
                           s3,
                           production)
        else:
            os.makedirs(os.path.join(options['prod'],
                                     os.path.split(dest_path)[0]), 
                        exist_ok=True)
            write_css_file(os.path.join(options['prod'],
                                        dest_path),
                           scss_string)
        print(' Done in {0} seconds'.format(round(float(time.time() - t1), 4)))

# ######## #
#  IMAGES  #
# ######## #

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
    else:
        image_dest = options["prod"]
        local_prod = os.path.expanduser(image_dest)
        print((f'linking {local_images} to {local_prod}...'), end='')
        subprocess.run(['ln', '-s', local_images, local_prod])
        print(' Done!')



# ###### #
#  HTML  #
# ###### #

def markdown_filter(text):
    renderer = mistune.Renderer(parse_html=True)
    markdown = mistune.Markdown(renderer=renderer)
    return markdown(text)


def get_destination(page, dest, production):
    '''
    Joins dest to the last part of the path from page, and strips the
    file extension
    '''
    basename = os.path.basename(page)
    if production:
        final_name = os.path.splitext(basename)[0]
    else:
        final_name = f'{os.path.splitext(basename)[0]}.html'
    return os.path.join(dest, final_name)


def get_nav_pages(files, production):
    nav_pages = []

    for fileset in files:
        fileset_pages = []
        if isinstance(fileset['src'], str):
            fileset_pages.append(fileset['src'])
        elif isinstance(fileset['src'], list):
            current_pages = GlobLoader.concat_paths(fileset['src'])
            for glob_page in current_pages:
                fileset_pages.append(glob_page)
        for page_name in fileset_pages:
            page = {'src': page_name,
                    'dest': get_destination(page_name, 
                                            fileset['dest'],
                                            production)}
            set_page_metadata(page)
            if 'order' in page['data']:
                nav_data = {}
                nav_data['title'] = page['data']['title']
                nav_data['dest'] = page['dest']
                nav_data['order'] = page['data']['order']
                if 'subtitle' in page['data']:
                    nav_data['subtitle'] = page['data']['subtitle']
                nav_pages.append(nav_data)
                     
    nav_pages = sorted(nav_pages, key=lambda x: x['order'])
    return nav_pages 


def set_page_metadata(page, index=False):
    '''
    Sets metadata, including dest, content, data
    '''
    if page['src'].endswith('.yaml'):
        with open(page['src'], 'r') as f:
            page['data'] = yaml.load(f)
        page['src'] = f'{page["src"][:-4]}html'

    elif page['src'].endswith('.md') or page['src'].endswith('.html'):
        fm_page = frontmatter.load(page['src'])
        page['data'] = fm_page.metadata
        if not index:
            page['content'] = fm_page.content
    else:
        print(f"{page['src']} must be in either .yaml,"
                ' .md or .html (jinja2) format!')


def get_pages(files, production):
    '''
    Returns a list containing one or more dicts of page data
    '''
    if isinstance(files, dict):
        files = [files]

    pages = []
    for fileset in files:
        current_filenames = GlobLoader.concat_paths(fileset['src'])

        for filename in current_filenames:
            page = ({'src': filename, 
                     'dest': get_destination(filename,
                                             fileset['dest'], 
                                             production),
                     'template': fileset['template']})

            set_page_metadata(page)
            pages.append(page)
            
    return pages


def build_pageset(pageset, options, s3=None, production=False):
    '''Logic for building pages.'''

    template_files = [pageset[pathset] for pathset in pageset
                      if pathset in ['partials', 'layouts']]
    pageset_options = pageset['options']
    if 'nav' in pageset_options:
        pageset_options['nav_pages'] = get_nav_pages(pageset['files'], 
                                                     production)

    j2_env = Environment(loader=GlobLoader(template_files), trim_blocks=True)
    j2_env.filters['markdown'] = markdown_filter
    pages = get_pages(pageset['files'], production)
    for page in pages:
        f_id = os.path.splitext(os.path.basename(page['src']))[0]
        page['data']['id'] = f_id 
        page['data']['production'] = production
        if 'site_globals' in page['data']:
            page['data']['site_globals'] = options['site_globals']
        if 'nav' in pageset_options:
            page['data']['nav_pages'] = pageset_options['nav_pages']
        page_time = time.time()
        print(f'Building {page["src"]}...', end='')
        if 'content' in page:
            final_page = j2_env.from_string(page['content']
                            ).render(page['data'])
        else:
            template = j2_env.get_template(page['template'])
            final_page = template.render(page['data']) 

        # UPDATE HTML TIDY BEFORE UNCOMMENTING
        # tidy_page, errors = tidy_document(final_page)
        # if errors:
        #     error_page = os.path.basename(page['src'])
        #     with open('HTMLTidy Errors', 'a') as f:
        #         f.write('{0}:\n{1}'.format(error_page, errors))

        print(f' Done writing {page["dest"]} in '
              f'{round(float(time.time() - page_time), 4)} seconds')

        if production:
            final_page = htmlmin.minify(final_page)
            print(f'Sending {page["dest"]} to S3...', end='')
            s3.Object(options['s3 bucket'], page['dest']
                    ).put(Body=final_page, ContentType='text/html')
            print('  Done!')
        else:
            local_path = os.path.join(options['prod'],
                                      os.path.dirname(page['dest']))
            os.makedirs(local_path, exist_ok=True)
            with open(os.path.join(options['prod'],
                                   page['dest']), 'w') as f:
                f.write(final_page)

