#! /usr/bin/env python3

import http.server
import socketserver

class SimpleHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    
    def do_html(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(f'request for {self.path}'.encode())
                     
    def do_GET(self):
        if not self.path.endswith( ('.css','.js','.jpg','.png') ):
            self.do_html()
    
if __name__ == '__main__':

    PORT = 8080
    Handler = SimpleHTTPRequestHandler
    
    with socketserver.TCPServer(('', PORT), Handler) as httpd:
        print('serving at port', PORT)
        httpd.serve_forever()