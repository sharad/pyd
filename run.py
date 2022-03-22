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
<html lang="hi">
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

<script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "url": "https://www.amarujala.com/",
        "potentialAction": {
          "@type": "SearchAction",
          "target": "https://www.amarujala.com/search?q={search_term_string}",
          "query-input": "required name=search_term_string"
        }
      }
    </script>

<script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "url":"https://www.amarujala.com/photo-gallery/humour/latest-viral-jokes-husband-how-much-do-you-love-me-read-most-funny-chutkule-in-hindi",
    "articleBody":"हमेशा हंसते और मुस्कुराते रहने से हमारा शरीर और मन दोनों ही स्वस्थ रहता है। एक्सपर्ट्स का भी मानना है कि हंसने से बड़ी से बड़ी बीमारी से छुटकारा पाने में आसानी होती है। हंसने से हमारे शरीर के सभी अंगों में रक्त का संचार तेज हो जाता है, जो हमारे शरीर के लिए बहुत लाभदायक होता है। इसके साथ ही ये चेहरे, त्वचा और बालों की चमक में भी वृद्धि करता है जिससे आप और भी आकर्षक लगते हैं।  हंसने के और भी कई फायदे हैं, इससे हमारी सांस लेने की प्रक्रिया में तेज हो जाती है। ऐसे में हमारी पाचन क्रिया भी सही काम करती है। इन सभी चीजों को ध्यान में रखते हुए आज हम आपके लिए बेहद मजेदार चुटकुले लेकर आएं हैं, तो आइए खोलते हैं ये जोक्स का पिटारा...   पत्नी- तुम मुझसे कितना प्यार करते हो? पति- शाहजहां से भी ज्यादा। पत्नी- मेरे मरने के बाद ताजमहल बनाओगे। पति- मैं तो प्लॉट ले भी चुका हूं पगली देर तो तू ही कर रही है। पति ने पत्नी को मेसेज भेजा-… मेरी जिंदगी इतनी प्यारी, इतनी खूबसूरत बनाने के लिए तुम्हारा शुक्रिया। मैं आज जो भी हूं, सिर्फ तुम्हारी वजह से हूं। तुम मेरे जीवन में एक फरिश्ता बनकर आई हो और तुमने ही मुझे जीने का मकसद दिया है। लव यू डार्लिंग… पत्नी ने रिप्लाई किया… मार लिया चौथा पैग? आ जाओ घर कुछ नही कहूँगी। परीक्षा में एक छात्र कॉपी पर फूल बना रहा था... टीचर - यह क्या कर रहे हो? फूल क्यों बना रहे हो? छात्र - सर, यह फूल मेरी याद्दाश्त को समर्पित है, जो अभी-अभी गुजर गई...!! एक आदमी खड़े खड़े चाबी से अपना कान खुजा रहा था। दूसरा आदमी पास जाकर बोला: भाई अगर तू स्टार्ट नहीं हो पा रहा है तो धक्का लगाऊं क्या? संता बंता को गुस्से से बोल रहा था। संता- यार, जब मैंने तुझे खत लिखा था कि मेरी शादी में जरूर आना। तो तुम आये क्यों नही? बंता- ओह यार, पर मुझे खत मिला ही नही। संता- मैंने लिखा तो था कि खत मिले या ना मिले तुम जरूर �
    "articleSection": "Humour",
    "mainEntityOfPage":{
      "@type":"WebPage",
      "@id":"https://www.amarujala.com/photo-gallery/humour/latest-viral-jokes-husband-how-much-do-you-love-me-read-most-funny-chutkule-in-hindi"
    },
    "headline": "Latest viral jokes: जब पत्नी ने पति पूछा- तुम मुझसे कितना प्यार करते हो, जवाब सुनकर नहीं रुकेगी हंसी",
    "description": "हमेशा हंसते और मुस्कुराते रहने से हमारा शरीर और मन दोनों ही स्वस्थ रहता है। एक्सपर्ट्स का भी मानना है कि हंसने से बड़ी से बड़ी बीमारी से छुटकारा पाने में आसानी होती है।",
    "datePublished": "2022-03-17T17:39:39+05:30",
    "dateModified": "2022-03-17T18:28:06+05:30",
    "publisher": {
      "@type": "Organization",
      "name": "Amarujala",
      "logo": {
        "@type": "ImageObject",
                "url": "https://spiderimg.amarujala.com/assets/img/au-logo.png",
        "width": 240,
        "height": 35
              }
    },
    "author": {
      "@type": "Organization",
      "name": "Amar Ujala Digital Team",
      "url": "https://www.amarujala.com"
    },
    "image": {
      "@type": "ImageObject",
      "url": "https://spiderimg.amarujala.com/cdn-cgi/image/width=1600,height=900,fit=cover,f=auto/assets/images/2022/03/07/750x506/viral-jokes-in-hindi_1646647713.jpeg",
            "width": 1600,
      "height": 900
          },
    "keywords": ["santa banta viral jokes, viral jokes, latest jokes, viral hindi jokes, lot pot kar dene wale chutkule, lot pot karne wale chutkule, hasi se lot pot chutkule, lot pot chutkule hindi me, lot pot chutkule in hindi, लोट पोट चुटकुले, santa banta, new latest jokes, new latest jokes in hindi 2022, hindi me jokes, husband wife jokes, funny jokes, funny hindi jokes, girlfriend boyfriend jokes, latest jokes in hindi, latest whatsapp joke in hindi, hindi chutkule hd, जोक्स इन हिंदी, हिंदी चुटकुले, जोक्स"]
  }
  </script>
