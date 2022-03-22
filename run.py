#!/usr/bin/env python3

# https://stackoverflow.com/questions/56383049/accessing-form-data-values-in-python-http-server-using-cgi-module

import getopt, sys, os
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
    sessionFile = ".session-demo.pkl"
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

class DemoWebServerBase(CGIHTTPRequestHandler):

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
                self.form.stream(base=self.basetmpl,
                                 http_headers=self.http_headers,
                                 title="Demo Generation",
                                 handler=self,
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

    clientSessionCookieName = "demo_session"

    def processCookie(self):
        print("calling processCookie")
        cookies = self.parseCookies(self.headers["Cookie"])
        if self.clientSessionCookieName in cookies:
            print("using demo_session from cookie")
            self.sessionid = cookies[self.clientSessionCookieName]
        else:
            print("using new generated session")
            self.sessionid = self.generateSessionId()

        SessionStore.addSessionStore(self.sessionid)

        self.printSessionStore()
        self.cookie = f"demo_session={self.sessionid}"
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

class DemoWebServerTemplate(DemoWebServerBase):

    env = Environment(loader=BaseLoader())

    basetmpl = env.from_string("""
<!DOCTYPE html>
<html lang="en" prefix="og: https://ogp.me/ns#">
<head>

    <!--
    <title>The Rock (1996)</title>
    <meta property="og:title" content="The Rock" />
    <meta property="og:type" content="video.movie" />
    <meta property="og:url" content="https://www.imdb.com/title/tt0117500/" />
    <meta property="og:image" content="https://ia.media-imdb.com/images/rock.jpg" />


    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    -->

    {% block http_headers %}{% endblock %}

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
{% block http_headers %} {{ http_headers | safe }} {% endblock %}
{% block content %}
<div>Hello World</div>
<div>Path: {{ path }}</div>
<div>IP: {{ ip }}</div>
<div>PORT: {{ port }}</div>
{% endblock %}
""")

    http_headers = """<title>Latest Viral Jokes Husband How Much Do You Love Me Read Most Funny Chutkule In Hindi - Latest Viral Jokes: जब पत्नी ने पति पूछा- तुम मुझसे कितना प्यार करते हो, जवाब सुनकर नहीं रुकेगी हंसी - Amar Ujala Hindi News Live</title>
<meta name="description" content="Latest viral jokes: हमेशा हंसते और मुस्कुराते रहने से हमारा शरीर और मन दोनों ही स्वस्थ रहता है। एक्सपर्ट्स का भी मानना है कि हंसने से बड़ी से बड़ी बीमारी से छुटकारा पाने में आसानी होती है। Read latest hindi news (ताजा हिन्दी समाचार) on santa banta viral jokes, viral jokes, latest jokes - #1 हिन्दी न्यूज़ website.">
<meta name="keywords" content="Santa banta viral jokes, viral jokes, latest jokes, viral hindi jokes, lot pot kar dene wale chutkule, lot pot karne wale chutkule, hasi se lot pot chutkule, lot pot chutkule hindi me, lot pot chutkule in hindi, लोट पोट चुटकुले, santa banta, new latest jokes, new latest jokes in hindi 2022, hindi me jokes, husband wife jokes, funny jokes, funny hindi jokes, girlfriend boyfriend jokes, latest jokes in hindi, latest whatsapp joke in hindi, hindi chutkule hd, जोक्स इन हिंदी, हिंदी चुटकुले, जोक्स">
<meta name="google-site-verification" content="RHOAa1hn5yFLUJCuE3dE9qqjBd1K9wLBVqh1uyRwEK0" />
<meta name="msvalidate.01" content="45F3E4C6A0E89A4DE2B637A9CFE04125" />
<meta name="news_keywords" content="Santa banta viral jokes, viral jokes, latest jokes, viral hindi jokes, lot pot kar dene wale chutkule, lot pot karne wale chutkule, hasi se lot pot chutkule, lot pot chutkule hindi me, lot pot chutkule in hindi, लोट पोट चुटकुले, santa banta, new latest jokes, new latest jokes in hindi 2022, hindi me jokes, husband wife jokes, funny jokes, funny hindi jokes, girlfriend boyfriend jokes, latest jokes in hindi, latest whatsapp joke in hindi, hindi chutkule hd, जोक्स इन हिंदी, हिंदी चुटकुले, जोक्स">
<meta name="robots" content="max-image-preview:large">
<link rel="canonical" href="https://www.amarujala.com/photo-gallery/humour/latest-viral-jokes-husband-how-much-do-you-love-me-read-most-funny-chutkule-in-hindi">
<link rel="amphtml" href="https://www.amarujala.com/amp/photo-gallery/humour/latest-viral-jokes-husband-how-much-do-you-love-me-read-most-funny-chutkule-in-hindi">
<meta property="fb:app_id" content="1652954484952398" />
<meta property="fb:pages" content="155612491169181" />
<meta property="og:locale" content="hi_IN" />
<meta property="og:type" content="article" />
<meta property="og:title" content="जोक्स: जब पत्नी ने पति पूछा- तुम मुझसे कितना प्यार करते हो, जवाब सुनकर नहीं रुकेगी हंसी" />
<meta property="og:headline" content="Latest viral jokes: जब पत्नी ने पति पूछा- तुम मुझसे कितना प्यार करते हो, जवाब सुनकर नहीं रुकेगी हंसी" />
<meta property="og:description" content="हमेशा हंसते और मुस्कुराते रहने से हमारा शरीर और मन दोनों ही स्वस्थ रहता है। एक्सपर्ट्स का भी मानना है कि हंसने से बड़ी" />
<meta property="og:url" content="https://www.amarujala.com/photo-gallery/humour/latest-viral-jokes-husband-how-much-do-you-love-me-read-most-funny-chutkule-in-hindi" />
<meta property="og:image" content="https://spiderimg.amarujala.com/assets/images/2022/03/07/750x506/viral-jokes-in-hindi_1646647713.jpeg">
<meta property="og:image:width" content="750">
<meta property="og:image:height" content="506">
<meta property="og:site_name" content="Amar Ujala" />
<meta name="twitter:description" content="हमेशा हंसते और मुस्कुराते रहने से हमारा शरीर और मन दोनों ही स्वस्थ रहता है। एक्सपर्ट्स का भी मानना है कि हंसने से बड़ी">
<meta name="twitter:url" content="https://www.amarujala.com/photo-gallery/humour/latest-viral-jokes-husband-how-much-do-you-love-me-read-most-funny-chutkule-in-hindi" />
<meta name="twitter:title" content="जोक्स: जब पत्नी ने पति पूछा- तुम मुझसे कितना प्यार करते हो, जवाब सुनकर नहीं रुकेगी हंसी">
<meta name="twitter:image" content="https://spiderimg.amarujala.com/assets/images/2022/03/07/750x506/viral-jokes-in-hindi_1646647713.jpeg">
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:site" content="@AmarUjalaNews" />
<meta name="twitter:creator" content="@AmarUjalaNews" />
<meta itemprop="name" content="Latest viral jokes: जब पत्नी ने पति पूछा- तुम मुझसे कितना प्यार करते हो, जवाब सुनकर नहीं रुकेगी हंसी">
<meta itemprop="description" content="हमेशा हंसते और मुस्कुराते रहने से हमारा शरीर और मन दोनों ही स्वस्थ रहता है। एक्सपर्ट्स का भी मानना है कि हंसने से बड़ी से बड़ी बीमारी से छुटकारा पाने में आसानी होती है।">
<meta itemprop="image" content="https://spiderimg.amarujala.com/assets/images/2022/03/07/viral-jokes-in-hindi_1646647713.jpeg">
<meta itemprop="publisher" content="Amar Ujala" />
<meta itemprop="url" content="https://www.amarujala.com/photo-gallery/humour/latest-viral-jokes-husband-how-much-do-you-love-me-read-most-funny-chutkule-in-hindi" />
<meta itemprop="editor" content="www.amarujala.com" />
<meta itemprop="headline" content="Latest viral jokes: जब पत्नी ने पति पूछा- तुम मुझसे कितना प्यार करते हो, जवाब सुनकर नहीं रुकेगी हंसी" />
<meta itemprop="inLanguage" content="Hindi" />
<meta itemprop="sourceOrganization" content="Amar Ujala" />
<meta itemprop="keywords" content="santa banta viral jokes, viral jokes, latest jokes, viral hindi jokes, lot pot kar dene wale chutkule, lot pot karne wale chutkule, hasi se lot pot chutkule, lot pot chutkule hindi me, lot pot chutkule in hindi, लोट पोट चुटकुले, santa banta, new latest jokes, new latest jokes in hindi 2022, hindi me jokes, husband wife jokes, funny jokes, funny hindi jokes, girlfriend boyfriend jokes, latest jokes in hindi, latest whatsapp joke in hindi, hindi chutkule hd, जोक्स इन हिंदी, हिंदी चुटकुले, जोक्स" />
"""


class DemoWebServer(DemoWebServerTemplate):
    def __init__(self, request, client_address, server):
        DemoWebServerBase.__init__(self, request, client_address, server)

    def do_POST(self):
        print("calling do_POST")
        print(f"self.path=u{self.path}")
        try:
            ctype, pdict = cgi.parse_header(self.headers['content-type'])
            content_len = int(self.headers.get('Content-length'))
            self.processCookie()
            self.outputPage(path = self.path,
                            ip = self.client_address[0],
                            port = self.client_address[1])
        except Exception as e:
            self.exceptionPage(e)

    def do_GET(self):
        try:
            print("calling do_GET")

            print(f"self.path = {self.path}")

            self.processCookie()
            self.outputPage(path = self.path,
                            ip = self.client_address[0],
                            port = self.client_address[1])
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

