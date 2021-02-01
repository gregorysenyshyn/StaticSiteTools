#!/usr/bin/env python3

import os
import time
import argparse
from glob import glob

import tools

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class JsEventHandler(FileSystemEventHandler):

    def __init__(self, data):
        self.data = data

    def on_any_event(self, event):
        for dest_path in self.data['js']['paths']:
            if isinstance(self.data['js']['paths'][dest_path], str):
                self.data['js']['paths'][dest_path] = [
                        self.data['js']['paths'][dest_path]]
            for path in self.data['js']['paths'][dest_path]:
                for search_path in self.data['js']['search']:
                    if event.src_path in glob(os.path.join(
                          os.path.expanduser(os.getcwd()), search_path, path)):
                        try:
                            tools.handle_js(self.data, dest_path)
                        except:
                            print("Error!")
                        return


class CssEventHandler(FileSystemEventHandler):

    def __init__(self, data):
        self.data = data

    def on_any_event(self, event):
        for dest_path in self.data['scss']['paths']:
            if isinstance(self.data['scss']['paths'][dest_path], str):
                self.data['scss']['paths'][dest_path] = [
                        self.data['scss']['paths'][dest_path]]
            for path in self.data['scss']['paths'][dest_path]:
                for search_path in self.data['scss']['search']:
                    if event.src_path in glob(os.path.join(
                          os.path.expanduser(os.getcwd()), search_path, path)):
                        try:
                            tools.handle_scss(self.data, dest_path)
                        except CompileError:
                            print("Compile Error!")
                        return


class HtmlEventHandler(FileSystemEventHandler):

    def __init__(self, data):
        self.data = data

    def on_any_event(self, event):
        for pageset in self.data['html']:
            for pathset in pageset['files']:
                if isinstance(pathset['src'], str):
                    pathset['src'] = [pathset['src']]
                for fileset in pathset['src']:
                    if event.src_path in glob(os.path.join(
                          os.path.expanduser(os.getcwd()),
                          fileset)):
                        page = ({'src': event.src_path,
                                 'template': pathset['template'],
                                 'dest': tools.get_destination(event.src_path,
                                                               pathset['dest'])})
                        tools.set_page_metadata(page)
                        if 'nav' in pageset['options']:
                            page['data']['nav_pages'] = tools.get_nav_pages(
                                                            pageset['files'])
                        j2_env = tools.get_j2_env(pageset)
                        try:
                            tools.build_page(page,
                                             j2_env,
                                             self.data['options'])
                        except Exception as e:
                            print(f'Error! {e}')
                        return


def watch(data):
    data = tools.load_yaml(data)
    observer = Observer()
    observer.schedule(CssEventHandler(data),
                      os.path.join(os.path.expanduser(os.getcwd()),
                                   'src/scss/'), recursive=True)
    observer.schedule(JsEventHandler(data),
                      os.path.join(os.path.expanduser(os.getcwd()), 'src/js/'),
                      recursive=True)
    observer.schedule(HtmlEventHandler(data),
                      os.path.join(os.path.expanduser(os.getcwd()),
                                   'src/pages/'), recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='YAML data file')
    args = parser.parse_args()

    watch(args.data)
