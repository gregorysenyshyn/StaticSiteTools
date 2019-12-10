#! /usr/bin/env python3

import os
import argparse
import http.server
import socketserver

class SimpleHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    
                     
    def do_GET(self):
        data = {}
        if not self.path.endswith( ('.css','.js','.jpg','.png') ):
            data['content-type'] = 'text/html'
        elif self.path.endswith('css'):
            data['content-type'] = 'text/css'
        elif self.path.endswith('js'):
            data['content-type'] = 'application/javascript'
        elif self.path.endswith('jpg'):
            data['content-type'] = 'image/jpeg'
        elif self.path.endswith('png'):
            data['content-type'] = 'image/png'
        self.send_response(200)
        self.send_header('Content-type', data['content-type'])
        self.end_headers()
        
        if self.path == '/':
            self.path += INDEX 
        
        print(f'request for {self.path} from {os.getcwd()}')
        path = os.path.join(os.getcwd(), args.directory, self.path[1:])
        with open(path) as f:
            self.wfile.write(f.read().encode())
        
if __name__ == '__main__':

    PORT = 8080
    INDEX = 'index'
    Handler = SimpleHTTPRequestHandler
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', help = 'Directory to Serve')
    args = parser.parse_args()
    
    with socketserver.TCPServer(('', PORT), Handler) as httpd:
        try:
            print('serving at port', PORT)
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.shutdown()
            print('Server is shut down')