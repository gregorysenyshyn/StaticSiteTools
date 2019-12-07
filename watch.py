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
        self.data = tools.load_yaml(data)
    
    def on_any_event(self, event):
        for dest_path in self.data['js']['paths']:
            if isinstance(self.data['js']['paths'][dest_path], str):
                self.data['js']['paths'][dest_path] = [self.data['js']['paths'][dest_path]]
            for path in self.data['js']['paths'][dest_path]:
                for search_path in self.data['js']['search']:
                    if event.src_path in glob(os.path.join(search_path, path)):
                        print('\n')
                        tools.handle_js(self.data, dest_path)
                        return

class CssEventHandler(FileSystemEventHandler):
    
    def __init__(self, data):
        self.data = tools.load_yaml(data)
    
    def on_any_event(self, event):
        for dest_path in self.data['scss']['paths']:
            if isinstance(self.data['scss']['paths'][dest_path], str):
                self.data['scss']['paths'][dest_path] = [self.data['scss']['paths'][dest_path]]
            for path in self.data['scss']['paths'][dest_path]:
                for search_path in self.data['scss']['search']:
                    if event.src_path in glob(os.path.join(search_path, path)):
                        print('\n')
                        tools.handle_scss(self.data, dest_path)
                        return

class HtmlEventHandler(FileSystemEventHandler):
    
    def __init__(self, data):
        self.data = tools.load_yaml(data)
    
    def on_any_event(self, event):
        for pageset in self.data['html']:
            for pathset in pageset:
                for fileset in pageset[pathset]:
                    if isinstance(fileset['src'], str):
                        fileset['src'] = [fileset['src']]
                for pathset in fileset['src']:
                    if event.src_path in glob(pathset):
                        page = ({'src': event.src_path,
                                 'template': fileset['template'],
                                 'dest': tools.get_destination(event.src_path,
                                                              fileset['dest'])})
                        tools.set_page_metadata(page)
                        j2_env = tools.get_j2_env(pageset)
                        print('\n')
                        tools.build_page(page, j2_env, self.data['options']['dist'])
                        return
                

def watch_files(data):
    
    observer = Observer()
    observer.schedule(CssEventHandler(data), 'src/scss/', recursive=True)
    observer.schedule(JsEventHandler(data), 'src/js/', recursive=True)
    observer.schedule(HtmlEventHandler(data), 'src/pages/', recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help = 'YAML data file')
    args = parser.parse_args()
    
    watch_files(args.data)