<script type="application/ld+json">
    [
        { 
    "@context": "https://schema.org",
    "@type": "ImageObject",
    "author": "Amar Ujala Digital Team",
    "contentUrl": "https://spiderimg.amarujala.com/assets/images/2022/03/07/750x506/viral-jokes-in-hindi_1646647713.jpeg",
    "datePublished": "2022-03-17T18:28:06+05:30",
    "description": "हमेशा हंसते और मुस्कुराते रहने से हमारा शरीर और मन दोनों ही स्वस्थ रहता है। एक्सपर्ट्स का भी मानना है कि हंसने से बड़ी से बड़ी बीमारी से छुटकारा पाने में आसानी होती है। हंसने से हमारे शरीर के सभी अंगों में रक्त का संचार तेज हो जाता है, जो हमारे शरीर के लिए बहुत लाभदायक होता है। इसके साथ ही ये चेहरे, त्वचा और बालों की चमक में भी वृद्धि करता है जिससे आप और भी आकर्षक लगते हैं।  हंसने के और भी कई फायदे हैं, इससे हमारी सांस लेने की प्रक्रिया में तेज हो जाती है। ऐसे में हमारी पाचन क्रिया भी सही काम करती है। इन सभी चीजों को ध्यान में रखते हुए आज हम आपके लिए बेहद मजेदार चुटकुले लेकर आएं हैं, तो आइए खोलते हैं ये जोक्स का पिटारा...   पत्नी- तुम मुझसे कितना प्यार करते हो? पति- शाहजहां से भी ज्यादा। पत्नी- मेरे मरने के बाद ताजमहल बनाओगे। पति- मैं तो प्लॉट ले भी चुका हूं पगली देर तो तू ही कर रही है।",
    "name": "जब पत्नी ने पति पूछा- तुम मुझसे कितना प्यार करते हो"
    },        { 
    "@context": "https://schema.org",
    "@type": "ImageObject",
    "author": "Amar Ujala Digital Team",
    "contentUrl": "https://spiderimg.amarujala.com/assets/images/2022/03/13/750x506/jokes-in-hindi_1647157243.jpeg",
    "datePublished": "2022-03-17T18:28:06+05:30",
    "description": "पति ने पत्नी को मेसेज भेजा-… मेरी जिंदगी इतनी प्यारी, इतनी खूबसूरत बनाने के लिए तुम्हारा शुक्रिया। मैं आज जो भी हूं, सिर्फ तुम्हारी वजह से हूं। तुम मेरे जीवन में एक फरिश्ता बनकर आई हो और तुमने ही मुझे जीने का मकसद दिया है। लव यू डार्लिंग… पत्नी ने रिप्लाई किया… मार लिया चौथा पैग? आ जाओ घर कुछ नही कहूँगी।",
    "name": "जब पत्नी ने पति पूछा- तुम मुझसे कितना प्यार करते हो"
    },        { 
    "@context": "https://schema.org",
    "@type": "ImageObject",
    "author": "Amar Ujala Digital Team",
    "contentUrl": "https://spiderimg.amarujala.com/assets/images/2022/03/07/750x506/jokes-in-hindi_1646632267.jpeg",
    "datePublished": "2022-03-17T18:28:06+05:30",
    "description": "परीक्षा में एक छात्र कॉपी पर फूल बना रहा था... टीचर - यह क्या कर रहे हो? फूल क्यों बना रहे हो? छात्र - सर, यह फूल मेरी याद्दाश्त को समर्पित है, जो अभी-अभी गुजर गई...!!",
    "name": "जब पत्नी ने पति पूछा- तुम मुझसे कितना प्यार करते हो"
    },        { 
    "@context": "https://schema.org",
    "@type": "ImageObject",
    "author": "Amar Ujala Digital Team",
    "contentUrl": "https://spiderimg.amarujala.com/assets/images/2022/03/07/750x506/jokes-in-hindi_1646632578.jpeg",
    "datePublished": "2022-03-17T18:28:06+05:30",
    "description": "एक आदमी खड़े खड़े चाबी से अपना कान खुजा रहा था। दूसरा आदमी पास जाकर बोला: भाई अगर तू स्टार्ट नहीं हो पा रहा है तो धक्का लगाऊं क्या?",
    "name": "जब पत्नी ने पति पूछा- तुम मुझसे कितना प्यार करते हो"
    },        { 
    "@context": "https://schema.org",
    "@type": "ImageObject",
    "author": "Amar Ujala Digital Team",
    "contentUrl": "https://spiderimg.amarujala.com/assets/images/2022/03/07/750x506/viral-jokes-in-hindi_1646648004.jpeg",
    "datePublished": "2022-03-17T18:28:06+05:30",
    "description": "संता बंता को गुस्से से बोल रहा था। संता- यार, जब मैंने तुझे खत लिखा था कि मेरी शादी में जरूर आना। तो तुम आये क्यों नही? बंता- ओह यार, पर मुझे खत मिला ही नही। संता- मैंने लिखा तो था कि खत मिले या ना मिले तुम जरूर आना।",
    "name": "जब पत्नी ने पति पूछा- तुम मुझसे कितना प्यार करते हो"
    }        ]
    </script>
<script type="application/ld+json">
        [
                {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "देश",
               "url" : "https://www.amarujala.com/india-news?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "शहर और राज्य",
               "url" : "https://www.amarujala.com/city-and-states?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "चुनाव 2022",
               "url" : "https://www.amarujala.com/election/vidhan-sabha-elections/uttar-pradesh?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "मनोरंजन",
               "url" : "https://www.amarujala.com/entertainment?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "क्रिकेट",
               "url" : "https://www.amarujala.com/cricket?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "ज्योतिष",
               "url" : "https://www.amarujala.com/astrology?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "दुनिया",
               "url" : "https://www.amarujala.com/world?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "नौकरी",
               "url" : "https://www.amarujala.com/jobs?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "शिक्षा",
               "url" : "https://www.amarujala.com/education?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "टेक्नॉलॉजी",
               "url" : "https://www.amarujala.com/technology?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "ऑटोमोबाइल",
               "url" : "https://www.amarujala.com/automobiles?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "कारोबार",
               "url" : "https://www.amarujala.com/business?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "विशेष",
               "url" : "https://www.amarujala.com/special-stories?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "आवाज",
               "url" : "https://www.amarujala.com/podcast?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "ट्रेंडिंग",
               "url" : "https://www.amarujala.com/recommended"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "वीडियो",
               "url" : "https://www.amarujala.com/video"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "",
               "url" : "https://www.amarujala.com/web-stories?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "न्यूज ब्रीफ",
               "url" : "https://www.amarujala.com/news-briefs?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "फोटो",
               "url" : "https://www.amarujala.com/photo-gallery?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "खेल",
               "url" : "https://www.amarujala.com/sports?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "लाइफ़स्टाइल",
               "url" : "https://www.amarujala.com/lifestyle?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "शक्ति",
               "url" : "https://www.amarujala.com/shakti?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "आस्था",
               "url" : "https://www.amarujala.com/spirituality?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "क्राइम",
               "url" : "https://www.amarujala.com/crime?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "काव्य",
               "url" : "https://www.amarujala.com/kavya?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "विचार",
               "url" : "https://www.amarujala.com/columns?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "हटके ख़बर",
               "url" : "https://www.amarujala.com/bizarre-news?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "हंसी-ठट्ठा",
               "url" : "https://www.amarujala.com/humour?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "कृषि",
               "url" : "https://www.amarujala.com/agriculture?src=mainmenu"
        },        
                   {
               "@context":"https://schema.org",          
               "@type": "SiteNavigationElement",
               "name": "पोल",
               "url" : "https://www.amarujala.com/poll?src=mainmenu"
        }        
                   ]
</script>
<script type="application/ld+json">
        {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Amarujala",
        "url": "https://www.amarujala.com/",
        "logo": "https://spiderimg.amarujala.com/assets/img/au-logo.png",
        "image": "https://spiderimg.amarujala.com/assets/img/au-logo.png",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "C-21, Sector-59",
            "addressLocality": "Noida",
            "addressRegion": "India",
            "postalCode": "201301",
            "Telephone": "0120-4694000"
        },
        "sameAs": [
            "https://www.facebook.com/Amarujala",
            "https://twitter.com/AmarUjalaNews",
            "https://www.youtube.com/user/NewsAmarujala",
            "https://www.instagram.com/amar_ujala/"
        ]
     }
