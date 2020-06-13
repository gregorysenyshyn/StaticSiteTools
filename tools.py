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
import htmlmin
import mistune
import frontmatter

import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

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
                   '...'),
                  end="")
            shutil.copyfile(file, os.path.join(dest_path,
                                               os.path.basename(file)))
            print(' Done!')


def link_static(src, dest):
    print((f'linking {src} to {dest}...'), end='')
    subprocess.run(['ln', '-s',
                    os.path.expanduser(src),
                    os.path.expanduser(dest)])
    print(' Done!')

def load_yaml(data):
    with open(data) as f:
        return yaml.load(f, Loader=Loader)

# #### #
#  JS  #
# #### #


def handle_js(data, dest_path):
    t1 = time.time()
    print(f'{time.asctime()} — Generating {dest_path}...', end="")
    js_string = ''
    js_string = concat_files(data['js']['paths'][dest_path],
                             data['js']['search'])
    os.makedirs(os.path.join(data['options']['dist'],
                             os.path.split(dest_path)[0]),
                exist_ok=True)
    with open(os.path.join(data['options']['dist'], dest_path), 'w') as f:
                f.write(js_string)
    print(' Done in {0} seconds'.format(round(float(time.time() - t1), 4)))


# ###### #
#  CSS   #
# ###### #


def handle_scss(data, dest_path):
    t1 = time.time()
    print(f'{time.asctime()} — Generating {dest_path}...', end="")
    scss_string = concat_files(data['scss']['paths'][dest_path],
                               data['scss']['search'])
    os.makedirs(os.path.join(data['options']['dist'],
                             os.path.split(dest_path)[0]),
                exist_ok=True)
    with open(os.path.join(data['options']['dist'], dest_path), 'w') as f:
        f.write(sass.compile(string=scss_string))
    print(' Done in {0} seconds'.format(round(float(time.time() - t1), 4)))

# ######## #
#  IMAGES  #
# ######## #

def handle_images(options):
    image_src = options['images']
    local_images = os.path.expanduser(image_src)
    image_dest = options['dist']
    print((f'linking {local_images} to {image_dest}...'), end='')
    subprocess.run(['ln', '-s', local_images, image_dest])
    print(' Done!')


# ###### #
#  HTML  #
# ###### #


def markdown_filter(text):
    renderer = mistune.Renderer(parse_html=True)
    markdown = mistune.Markdown(renderer=renderer)
    return markdown(text)


def get_j2_env(pageset):
    template_files = [pageset[pathset] for pathset in pageset
                      if pathset in ['partials', 'layouts']]
    j2_env = Environment(loader=GlobLoader(template_files), trim_blocks=True)
    j2_env.filters['markdown'] = markdown_filter
    return j2_env


def get_destination(page, dest):
    '''
    Joins dest to the last part of the path from page, and strips the
    file extension
    '''
    basename = os.path.basename(page)
    final_name = os.path.splitext(basename)[0]
    return os.path.join(dest, f'{final_name}.html')


def get_nav_pages(files):
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
                    'dest': get_destination(page_name, fileset['dest'])}
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

    elif page['src'].endswith('.md') or page['src'].endswith('.html'):
        fm_page = frontmatter.load(page['src'])
        page['data'] = fm_page.metadata
        # if not index:
        page['content'] = fm_page.content
    else:
        print(f"{page['src']} must be in either .yaml,"
               ' .md or .html (jinja2) format!')


def get_page(src, dest, template):
    page = ({'src': src,
             'dest': get_destination(src, dest),
             'template': template})
    set_page_metadata(page)
    return page


def get_pages(files):
    '''
    Returns a list containing one or more dicts of page data
    '''
    if isinstance(files, dict):
        files = [files]

    pages = []
    for fileset in files:
        current_filenames = GlobLoader.concat_paths(fileset['src'])

        for filename in current_filenames:
            page = get_page(filename, fileset['dest'], fileset['template'])
            pages.append(page)

    return pages


def build_page(page, j2_env, options):

    page_time = time.time()
    print(f'{time.asctime()} — Building {page["src"]}...', end='')

    if 'site_globals' in options:
        page['data']['site_globals'] = options['site_globals']
    if 'content' in page:
        final_page = j2_env.from_string(page['content']
                        ).render(page['data'])
    else:
        template = j2_env.get_template(page['template'])
        final_page = template.render(page['data'])

    local_path = os.path.join(options['dist'], os.path.dirname(page['dest']))
    os.makedirs(local_path, exist_ok=True)
    with open(os.path.join(options['dist'], page['dest']), 'w') as f:
        f.write(final_page)

    print(f' Done writing {page["dest"]} in '
          f'{round(float(time.time() - page_time), 4)} seconds')


def build_pageset(pageset, options):
    '''Logic for building pages.'''

    if pageset['options']['nav']:
        nav_pages = get_nav_pages(pageset['files'])

    pages = get_pages(pageset['files'])
    j2_env = get_j2_env(pageset)
    for page in pages:
        if 'nav' in pageset['options']:
            page['data']['nav_pages'] = nav_pages
        build_page(page, j2_env, options)
