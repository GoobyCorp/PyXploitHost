#!/usr/bin/python3

from http.server import SimpleHTTPRequestHandler, HTTPServer

SERVER_ADDR = "0.0.0.0"
SERVER_PORT = 80

SERVER_DIR = "http"

class HTTPHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        #move the path up to the SERVER_DIR
        self.path = SERVER_DIR + "/" + self.path
        super(HTTPHandler, self).do_GET()

with HTTPServer((SERVER_ADDR, SERVER_PORT), HTTPHandler) as httpd:
    print("Serving on port {}".format(SERVER_PORT))
    httpd.serve_forever()