#!/usr/bin/env python

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
from SocketServer import ThreadingMixIn
import threading
import uuid
import urlparse
import os.path
import picture_recognition as pr
import shutil
import mimetypes
import posixpath
import datetime
import json, re,  urllib
import cv2
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from cgi import parse_header, parse_multipart

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
        try:
            print "Threaded request : ", threading.currentThread().getName()
            request_dict = parse_get_string(self.path)
            timestamp = get_time()
            request_dict["timestamp"] = timestamp
        except (KeyError, ValueError) as e:
            print "Exception: %s. Try to serve static document" % e
            self.serve_static_documents()
            return

            # set headers
            self.send_headers('text/plain')
            self.wfile.write("success".format(result.shape[0]))
            


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
        #self.send_header("Content-Length", str(length))
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

    def copyfile(self, source, outputfile):
        """Copy all data between two file objects.
        The SOURCE argument is a file object open for reading
        (or anything with a read() method) and the DESTINATION
        argument is a file object open for writing (or
        anything with a write() method).
        The only reason for overriding this would be to change
        the block size or perhaps to replace newlines by CRLF
        -- note however that this the default server uses this
        to copy binary data as well.
        """
        shutil.copyfileobj(source, outputfile)

    def guess_type(self, path):
        """Guess the type of a file.
        Argument is a PATH (a filename).
        Return value is a string of the form type/subtype,
        usable for a MIME Content-type header.
        The default implementation looks the file's extension
        up in the table self.extensions_map, using application/octet-stream
        as a default; however it would be permissible (if
        slow) to look inside the data to make a better guess.
        """

        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']

    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream', # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
        })


    def send_headers(self, mimetype):
        self.send_response(200)
        self.send_header('Content-type', mimetype)
        self.end_headers()
        
        
    def serve_static_documents(self):
        """
        retrieve html pages relative to the path static/
        """
        print "path: %s" % self.path
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
            print "url does not start with 'static/...', reject request for '%s'" % filename
            return
        #if filename.startswith("static/scripts/"):
            # avoid trickery with '../../'
        #    print "invalid url, reject request for '%s'" % filename
        #    return
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

        print "mimetype: %s" % mimetype
        print "filename: %s" % filename
        try:
            self.send_headers(mimetype)
            fh = open(filename, "rb")
            self.wfile.write(fh.read())
            fh.close()
        except IOError as e:
            print e
            self.send_error(404, "File '%s' not found" % self.path)
            
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

