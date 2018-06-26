#!/usr/bin/env python

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
from SocketServer import ThreadingMixIn
import threading
import urlparse
import os.path
import picture_recognition as pr
import shutil
import mimetypes
import posixpath
import datetime
import json, re, urllib
import cv2

def get_time():
    from time import gmtime, strftime
    return strftime("%Y-%m-%d %H:%M:%S", gmtime())


def parse_get_string(path):
    """
    extract key-value pairs from GET query
    """
    
    path, get_data = path.split("?")
    kv_pairs = get_data.split("&")
    print get_data
    d = {}
    for kv in kv_pairs:
        key, value = kv.split("=")
        d[key] = value.replace("%20", " ").replace("%40", "@").replace("%23", "#")
    print "dictionary: %s" % d
    
    return d


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

class MyServer(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwds):
        BaseHTTPRequestHandler.__init__(self, *args, **kwds)

    def do_GET(self):
        """Serve a GET request."""
        self.serve_static_documents()

    def do_POST(self):
        """Serve a POST request."""
        r, info = self.deal_post_data()
        print r, info, "by: ", self.client_address

        image, gray = pr.get_image_from_path(info)
        faces = pr.get_faces(gray)
        result = {}
        for count, (x, y, w, h) in enumerate(faces):
            result[count] = {}
            result[count]["id"], result[count]["confidence"] = pr.recognize(gray, x, y, w, h)
            result[count]["x"], result[count]["y"], result[count]["w"], result[count]["h"]  = (int(x), int(y), int(w), int(h))

        print result
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(json.dumps(result))


        
    def deal_post_data(self):
        boundary = self.headers.plisttext.split("=")[1]
        remainbytes = int(self.headers['content-length'])
        line = self.rfile.readline()
        remainbytes -= len(line)
        if not boundary in line:
            return (False, "Content NOT begin with boundary")
        line = self.rfile.readline()
        remainbytes -= len(line)
        fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line)
        if not fn:
            return (False, "Can't find out file name...")
        path = self.translate_path(self.path)
        fn = os.path.join(path, 'uploads/' + fn[0])
        line = self.rfile.readline()
        remainbytes -= len(line)
        line = self.rfile.readline()
        remainbytes -= len(line)
        try:
            out = open(fn, 'wb')
        except IOError:
            return (False, "Can't create file to write, do you have permission to write?")
                
        preline = self.rfile.readline()
        remainbytes -= len(preline)
        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            if boundary in line:
                preline = preline[0:-1]
                if preline.endswith('\r'):
                    preline = preline[0:-1]
                out.write(preline)
                out.close()
                return (True, fn)
            else:
                out.write(preline)
                preline = line
        return (False, "Unexpect Ends of data.")

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.
        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)
        """
        # abandon query parameters
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = os.getcwd()
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path

    def send_headers(self, mimetype):
        self.send_response(200)
        self.send_header('Content-type', mimetype)
        self.end_headers()
        
        
    def serve_static_documents(self):
        """
        retrieve html pages relative to the path static/
        """
        print "path: {}".format(self.path)
        res = urlparse.urlparse(self.path)
        path = res.path
        
        # remove leading '/'
        if path.startswith("/"):
            path = path[1:]
        if path == "":
            path = "index.html"
        filename = urlparse.urljoin("static/", path)
        if not filename.startswith("static/"):
            # avoid trickery with '../../'
            print "url does not start with 'static/...', reject request for '{}'".format(filename)
            return
       
        if filename.endswith(".html"):
            mimetype = "text/html"
        elif filename.endswith(".png"):
            mimetype = "image/png"
        elif filename.endswith(".jpg"):
            mimetype = "image/jpeg"
        elif filename.endswith(".jpeg"):
            mimetype = "image/jpeg"
        elif filename.endswith(".gif"):
            mimetype = "image/gif"
        elif filename.endswith(".js"):
            mimetype = "application/javascript"
        elif filename. endswith(".css"):
            mimetype = "text/css"
        else:
            mimetype = "text/plain"

        print "mimetype: {}".format(mimetype)
        print "filename: {}".format(filename)
        try:
            self.send_headers(mimetype)
            fh = open(filename, "rb")
            self.wfile.write(fh.read())
            fh.close()
        except IOError as e:
            print e
            self.send_error(404, "File '{}' not found".format(self.path))
            
    def log_message(self, frmt, *args):
        # silence the web server
        return

        
def run(server_class=ThreadedHTTPServer, handler_class=MyServer):
    port = 80
    server_address = ('', port)
    server = server_class(server_address, handler_class)
    print "Starting server on port {}".format(port)
    server.serve_forever()

if __name__ == "__main__":
    run()

