from urllib2 import Request, urlopen, HTTPError
from HTMLParser import HTMLParser
import glob
import mimetypes
import os
import re
import threading
import hexchat

__module_name__ = "Link Title"
__module_author__ = "PDog"
__module_version__ = "0.5"
__module_description__ = "Display website title when a link is posted in chat"

try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    hexchat.prnt("\002Link Title\002: Please install python-BeautifulSoup")
    hexchat.command("TIMER 0.1 PY UNLOAD {0}".format(__module_name__))

# TODO: Deal with threading delay, Python 3 compat, handle encoding properly <PDog>

events = ("Channel Message", "Channel Action",
          "Channel Msg Hilight", "Channel Action Hilight")

def find_yt_script():
    script_path = os.path.join(hexchat.get_info("configdir"),
                               "addons", "get-youtube-video-info.py")

    if glob.glob(script_path):
        return re.compile("https?://(?!(w{3}\.)?youtu\.?be(\.|/))")
    else:
        return re.compile("https?://")

def mimetype(url):
    mimetype = mimetypes.guess_type(url)

    if mimetype[0]:
        split_type = mimetype[0].split("/")
        return split_type[0]
    else:
        return mimetype[0]

def get_title(url, chan, nick):
    mtype = mimetype(url)
    
    if mtype == "text" or not mtype:
        req = Request(url)

        try:
            response = urlopen(req)
            html_doc = response.read().decode("utf-8", "ignore")
            response.close()
            soup = BeautifulSoup(html_doc)
            title = HTMLParser().unescape(soup.title.string[:431])
            msg = u"\0033\002::\003 Title:\002 {0} " + \
                  u"\0033\002::\003 URL:\002 \00318\037{1}\017 " + \
                  u"\0033\002::\003 Posted by:\002 {2} " + \
                  u"\0033\002::\002"
            msg = msg.format(title, url, nick)
            msg = msg.encode("utf-8")
            # Weird context and timing issues with threading, hence:
            hexchat.command("TIMER 0.1 DOAT {0} ECHO {1}".format(chan, msg))
        except HTTPError as e:
            msg = "\0033\002::\003 Title:\002 {0}: {1} " + \
                  "\0033\002::\003 URL:\002 \00318\037{2}\017 " + \
                  "\0033\002::\003 Posted by:\002 {3} " + \
                  "\0033\002::\002"
            msg = msg.format(str(e.code), e.reason, url, nick)
            hexchat.command("TIMER 0.1 DOAT {0} ECHO {1}".format(chan, msg))

def event_cb(word, word_eol, userdata):
    chan = hexchat.get_info("channel")
    
    for w in word[1].split():
        stripped_word = hexchat.strip(w, -1, 3)
        
        if find_yt_script().match(stripped_word):
            url = stripped_word

            if url.endswith(","):
                url = url[:-1]
                
            threading.Thread(target=get_title, args=(url, chan, word[0])).start()

    return hexchat.EAT_NONE
            

for event in events:
    hexchat.hook_print(event, event_cb)

hexchat.prnt(__module_name__ + " version " + __module_version__ + " loaded")
