#!/usr/bin/env python3

# https://stackoverflow.com/questions/56383049/accessing-form-data-values-in-python-http-server-using-cgi-module

import getopt, sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../backend/app')
import cgi
from jinja2 import Environment, Template, BaseLoader
from http.server import HTTPServer, CGIHTTPRequestHandler
from random import randint
from datetime import date,datetime
import json
from base64 import b64decode, b64encode
from netifaces import interfaces, ifaddresses, AF_INET
import traceback


class DemoWebError(Exception):
    def __init__(self, *, code, message, errors):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        # Now for your custom code...
        self.code = code
        self.errors = errors

class SessionStore:
    sessionFile = ".session-lmgenweb.pkl"
    sessionStore = {}
    @staticmethod
    def writeSessionFile():
        if SessionStore.sessionFile and os.path.exists(SessionStore.sessionFile):
            os.rename(SessionStore.sessionFile, SessionStore.sessionFile + ".backup")
        with open(SessionStore.sessionFile, 'wb') as f:
            output = json.dumps(indent    = 4,
                                sort_keys = True ).encode('utf-8')
            f.write(output)

            # pickle.dump(SessionStore.sessionStore, f)
        print(f"Written session file {SessionStore.sessionFile}")

    @staticmethod
    def readSessionFile():
        if SessionStore.sessionFile and os.path.exists(SessionStore.sessionFile):
            with open(SessionStore.sessionFile, 'r') as f:
                SessionStore.sessionStore = json.loads(f.read())
                # SessionStore.sessionStore = pickle.load(f)
        else:
            print(f"No session file {SessionStore.sessionFile} exists")

    @staticmethod
    def getSessionStore(sessionid):
        return SessionStore.sessionStore[sessionid]

    @staticmethod
    def addSessionStore(sessionid):
        if sessionid not in SessionStore.sessionStore:
            SessionStore.sessionStore[ sessionid ] = {}

class DemoWebServer(CGIHTTPRequestHandler):

    env = Environment(loader=BaseLoader())

    basetmpl = env.from_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <style>
    <!-- https://stackoverflow.com/a/24334030 -->
    pre {
      font-size: inherit;
      color: inherit;
      border: initial;
      padding: initial;
      font-family: inherit;
    }
    </style>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/2.0.2/jquery.min.js"></script>
    <script src="http://code.jquery.com/ui/1.9.2/jquery-ui.min.js"></script>
    <title>{% block title %}{% endblock %}</title>
</head>
<body>
    <div class="container">
      <h2>Demo gen</h2>
      <br>
      {% block content %}{% endblock %}
      <br>
    </div>
    <div class="debug">
    {% if exception %}
      <h2>A exception occurred, Please report this text to dev team.</h2>
      <pre>
{{ exception | e }}
      </pre>
    {% endif %}
    </div>
</body>
</html>
""")

    form = env.from_string("""
{% extends base %}
{% block title %} {{ title }} {% endblock %}
{% block content %}
<div>Hello World</div>
{% endblock %}
""")


    def __init__(self, request, client_address, server):
        CGIHTTPRequestHandler.__init__(self, request, client_address, server)

    def parseCookies(self, cookie_list):
        return dict(((c.split("=")) for c in cookie_list.split(";"))) if cookie_list else {}

    def generateSessionId(self):
        return "".join(str(randint(1,9)) for _ in range(100))

    def outputPage(self, **kwargs):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                # self.send_header('Location', '/')
                self.setCookie()
                self.end_headers()
                self.form.stream(base = self.basetmpl,
                                 title = "Demo Generation",
                                 handler = self,
                                 genparams = self.genparams,
                                 password = (not privatekeys.Keys.password),
                                 **kwargs).dump(self.wfile, encoding='utf-8')

    def exceptionString(self, excp):
        # https://stackoverflow.com/questions/4564559/get-exception-description-and-stack-trace-which-caused-an-exception-all-as-a-st
        stack = traceback.extract_stack()[:-3] + traceback.extract_tb(excp.__traceback__)  # add limit=?? 
        pretty = traceback.format_list(stack)
        return ''.join(pretty) + '\n  {} {}'.format(excp.__class__,excp)

    def exceptionPage(self, exception: Exception, **kwargs):
        expstr = self.exceptionString(exception)
        print(expstr)
        self.outputPage(exception = expstr)

    def do_POST(self):
        print("calling do_POST")
        print(f"self.path=u{self.path}")
        try:
            ctype, pdict = cgi.parse_header(self.headers['content-type'])
            content_len = int(self.headers.get('Content-length'))
            self.processCookie()
            self.outputPage()
        except Exception as e:
            self.exceptionPage(e)

    clientSessionCookieName = "lmgenweb_session"

    def processCookie(self):
        print("calling processCookie")
        cookies = self.parseCookies(self.headers["Cookie"])
        if self.clientSessionCookieName in cookies:
            print("using lmgenweb_session from cookie")
            self.sessionid = cookies[self.clientSessionCookieName]
        else:
            print("using new generated session")
            self.sessionid = self.generateSessionId()

        SessionStore.addSessionStore(self.sessionid)

        self.printSessionStore()
        self.cookie = f"lmgenweb_session={self.sessionid}"
        print(f"current session {self.sessionid}")

        self.printSessionStore()

    def setCookie(self):
        print("calling setCookie")
        if self.cookie:
            self.send_header('Set-Cookie', self.cookie)

    def getSessionStore(self):
        return SessionStore.getSessionStore( self.sessionid )

    def printSessionStore(self):
        store = self.getSessionStore()
        print(f"sessionid {self.sessionid} store:")
        print(f"store = {store}")

    def getVal(self, key, default = ""):
        print(f"calling getval {key}")
        store = self.getSessionStore()
        if key in store:
            return store[key]
        else:
            return default

    def addVal(self, key, value):
        print(f"calling addval {key} = {value}")
        store = self.getSessionStore()
        store[key] = value

        self.printSessionStore()

        return value

    def do_GET(self):
        try:
            print("calling do_GET")
            self.processCookie()
            self.outputPage()
        except Exception as e:
            self.exceptionPage(e)

def main():
    args = []
    port = 8080
    host = '0.0.0.0'

    if len(sys.argv) > 1:
        args = sys.argv[1:]
    arguments, values = getopt.getopt(args,
                                      "h:p:",
                                      ["host=",
                                       "port="])
    for curr_arg, curr_value in arguments:
        if curr_arg in ("-p", "--port"):
            port = int(curr_value or port)
        elif curr_arg in ("-h", "--host"):
            host = curr_value

    lmgen = HTTPServer((host, port),
                       DemoWebServer)

    if '0.0.0.0' == host:
        addresses = list(filter(None, [ifaddresses(ifaceName).setdefault(AF_INET, [{'addr': None}] )[0]['addr'] for ifaceName in interfaces()]))
    else:
        addresses = [host]

    print(f"lmweb server listening at below addresses.")
    for addr in addresses:
        print(f"http://{addr}:{port}")

    try:
        SessionStore.readSessionFile()
        lmgen.serve_forever()
    finally:
        SessionStore.writeSessionFile()
    return 0



if __name__ == "__main__":
    main()