</script>
<meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5"><meta name="theme-color" content="#DC2829"> <meta http-equiv="X-UA-Compatible" content="IE=edge"> <meta name="csrf-token" content="zApyjTCbKecYgS3WyRvscPTpI25KbanVIuzdpxFi" /> <meta name="apple-itunes-app" content="app-id=1028364855, affiliate-data=ct=Smart%20App%20Banner%20Tracker&amp;pt=2198976" /> <meta name="p:domain_verify" content="9d18a7a0a8b7e2660a9230ad073ab60e" /> <meta http-equiv="Content-Type" content="text/html"> <link rel="shortcut icon" type="image/ico" href="//spidercss1.itstrendingnow.com/assets/images/favicon.ico" />
<link rel="icon" sizes="192x192" href="/touch-icon.png"><link rel="icon" sizes="128x128" href="/touch-icon-128x128.png"><link rel="apple-touch-icon" sizes="128x128" href="/touch-icon-128x128.png"><link rel="apple-touch-icon-precomposed" sizes="128x128" href="/touch-icon-128x128.png"> <link rel="preconnect" crossorigin="anonymous" href="https://spidercss1.itstrendingnow.com"> <link rel="preconnect" crossorigin="anonymous" href="https://spiderimg.amarujala.com/"> <link rel="preconnect" crossorigin="anonymous" href="https://spiderjs1.itstrendingnow.com/"> <link rel="preconnect" crossorigin="anonymous" href="https://sb.scorecardresearch.com"> <link rel="preconnect" crossorigin="anonymous" href="https://www.google-analytics.com"> <link rel="preconnect" crossorigin="anonymous" href="https://securepubads.g.doubleclick.net"> <link rel="preconnect" crossorigin="anonymous" href="https://accounts.google.com"> <link rel="preconnect" crossorigin="anonymous" href="https://ads.pubmatic.com"> <link rel="preconnect" crossorigin="anonymous" href="https://cdn.ampproject.org"><link rel="preconnect" crossorigin="anonymous" href="https://sso.amarujala.com/"><link rel="preconnect" crossorigin="anonymous" href="https://fonts.gstatic.com/">
<link rel="preload" href="//spiderimg.amarujala.com/cdn-cgi/image/width=674,height=379.25,fit=cover,f=auto/assets/images/2022/03/07/750x506/viral-jokes-in-hindi_1646647713.jpeg" as="image" media="(min-width: 414.1px)">
<link rel="preload" href="//spiderimg.amarujala.com/cdn-cgi/image/width=414,height=233,fit=cover,f=auto/assets/images/2022/03/07/750x506/viral-jokes-in-hindi_1646647713.jpeg" as="image" media="(max-width: 414px)">
<link rel="preload" href="https://spidercss1.itstrendingnow.com/assets/v1/fonts/NotoSansDevanagariUI-Medium.woff2" as="font" type="font/woff2" crossorigin>
<link rel="manifest" href="/manifest.json?v=uy77u8i9gghyt">
<style>
@font-face{font-family:NotoSansDevanagariUI-Medium;src:local("NotoSansDevanagariUI-Medium"),url(https://spidercss1.itstrendingnow.com/assets/v1/fonts/NotoSansDevanagariUI-Medium.woff2) format("woff2"),url(https://spidercss1.itstrendingnow.com/assets/v1/fonts/NotoSansDevanagariUI-Medium.woff) format("woff"),url(https://spidercss1.itstrendingnow.com/assets/v1/fonts/NotoSansDevanagariUI-Medium.ttf) format("truetype"),url(https://spidercss1.itstrendingnow.com/assets/v1/fonts/NotoSansDevanagariUI-Medium.eot),url(https://spidercss1.itstrendingnow.com/assets/v1/fonts/NotoSansDevanagariUI-Medium.eot#iefix) format("embedded-opentype"),url(https://spidercss1.itstrendingnow.com/assets/v1/fonts/NotoSansDevanagariUI-Medium.otf) format("opentype"),url(https://spidercss1.itstrendingnow.com/assets/v1/fonts/NotoSansDevanagariUI-Medium.svg) format("svg");font-weight:400;font-style:normal;font-display:swap}@font-face{font-family:Noto Sans Devanagari;font-style:normal;font-weight:400;font-display:swap;src:url(https://spidercss1.itstrendingnow.com/assets/fonts_v1/NotoSansDevanagari-Regular.eot);src:url(https://spidercss1.itstrendingnow.com/assets/fonts_v1/NotoSansDevanagari-Regular.eot#iefix) format("embedded-opentype"),url(https://spidercss1.itstrendingnow.com/assets/fonts_v1/NotoSansDevanagari-Regular.woff2) format("woff2"),url(https://spidercss1.itstrendingnow.com/assets/fonts_v1/NotoSansDevanagari-Regular.woff) format("woff"),url(https://spidercss1.itstrendingnow.com/assets/fonts_v1/NotoSansDevanagari-Regular.ttf) format("truetype")}@font-face{font-family:Noto Sans Devanagari;font-style:normal;font-weight:700;font-display:swap;src:url(https://spidercss1.itstrendingnow.com/assets/fonts_v1/NotoSansDevanagari-Bold.eot);src:url(https://spidercss1.itstrendingnow.com/assets/fonts_v1/NotoSansDevanagari-Bold.eot#iefix) format("embedded-opentype"),url(https://spidercss1.itstrendingnow.com/assets/fonts_v1/NotoSansDevanagari-Bold.woff2) format("woff2"),url(https://spidercss1.itstrendingnow.com/assets/fonts_v1/NotoSansDevanagari-Bold.woff) format("woff"),url(https://spidercss1.itstrendingnow.com/assets/fonts_v1/NotoSansDevanagari-Bold.ttf) format("truetype")} .hgt50{min-height: 50px;}
html{font-family:NotoSansDevanagariUI-Medium,Helvetica Neue,Helvetica,Arial,sans-serif;-ms-text-size-adjust:100%;-webkit-text-size-adjust:100%}body{font-family:NotoSansDevanagariUI-Medium;margin:0}article,aside,details,figcaption,figure,footer,header,hgroup,main,menu,nav,section,summary{display:block}audio,canvas,progress,video{display:inline-block;vertical-align:baseline}[hidden],template{display:none}a{background-color:transparent}a:active,a:hover{outline:0}table{border-collapse:collapse;border-spacing:0}td,th{padding:0}*{-webkit-box-sizing:border-box;-moz-box-sizing:border-box;box-sizing:border-box}*:before,*:after{-webkit-box-sizing:border-box;-moz-box-sizing:border-box;box-sizing:border-box}figure{margin:0}img{vertical-align:middle}.img-responsive{display:block;max-width:100%;height:auto}ul,ol{margin-top:0;margin-bottom:10px}ul ul,ol ul,ul ol,ol ol{margin-bottom:0}.container{padding-right:15px;padding-left:15px;margin-right:auto;margin-left:auto}@media (min-width:768px){.container{width:750px}}@media (min-width:992px){.container{width:970px}}@media (min-width:1200px){.container{width:1170px}}.row{margin-right:-15px;margin-left:-15px}.row-no-gutters{margin-right:0;margin-left:0}.col-xs-1,.col-sm-1,.col-md-1,.col-lg-1,.col-xs-2,.col-sm-2,.col-md-2,.col-lg-2,.col-xs-3,.col-sm-3,.col-md-3,.col-lg-3,.col-xs-4,.col-sm-4,.col-md-4,.col-lg-4,.col-xs-5,.col-sm-5,.col-md-5,.col-lg-5,.col-xs-6,.col-sm-6,.col-md-6,.col-lg-6,.col-xs-7,.col-sm-7,.col-md-7,.col-lg-7,.col-xs-8,.col-sm-8,.col-md-8,.col-lg-8,.col-xs-9,.col-sm-9,.col-md-9,.col-lg-9,.col-xs-10,.col-sm-10,.col-md-10,.col-lg-10,.col-xs-11,.col-sm-11,.col-md-11,.col-lg-11,.col-xs-12,.col-sm-12,.col-md-12,.col-lg-12{position:relative;min-height:1px;padding-right:15px;padding-left:15px}.col-xs-1,.col-xs-2,.col-xs-3,.col-xs-4,.col-xs-5,.col-xs-6,.col-xs-7,.col-xs-8,.col-xs-9,.col-xs-10,.col-xs-11,.col-xs-12{float:left}.col-xs-12{width:100%}.col-xs-11{width:91.66666667%}.col-xs-10{width:83.33333333%}.col-xs-9{width:75%}.col-xs-8{width:66.66666667%}.col-xs-7{width:58.33333333%}.col-xs-6{width:50%}.col-xs-5{width:41.66666667%}.col-xs-4{width:33.33333333%}.col-xs-3{width:25%}.col-xs-2{width:16.66666667%}.col-xs-1{width:8.33333333%}@media (min-width:768px){.col-sm-1,.col-sm-2,.col-sm-3,.col-sm-4,.col-sm-5,.col-sm-6,.col-sm-7,.col-sm-8,.col-sm-9,.col-sm-10,.col-sm-11,.col-sm-12{float:left}.col-sm-12{width:100%}.col-sm-11{width:91.66666667%}.col-sm-10{width:83.33333333%}.col-sm-9{width:75%}.col-sm-8{width:66.66666667%}.col-sm-7{width:58.33333333%}.col-sm-6{width:50%}.col-sm-5{width:41.66666667%}.col-sm-4{width:33.33333333%}.col-sm-3{width:25%}.col-sm-2{width:16.66666667%}.col-sm-1{width:8.33333333%}}@media (min-width:992px){.col-md-1,.col-md-2,.col-md-3,.col-md-4,.col-md-5,.col-md-6,.col-md-7,.col-md-8,.col-md-9,.col-md-10,.col-md-11,.col-md-12{float:left}.col-md-12{width:100%}.col-md-11{width:91.66666667%}.col-md-10{width:83.33333333%}.col-md-9{width:75%}.col-md-8{width:66.66666667%}.col-md-7{width:58.33333333%}.col-md-6{width:50%}.col-md-5{width:41.66666667%}.col-md-4{width:33.33333333%}.col-md-3{width:25%}.col-md-2{width:16.66666667%}.col-md-1{width:8.33333333%}}.clearfix:before,.clearfix:after,.dl-horizontal dd:before,.dl-horizontal dd:after,.container:before,.container:after,.container-fluid:before,.container-fluid:after,.row:before,.row:after,.form-horizontal .form-group:before,.form-horizontal .form-group:after{display:table;content:" "}.clearfix:after,.dl-horizontal dd:after,.container:after,.container-fluid:after,.row:after,.form-horizontal .form-group:after{clear:both}.center-block{display:block;margin-right:auto;margin-left:auto}.pull-right{float:right !important}.pull-left{float:left !important}.hide{display:none !important}.show{display:block !important}.hidden{display:none !important}h1{font-size:2em;margin:.67em 0}.h1 .small,.h1 small,.h2 .small,.h2 small,.h3 .small,.h3 small,.h4 .small,.h4 small,.h5 .small,.h5 small,.h6 .small,.h6 small,h1 .small,h1 small,h2 .small,h2 small,h3 .small,h3 small,h4 .small,h4 small,h5 .small,h5 small,h6 .small,h6 small{font-weight:400;
html{-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%}*,:after,:before{box-sizing:border-box;padding:0;margin:0}article,aside,details,figcaption,figure,footer,header,hgroup,main,menu,nav,section,summary{display:block}body{font-family:NotoSansDevanagariUI-Medium,Helvetica,sans-serif;background:#f8f8fa;font-size:14px;color:#221f1f}.h1,.h2,.h3,.h4,.h5,.h6,h1,h2,h3,h4,h5,h6{font-family:inherit;font-weight:500;line-height:1.1;color:inherit}li,ul{list-style-type:none;padding:0;margin:0}h1,h2{font-size:24px;font-weight:700}h1,h2,h3{line-height:1.5em}h3{font-size:16px;font-weight:500}a,h1,h1 a,h2,h2 a,h3,h3 a,h4,h4 a,h5,h5 a,h6,h6 a{color:#221f1f}a,a:focus,a:hover{text-decoration:none}a:focus,a:hover{color:#17aada}nav ul li{display:inline-block}@media  only screen and (max-width:736px){.col-xs-12,.col-xs-6{padding-right:10px;padding-left:10px}.col-xs-12 .row,.col-xs-6 .row{margin-left:-10px;margin-right:-10px}.full-column{padding:0!important}.full-column .article-desc,.full-column .auther-time,.full-column .social-div,.full-column h1{padding:0 10px}}.dflt .time-clock span{width:12px;height:12px;margin-right:5px;background-position:0 -30px;display:block;float:left}.white-wrapper{background:#fff}.white-wrapper.pdb32{padding-bottom:32px}.category-name{display:block;font-size:11px;text-align:left;color:#17aada;margin:8px 0 6px}.category-name a{color:#17aada}.time-clock{font-size:11px;color:#ccc;position:absolute;margin:0;line-height:1.1;top:1px}@media  only screen and (max-width:960px){.ad-mb-app.fix_300_250,.ad-mb.fix_300_250,.fix_300_250,.width320.fix_300_250{width:300px!important;height:272px!important;overflow:hidden;position:relative}.shadow,.white-wrapper.shadow{overflow:hidden;box-shadow:0 2px 4px 0 rgba(72,72,72,.1);margin-bottom:4px}.white-wrapper.mrgb8{margin-bottom:8px}.white-wrapper.bgnone{background:0 0}.white-wrapper.bgnone.shadow{box-shadow:0 0}.white-wrapper.bgnone.mrgb8{margin-bottom:0}.white-wrapper.bgnone.pdb32,.white-wrapper.pdnonemb.pdb32{padding-bottom:0}}.oh{overflow:hidden}.center-block{display:block;margin-right:auto;margin-left:auto}.mt-36{margin-top:36px!important}.bdr-b{border-bottom:1px solid #ddd;margin:0 15px 24px}.bdr-t{border-top:1px solid #eee}.bdr-b-dotted{border-bottom:2px dotted #ddd;margin:0 15px 24px}.bdr-b-dotted.mrgb0{margin-bottom:0}.ad-dt.mrgb0{margin-bottom:0!important}@media  only screen and (min-width:992px){.white-wrapper.pdt-15{padding-top:15px!important}}@media  only screen and (max-width:736px){.bdr-b{border-bottom:0;margin-bottom:0}.bdr-b-dotted{border-bottom:0;margin:0}} .read-later{background-position:-75px -116px} .read-later.sel{background-position:-112px -116px}.dflt .fb-icn{background-position:-98px -69px}.dflt .fb-icn,.dflt .tw-icn{width:32px;height:32px;display:inline-block;cursor:pointer}.dflt .tw-icn{background-position:-133px -69px}.dflt .wht-icn{background-position:-168px -69px}.dflt .gplus-icn,.dflt .wht-icn{width:32px;height:32px;display:inline-block;cursor:pointer}.dflt .gplus-icn{background-position:-309px -69px}.socialicn ul li.telegramDv,.socialicn ul li.whtDv{display:none}.mt-10{margin-top:10px!important}.mt-16{margin-top:16px!important}.ctr{text-align:center}.advertisement_wrapper{color:#a8a8a8;padding:15px 10px;text-align:center}.advertisement_wrapper.pd0{padding:0}.advertisement_wrapper.pd5{padding:5px 0}.advertisement_wrapper.pd10{padding:10px}center.vigyapan{height:20px;color:#a8a8a8;font-weight:400;padding:0 0 0 5px;font-size:13px;text-align:center;overflow:hidden;margin-bottom:1px;line-height:1.5}center.vigyapan .removeads{background:#dc2829;color:#fff;font-size:12px;text-align:center;float:right;padding:1px 0 0}center.vigyapan .removeads a{padding:0 7px;color:#fff}center.vigyapan .removeads span{border:solid #fff;border-width:0 2px 2px 0;display:inline-block;width:8px;height:8px;transform:rotate(-45deg);-webkit-transform:rotate(-45deg)}.ad-dt{display:block;margin:0 auto 20px}.ad-mb,.ad-mb-app{display:none}.ad-300,.width300{width:300px;margin:0 auto 20px}.ad-320,.width320{width:320px;margin:0 auto 20px;text-align:center}.ad-990{width:990px}.ad-970,.

.sprite_card {background-image:url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAOIAAACWCAYAAADDo1QAAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAA3RpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tldCBiZWdpbj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+IDx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IkFkb2JlIFhNUCBDb3JlIDcuMS1jMDAwIDc5LmRhYmFjYmIsIDIwMjEvMDQvMTQtMDA6Mzk6NDQgICAgICAgICI+IDxyZGY6UkRGIHhtbG5zOnJkZj0iaHR0cDovL3d3dy53My5vcmcvMTk5OS8wMi8yMi1yZGYtc3ludGF4LW5zIyI+IDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiIHhtbG5zOnhtcE1NPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvbW0vIiB4bWxuczpzdFJlZj0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL3NUeXBlL1Jlc291cmNlUmVmIyIgeG1sbnM6eG1wPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvIiB4bXBNTTpPcmlnaW5hbERvY3VtZW50SUQ9InhtcC5kaWQ6OWM3NDFmYmYtZTgzZC1mYzQyLTg5YWEtNzg4ZmMxZWRmZmE4IiB4bXBNTTpEb2N1bWVudElEPSJ4bXAuZGlkOjhFMjg3NEREN0FBQTExRUM4OUQ2REY3RkFGQjUzQzM3IiB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOjhFMjg3NERDN0FBQTExRUM4OUQ2REY3RkFGQjUzQzM3IiB4bXA6Q3JlYXRvclRvb2w9IkFkb2JlIFBob3Rvc2hvcCAyMi41IChXaW5kb3dzKSI+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjppbnN0YW5jZUlEPSJ4bXAuaWlkOjc1ZTNjZTcyLTBlYzEtYmM0Zi04NTZjLWE1YmQ4NGY3NTk2YyIgc3RSZWY6ZG9jdW1lbnRJRD0ieG1wLmRpZDo5Yzc0MWZiZi1lODNkLWZjNDItODlhYS03ODhmYzFlZGZmYTgiLz4g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

@media  only screen and (min-width:961px){ .scroll_x {overflow: hidden;overflow-x: auto;} .scroll_x::-webkit-scrollbar {width:2px;height:8px} .scroll_x::-webkit-scrollbar-track {-webkit-box-shadow: inset 0 0 6px rgba(0,0,0,0.3);box-shadow: inset 0 0 6px rgba(0,0,0,0.3);} .scroll_x::-webkit-scrollbar-thumb {-webkit-border-radius:10px;border-radius:10px;background:#B0B0B0;-webkit-box-shadow: inset 0 0 6px rgba(0,0,0,0.5);box-shadow: inset 0 0 6px rgba(0,0,0,0.5)} .scroll_x::-webkit-scrollbar-thumb:window-inactive {background:#B0B0B0} }
@media  only screen and (min-width:992px){
#city-rs-tranding-content {min-height:700px}
}
.__main_listing_content.epaper_dropdown {display: table;padding:8px !important;background:#3C3C49;color:#fff;font-size:15px;} .__main_listing_content.epaper_dropdown .image{width:80px;height:80px;line-height:78px;display:table-cell;vertical-align:top;overflow: hidden;background: none;} .__main_listing_content.epaper_dropdown .image img{height: 80px;width:80px;vertical-align: top;display: inline-block;border-radius:5px;border:2px solid #fff} .__main_listing_content.epaper_dropdown .image-caption {height: 100%;position: relative;display: table-cell;padding: 0 0 0 16px;vertical-align:top;} .__main_listing_content.epaper_dropdown h2 {color: #fff;margin: 0px 0 4px;line-height:24px;font-size:18px;font-weight: 500;} .__main_listing_content.epaper_dropdown .epaper_link {color:#ffe500;margin-top:5px;display: inline-block;line-height:14px} .__main_listing_content.epaper_dropdown label {width:100%;display:inline-block;position: relative;font-weight:normal;margin-bottom: 0;font-size:15px;} .__main_listing_content.epaper_dropdown label::after {content: '\203A';width:15px;height:18px;color:#747373;display:block;position: absolute;top:6px;right:8px;z-index:1;transform: rotate(90deg);font-size: 30px;line-height: 12px;text-align: center;pointer-events:none;} .__main_listing_content.epaper_dropdown select {font-size: 14px;line-height: 20px;width: 100%;height:30px;border:0;border-radius: 4px;position: relative;overflow: hidden;cursor:pointer;line-height: 24px;margin: 0;color: #747373;padding: 4px 30px 5px 10px;-webkit-appearance: none;-moz-appearance: none;appearance: none;background:#fff} .__main_listing_content.epaper_dropdown select::-ms-expand {display: none}



.image-caption-text table { width: 100% !important } .image-caption-text table, .image-caption-text table th, .image-caption-text table td { border: 1px solid #e5e5e5; padding: 5px 8px 7px } .lead-gal-detail .lead-gallery .auther-time { opacity: 1; color: #CCEBF5; } .lead-gal-detail .auther-time span { color: #CCEBF5; display: inline-block; margin-right: 0px; font-size: 14px; } .lead-gal-detail .auther-time .authdesc { display: inline-block } .lead-gal-detail .auther-time .authpic { width: 34px; height: 34px; display: inline-block; vertical-align: top } .lead-gal-detail .auther-time .authpic img { width: 100%; height: 100%; border-radius: 50px; border: 2px solid #f3f3f3; } .lead-gal-detail .gallery-caption, .gallery-content .gallery-caption { background: #f8f8fa; padding: 8px; text-align: center; font-size: 14px; color: #626262; } .lead-gal-detail .gallery-caption span, .gallery-content .gallery-caption span { display: inline-block; margin-left: 2px } .gallery-content .gallery-caption { background: none; color: #a5a5a5 } /*f8f8fa*/ .lead-gal-detail .lead-gallery img { max-width: 100% } .leadgal-wrapper { background: #fff; padding-top: 8px } /*Lead Galleries detail page -*/ .lead-gal-detail { position: relative; margin: 0px 0 24px } .lead-gallery a { color: #17aada; } .lead-gal-detail .lead-gallery { width: 100%; position: relative; margin: 0;word-break: break-word; } @media  only screen and (max-width: 736px){ .lead-gal-detail .lead-gallery {width: calc(100% + 20px);margin-left:-10px} } .lead-gal-detail .lead-gallery .image { width:100%;position: relative;text-align: center;margin-bottom:0;height: auto !important;line-height: normal !important; } .lead-gal-detail .lead-gallery .image figure{width:100%;height: 0;padding-top: 56.25%;line-height: normal;position: relative;background-color:#EAEAEA;} .lead-gal-detail .lead-gallery .image figure img, .lead-gal-detail .lead-gallery .image figure iframe { width:100%;height:100%;position: absolute;top: 0;left: 0;border: 0;max-width:100%;object-fit: cover;object-position: center; max-height: none !important; } .lead-gallery .story-detail { background: #101010; padding: 20px 20px 12px } .lead-gal-detail .lead-gallery h1 { font-size: 32px; font-weight: 700; margin: 0; line-height: 40px; color: #fff } .lead-gal-detail .lead-gallery h1 a { color: #fff } .lead-gal-detail .lead-gallery h2, .lead-gal-detail .lead-gallery h3 { font-size: 20px; line-height: 1.4; font-weight: 400; margin: 5px 0px } .lead-gal-detail .lead-gallery .auther-time { color: #fff; display: block; opacity: 0.8; font-size: 13px; font-weight: normal; font-style: normal; font-stretch: normal; line-height: 1.43; letter-spacing: normal; text-align: left; margin-top: 6px } .lead-gal-detail .image-caption-text { font-size: 19px; line-height: 1.5em; padding: 10px 0 20px } .lead-gal-detail .nxtpre-icon .pre { background-position: -140px 0px; left: 0px; right: auto; width: 36px; height: 65px; cursor: pointer; display: inline-block; line-height: normal; position: absolute; z-index: 10; top: 40% } .lead-gal-detail .nxtpre-icon .nxt { background-position: -101px 0px; right: 0px; left: auto; width: 36px; height: 65px; cursor: pointer; display: inline-block; line-height: normal; position: absolute; z-index: 10; top: 40% } .lead-gal-detail .gallery-caption { background: #f8f8fa; padding: 8px; text-align: center; font-size: 14px; color: #626262; } .lead-gallery .image .total-pic { font-size: 12px; text-align: center; padding: 10px 10px 6px; color: #fff; position: absolute; top: 5px; left: 5px; border-radius: 6px; background: rgb(0, 0, 0); background: rgba(0, 0, 0, 0.5); line-height: 1.2; display: inline-block } @media  only screen and (max-width:960px) { .lead-gal-detail .lead-gallery h1 { height: auto } .lead-gal-detail .lead-gallery h1 { height: auto } } @media  only screen and (max-width:736px) { .leadgal-wrapper { background: none; padding-top: 0 } .leadgal-wrapper .innerwrap.detail { background: #fff; padding: 0px 0 0 0px; box-shadow: 0 2px 4px 0 rgba(72, 72, 72, 0.1); margin-bottom: 20px } .lead-gal-detail { position: relativ



@media  only screen and (max-width:320px){ /* for full width ads on 320 resulation */
.col-xs-12 .width320{margin-left:-10px}
}
</style>

<style type="text/css">.customised-sub-menu .bx-controls-direction a.bx-next, .customised-sub-menu .bx-controls-direction a.bx-prev, .election-quote .bx-controls-direction a.bx-next, .election-quote .bx-controls-direction a.bx-prev, .fullview-gal-container .bx-controls-direction a.click-next-story, .highlight-carousel .bx-controls-direction a.bx-next, .highlight-carousel .bx-controls-direction a.bx-prev, .lead-news .bx-controls-direction a.bx-next, .lead-news .bx-controls-direction a.bx-prev, .login-icn a.loginBtn, .rankingkit-container .bx-controls-direction a.bx-next, .rankingkit-container .bx-controls-direction a.bx-prev, .related-candidate .bx-controls-direction a.bx-next, .related-candidate .bx-controls-direction a.bx-prev, .services-carousel .bx-controls-direction a.bx-next, .services-carousel .bx-controls-direction a.bx-prev, .sprite, .topschedule .bx-controls-direction a.bx-next, .topschedule .bx-controls-direction a.bx-prev,.rectangle-slider-container .bx-controls-direction a.bx-next, .rectangle-slider-container .bx-controls-direction a.bx-prev{background-image:url("data:image/png;base64,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
<script>
function getCookieValue(a) {
    var b = document.cookie.match('(^|[^;]+)\\s*' + a + '\\s*=\\s*([^;]+)');
    return b ? b.pop() : '';
}
</script>
<script>
_auw_page_detail = {"author_type":"Organization","story_title":"Latest viral jokes: \u091c\u092c \u092a\u0924\u094d\u0928\u0940 \u0928\u0947 \u092a\u0924\u093f \u092a\u0942\u091b\u093e- \u0924\u0941\u092e \u092e\u0941\u091d\u0938\u0947 \u0915\u093f\u0924\u0928\u093e \u092a\u094d\u092f\u093e\u0930 \u0915\u0930\u0924\u0947 \u0939\u094b, \u091c\u0935\u093e\u092c \u0938\u0941\u0928\u0915\u0930 \u0928\u0939\u0940\u0902 \u0930\u0941\u0915\u0947\u0917\u0940 \u0939\u0902\u0938\u0940","author_name":"Amar Ujala Digital Team","analytics":{"id":"62332503f039295f3c7a3870","type":"story","user_source":"national"},"id":"62332503f039295f3c7a3870","content_partner":"Amar Ujala Digital","story_writer":"Jyoti Mehra","category":"humour","sub_category":"humour","national":"national","notification_title":"\u092e\u091c\u0947\u0926\u093e\u0930 \u091c\u094b\u0915\u094d\u0938-\u091a\u0941\u091f\u0915\u0941\u0932\u0947 \u092a\u0922\u093c\u0928\u0947 \u0915\u0947 \u0932\u093f\u090f \u0938\u092c\u094d\u0938\u0915\u094d\u0930\u093e\u0907\u092c \u0915\u0930\u0947\u0902 \u0905\u092e\u0930 \u0909\u091c\u093e\u0932\u093e","template":"photo-gallery","keywords":["santa banta viral jokes","viral jokes","latest jokes","viral hindi jokes","lot pot kar dene wale chutkule","lot pot karne wale chutkule","hasi se lot pot chutkule","lot pot chutkule hindi me","lot pot chutkule in hindi","\u0932\u094b\u091f \u092a\u094b\u091f \u091a\u0941\u091f\u0915\u0941\u0932\u0947","santa banta","new latest jokes","new latest jokes in hindi 2022","hindi me jokes","husband wife jokes","funny jokes","funny hindi jokes","girlfriend boyfriend jokes","latest jokes in hindi","latest whatsapp joke in hindi","hindi chutkule hd","\u091c\u094b\u0915\u094d\u0938 \u0907\u0928 \u0939\u093f\u0902\u0926\u0940","\u0939\u093f\u0902\u0926\u0940 \u091a\u0941\u091f\u0915\u0941\u0932\u0947","\u091c\u094b\u0915\u094d\u0938",""],"tags":["humour","national","latest jokes","jokes in hindi","jokes"],"tags_slug0":"humour","tags_slug1":"national","tags_slug2":"latest-jokes","tags_slug3":"jokes-in-hindi","tags_slug4":"jokes","request_client":"web","author":"61b9749252e799113a0ea961","refresh":"false"}

_auw_page_detail.logged_in = "false";

var check_logged_on = getCookieValue('_raidu');

if(typeof check_logged_on !=="undefined" && check_logged_on.length >0){
 _auw_page_detail.logged_in = "true";
 _auw_page_detail.sid = check_logged_on;
 }



    var topic = "national";
    let topics  = JSON.parse(localStorage.getItem('auw_topics'));
    topics = topics === null? []:topics;
    if(topic && !topics.includes(topic)){
        topics.push(topic);
        localStorage.setItem('auw_topics', JSON.stringify(topics));
    }
</script>
<script type="text/javascript">
handlerJsUrl = "https://handler.amarujala.com";
fcmJsUrl = "https://fcmapi.amarujala.com";    
ADS_LOAD_SYNC = '1';  
enablePrebid = "disable";
if(typeof AndroidStorage!="undefined"){
	window.Storage=AndroidStorage;
}else{
	window.Storage=window.localStorage;
}
_request_client = 'web';_pwa_app='web';var timerStart = Date.now(); pageAds = {};site_ga_data ={};_cf_device_type = "";
_request_client = 'web';
var googletag = googletag || {};googletag.cmd = googletag.cmd || [];
site_ga_data =[];
_app_adv_status = 'enable';
amarujala_clients = ["dailyhunt","raftaar"];
if(typeof _app_adv_status !=='undefined' && _app_adv_status == 'enable'){
  _allowed_clients = amarujala_clients;
}else{
 _allowed_client = ['iphone','android'];
 _allowed_clients = _allowed_client.concat(amarujala_clients);
}



var is_premium_user = getCookieValue('is_premium_user');

    pageType = 'photo-gallery-article'; //it's compulsary far async ad load
if(typeof _request_client!=='undefined' && _request_client=='web'){
             site_ga_data= [{"id":"UA-28612117-1","name":"main_id","link":"auto"},{"id":"UA-57570453-1","name":"global_id","link":"amarujala.com"}]
    }else{//else if(typeof _request_client!=='undefined' && (_request_client=='android' || _request_client=='iphone')){
      site_ga_data=[{'id':'UA-57570453-1','name':'global_id','link':'amarujala.com'}];
}
if(typeof _auw_page_detail!="undefined" && typeof _auw_page_detail.page!="undefined" && (_auw_page_detail.page=="board-result-2018" || _auw_page_detail.page=="andhra-pradesh-board-result-2018")){
     site_ga_data.push({'id':'UA-28612117-6','name':'result_id','link':'results.amarujala.com'});
}
/*else if(typeof _request_client!=='undefined' && _request_client=='iphone'){
      site_ga_data=[{'id':'UA-28612117-1','name':'main_id','link':'auto'},{'id':'UA-57570453-1','name':'global_id','link':'amarujala.com'},{'id':'UA-62762346-2','name':'iphone_id','link':'iphone'}];
}*/
function pageview_candidate(){
var xmlhttp = new XMLHttpRequest();
var url = '/ajax/comscore-pv?_ts='+Date.now();
xmlhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
        return this.responseText
    }
};
xmlhttp.open("GET", url, true);
xmlhttp.send();
}
function gaTracker(site_ga_data) { (function(i, s, o, g, r, a, m) { i['GoogleAnalyticsObject'] = r; i[r] = i[r] || function() { (i[r].q = i[r].q || []).push(arguments) }, i[r].l = 1 * new Date(); a = s.createElement(o), m = s.getElementsByTagName(o)[0]; a.async = 1; a.src = g; m.parentNode.insertBefore(a, m) })(window, document, 'script', '//www.google-analytics.com/analytics.js', 'ga'); for (ga_data in site_ga_data) { ga('create', site_ga_data[ga_data]['id'], site_ga_data[ga_data]['link'], { 'name': site_ga_data[ga_data]['name'], 'allowLinker': true, 'useAmpClientId': true }); ga(site_ga_data[ga_data]['name'] + '.require', 'linker'); ga(site_ga_data[ga_data]['name'] + '.require', 'displayfeatures'); /* ga custom dimension data */ var ga_cdimension_story = ["story", "feature-story", "photo-gallery", "video", "live", "wiki", "blog","podcast"]; var ga_cdimension_story_template = null; var ga_cdimension_story_template_index = null; if(typeof _auw_page_detail!='undefined' && typeof _auw_page_detail.template !='undefined' && _auw_page_detail.template!=null){ ga_cdimension_story_template = _auw_page_detail.template; ga_cdimension_story_template_index = ga_cdimension_story.indexOf(ga_cdimension_story_template); } /* for (ga_data in site_ga_data){ */ if( ga_cdimension_story_template_index >=0 ){ var article_user_name = "Jyoti Mehra"; if( article_user_name.trim().length >0 ){ ga(site_ga_data[ga_data]['name'] + '.set', 'dimension4', article_user_name);/*Custom dimension to track */ } var story_tags_for_dimension6 = "humour, national, latest jokes, jokes in hindi, jokes"; if(typeof ga_cdimension_story_template!='undefined' && ga_cdimension_story_template=='video'){ story_tags_for_dimension6 = ""; } ga(site_ga_data[ga_data]['name'] + '.set', 'dimension6', story_tags_for_dimension6);/*Custom dimension to track */   ga(site_ga_data[ga_data]['name'] + '.set', 'contentGroup1', 'allstories');/* GA Content Grouping tags */   if(typeof _auw_page_detail!='undefined' && typeof _auw_page_detail.content_partner !='undefined' && _auw_page_detail.content_partner!=null){ ga(site_ga_data[ga_data]['name'] + '.set', 'dimension2', _auw_page_detail.content_partner ); /* Custom dimension to track */ } } if (typeof is_premium_user != 'undefined' && is_premium_user==1) { ga(site_ga_data[ga_data]['name'] + '.set', 'dimension3', 'Paid'); /*Custom dimension to track */ }else{ ga(site_ga_data[ga_data]['name'] + '.set', 'dimension3', 'Free'); /* Custom dimension to track */ } /*} */ /* ga custom dimension data */ ga(site_ga_data[ga_data]['name'] + '.send', 'pageview'); } /*ga('require', 'autotrack');ga('auglobal.require', 'autotrack');*/ } function gaTrackPageViews(path) { for (ga_data in site_ga_data) { ga(site_ga_data[ga_data]['name'] + '.set', { page: path }); ga(site_ga_data[ga_data]['name'] + '.send', 'pageview'); }; if(typeof COMSCORE !='undefined' && typeof COMSCORE.beacon !== 'undefined'){ COMSCORE.beacon({ c1: "2", c2: "21916725" });pageview_candidate(); } }; function gaTrackEvent(eventCategory, eventAction, eventLabel, eventValue, interaction) { if (typeof eventCategory == 'undefined') { eventCategory = "Amarujala-"; }else{ eventCategory = "Amarujala-"+eventCategory; }; if (typeof eventAction == 'undefined') { eventAction = "default"; }; if (typeof eventLabel == 'undefined') { eventLabel = null; }; if(typeof eventValue == 'undefined'){ eventValue = null; }; if(typeof interaction == 'undefined'){ interaction = false; }; fields = { hitType: 'event', eventCategory: eventCategory, eventAction: eventAction, eventLabel: eventLabel, eventValue: eventValue, nonInteraction:interaction }; for (ga_data in site_ga_data) { ga(site_ga_data[ga_data]['name'] + ".send", fields); } };
gaTracker(site_ga_data);


            
function is_mobile(){if (! navigator.userAgent.match(/Android/i) && ! navigator.userAgent.match(/webOS/i) && ! navigator.userAgent.match(/iPhone/i) &&! navigator.userAgent.match(/iPod/i) && ! navigator.userAgent.match(/iPad/i) && ! navigator.userAgent.match(/Blackberry/i) && ! navigator.userAgent.match(/UCWEB/i)){return false;} else{return true;}};
//for jio site
_allowed_clients_jio = ['iphone','android'];
if(typeof _request_client!=='undefined' && _allowed_clients_jio.indexOf(_request_client) ===-1){
    if(typeof window.innerWidth !='undefined' && window.innerWidth <290){
        var current_url = location.href;
        if((typeof _auw_page_detail['sub_category']=='undefined' ||  _auw_page_detail['sub_category']!='cricket-scorecards') && (typeof _auw_page_detail['page']=='undefined' || _auw_page_detail['page']!='election')){
            location.href = current_url.replace('.com','.com/jio');
        }
    }
}
//use for check gutter enable or disable
auw_gutter_ad=false;
</script>
<!--Dont remove below code. It's for IE less than 9 [if lt IE 9]>
<script>
  var e = ("article,aside,audio,canvas,datalist,details," +
    "figure,footer,header,mark,menu,nav," +
    "progress,section,time,video").split(',');
  for (var i = 0; i < e.length; i++) {
    document.createElement(e[i]);
  }
</script>
<![endif]-->
<script>

if(typeof _auw_page_detail=="undefined"){
    _auw_page_detail = {};
}

var tags = document.cookie.split(';').filter(function(c){return c.trim().match("_au_camp_")}).map(function(d){return d.trim().split("=")[0]});

if ( tags && tags.length != 0 ) {

    for( var i_camp = 0; i_camp < tags.length; i_camp++ ) {
        
        if( typeof tags[i_camp] != "undefined" ) {
            _auw_page_detail[tags[i_camp]] = true;
        }
    }
}
</script>
</head>
<body class="lite gutter-ads ">
<div class="mini-brwsr-msg" style="position:relative;padding:10px 3%; text-align: center; color:#c70514;display:none;background:#f5f5f5">
बेहतर अनुभव के लिए अपनी सेटिंग्स में जाकर हाई मोड चुनें।
</div>
<script>
    
    googletag.cmd.push(function() {
    if(typeof is_mobile !='undefined' && !is_mobile()){
               //ads_desk_slot1=googletag.defineSlot('/188001951/Amarujala-Desktop-Photogallery-970x90-1', [970, 90], 'div-gpt-ad-1507187614635-5').setTargeting('test', 'lazyload').addService(googletag.pubads());
        ads_desk_slot1=googletag.defineSlot('/188001951/Amarujala-Desktop-Photogallery-728x90-Top', [728, 90], 'div-gpt-ad-1516602366814-1').setTargeting('test', 'lazyload').addService(googletag.pubads());
        ads_desk_slot2=googletag.defineSlot('/188001951/Amarujala-Desktop-Photogallery-300x250-1', [300, 250], 'div-gpt-ad-1507187614635-0').setTargeting('test', 'lazyload').addService(googletag.pubads());
       // ads_desk_slot3=googletag.defineSlot('/188001951/Amarujala-Desktop-Photogallery-300x250-2', [300, 250], 'div-gpt-ad-1507187614635-1').setTargeting('test', 'lazyload').addService(googletag.pubads());
        //ads_desk_slot4=googletag.defineSlot('/188001951/Amarujala-Desktop-Photogallery-728x90', [728, 90], 'div-gpt-ad-1513751292715-0').setTargeting('test', 'lazyload').addService(googletag.pubads());
       // ads_desk_slot4=googletag.defineSlot('/188001951/Amarujala-Desktop-Photogallery-600x300', [[300, 250], [600, 300]], 'div-gpt-ad-1544183048069-0').setTargeting('test', 'lazyload').addService(googletag.pubads());
       // ads_desk_slot5=googletag.defineSlot('/188001951/Amarujala-Desktop-Photogallery-970x90-2', [970, 90], 'div-gpt-ad-1507187614635-6').setTargeting('test', 'lazyload').addService(googletag.pubads());
       // ads_desk_slot6=googletag.defineSlot('/188001951/Amarujala-Desktop-Photogallery-300x250-3', [300, 250], 'div-gpt-ad-1507187614635-2').setTargeting('test', 'lazyload').addService(googletag.pubads());
      //  googletag.defineSlot('/188001951/Amarujala_Desktop_Photogallery_1x1', [1.0, 1.0], 'div-gpt-ad-1528716016177-0').setTargeting('test', 'lazyload').addService(googletag.pubads());
        googletag.defineSlot('/188001951/Amarujala-Desktop-ROS-160x600-RHS', [160, 600], 'div-gpt-ad-1543487812772-0').setTargeting('test', 'lazyload').addService(googletag.pubads());
        googletag.defineSlot('/188001951/Amarujala-Desktop-ROS-160x600-LHS', [160, 600], 'div-gpt-ad-1543487470665-0').setTargeting('test', 'lazyload').addService(googletag.pubads());
        //googletag.defineSlot('/188001951/Amarujala_Desktop_ROS1_1x1', [1, 1], 'div-gpt-ad-1547466217799-0').setTargeting('test', 'lazyload').addService(googletag.pubads());
        //googletag.defineSlot('/188001951/Amarujala_Desktop_ROS2_1x1', [1, 1], 'div-gpt-ad-1552979597453-0').setTargeting('test', 'lazyload').addService(googletag.pubads());
                googletag.defineSlot('/188001951/Amarujala-Desktop-Photogallery-970x250-Top', [970, 250], 'div-gpt-ad-1576578063620-0').setTargeting('test', 'lazyload').addService(googletag.pubads());
                            //googletag.defineSlot('/188001951/AmarUjala_Desktop_1x1_3', [1, 1], 'div-gpt-ad-1577363043021-0').setTargeting('test', 'lazyload').addService(googletag.pubads());
        //googletag.defineSlot('/188001951/Amarujala_Desktop_1x1_5', [1, 1], 'div-gpt-ad-1600502198770-0').setTargeting('test', 'lazyload').addService(googletag.pubads());
         googletag.defineSlot('/188001951/Amarujala-Desktop-Photogallery-300x250-6', [300, 250], 'div-gpt-ad-1635518702450-0').setTargeting('test', 'lazyload').addService(googletag.pubads());
         googletag.defineSlot('/188001951/Amarujala-Desktop-Photogallery-300x250-7', [300, 250], 'div-gpt-ad-1635518727070-0').setTargeting('test', 'lazyload').addService(googletag.pubads());
    }else{
        
        ads_mob_slot1=googletag.defineSlot('/188001951/Amarujala-Mobile-Photogallery-300x250-1', [300, 250], 'div-gpt-ad-1507187737510-0').setTargeting('test', 'lazyload').addService(googletag.pubads());
        ads_mob_slot2=googletag.defineSlot('/188001951/Amarujala-Mobile-Photogallery-300x250-2', [[300, 250],[300,600]], 'div-gpt-ad-1507187737510-1').setTargeting('test', 'lazyload').addService(googletag.pubads());
        //ads_mob_slot3=googletag.defineSlot('/188001951/Amarujala-Mobile-Photogallery-300x250-3', [[300, 250],[300,600]], 'div-gpt-ad-1507187737510-2').setTargeting('test', 'lazyload').addService(googletag.pubads());
        //ads_mob_slot4=googletag.defineSlot('/188001951/Amarujala-Mobile-Photogallery-300x250-4', [300, 250], 'div-gpt-ad-1507187737510-3').setTargeting('test', 'lazyload').addService(googletag.pubads());
        //ads_mob_slot5=googletag.defineSlot('/188001951/Amarujala-Mobile-Photogallery-300x250-5', [300, 250], 'div-gpt-ad-1507187737510-4').setTargeting('test', 'lazyload').addService(googletag.pubads());
                        //googletag.defineSlot('/188001951/AmarUjala_Mobile_1x1_3', [1, 1], 'div-gpt-ad-1577363395379-0').setTargeting('test', 'lazyload').addService(googletag.pubads());
                //googletag.defineSlot('/188001951/Amarujala_Mob_1x1_5', [1, 1], 'div-gpt-ad-1600502280126-0').setTargeting('test', 'lazyload').addService(googletag.pubads());
        
        recommnded_ads_adslot_mob_300x250 = googletag.defineSlot('/188001951/Amarujala_EndOfStory_300x250', [300, 250], 'div-gpt-ad-1635325222211-0').setTargeting('test', 'lazyload').addService(googletag.pubads());
        googletag.defineSlot('/188001951/Amarujala-Mobile-Photogallery-300x250-6', [300, 250], 'div-gpt-ad-1635518596910-0').setTargeting('test', 'lazyload').addService(googletag.pubads());
        googletag.defineSlot('/188001951/Amarujala-Mobile-Photogallery-300x250-7', [300, 250], 'div-gpt-ad-1635518631921-0').setTargeting('test', 'lazyload').addService(googletag.pubads());
        if (typeof is_premium_user == 'undefined' || is_premium_user == null || is_premium_user==0) {
var visited_webint_count = au_webint_count();
if(typeof visited_webint_count !="undefined" && visited_webint_count >= 2){
interstitialSlot = googletag.defineOutOfPageSlot('188001951/Web_Interstitial',googletag.enums.OutOfPageFormat.INTERSTITIAL);
// Slot returns null if the page or device does not support interstitials.
if (interstitialSlot) {
interstitialSlot.addService(googletag.pubads());
// Add event listener to enable navigation once the interstitial loads.
// If this event doesn't fire, try clearing local storage and refreshing
// the page.
googletag.pubads().addEventListener('slotOnload', function (event) {
if (interstitialSlot === event.slot) {
console.log('interstitialSlot loaded');
}
});
} } } 

    
    }
    googletag.pubads().enableSingleRequest();
    googletag.pubads().collapseEmptyDivs();
    if(!ADS_LOAD_SYNC){googletag.pubads().disableInitialLoad();}
    googletag.pubads().enableLazyLoad({
          // Fetch slots within 5 viewports.
          fetchMarginPercent: 500,
          // Render slots within 2 viewports.
          renderMarginPercent: 200,
          // Double the above values on mobile, where viewports are smaller
          // and users tend to scroll faster.
          mobileScaling: 2.0
    });
    googletag.enableServices();
    if(typeof _auw_page_detail !='undefined' && typeof _auw_page_detail =="object"){
                Object.keys(_auw_page_detail).forEach(function(key) {
                    //console.log(key, _auw_page_detail[key]);
                    if(key != null && key !='' && key!=""){
                        if(key != null && key.length>0 && _auw_page_detail[key]!=null && _auw_page_detail[key].length>0){
                            googletag.pubads().setTargeting(key, _auw_page_detail[key]);
                        };
                    };
                     
                 });
    };
  });
   
</script>"""

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
    port = 80
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

