###
 # Copyright (c) 2011 Bert JW Regeer <bertjw@regeer.org>;
 # 
 # Permission to use, copy, modify, and distribute this software for any
 # purpose with or without fee is hereby granted, provided that the above
 # copyright notice and this permission notice appear in all copies.
 # 
 # THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 # WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 # MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 # ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 # WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 # ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 # OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
###

# File: wall.py
# Author: Bert JW Regeer <bertjw@regeer.org>
# Created: 2011-05-04 

""" Facebook backup wall.html parser

This parses the Facebook wall.html file into the following structure:

    { "profile": <Profile name of creator>,
      "data": <text version of all of the data in the entry, such as status updates or messages left on your wall>,
      "datetime": <Month dd, yyyy at hh:mm>
      "comments":
                [
                    { "profile": <Profile name of creator>,
                      "data": <text versin of all of the data in the entry>,
                      "datetime": <Month dd, yyyy at hh:mm>
                    }
                ], # optional, and if it exists, does not mean there are comments
      "likes": <x people like this>, # optional
      "type": <text, link> # Differentiates between a link posted to the wall, or just text
    }

"""
import sys

from HTMLParser import HTMLParser
from collections import deque

class _parserStateMachine():
    def __init__(self):
        self.handlers = {
                "div": (self.start_div, self.end_tag),
                "span": (self.start_span, self.end_tag),
                "br": (self.handle_br, None),
                "img": (lambda data, attrs: None, None), # We really just don't care...
                }

        self.data_handlers = deque()
        self.parse_stack = deque()
        self.feedentry = 0
        self.parsed = []
        self.parsing = {}

    def get_handlers(self):
        return self.handlers

    def get_data_handler(self):
        if self.data_handlers:
            if self.data_handlers[0][0]:
                return self.data_handlers[0][0]

        return lambda data: None

    def data_feedentry(self, data):
        if "data" in self.parsing:
            self.parsing["data"] += data
        else:
            self.parsing["data"] = data

    def data_profile(self, data):
        self.parsing["profile"] = data

    def data_time(self, data):
        self.parsing["datetime"] = data

    def end_feedentry(self):
        # Strip the extra \n's from the Wall "data" and from the comment "data".
        if "data" in self.parsing:
            self.parsing["data"] = self.parsing["data"].strip()

        if "comments" in self.parsing:
            for comment in self.parsing["comments"]:
                comment["data"] = comment["data"].strip()

        print self.parsing
        self.parsed.append(self.parsing)
        self.parsing = {}

    def end_comments(self):
        sofar = self.parse_stack.pop()
        sofar["comments"] = self.parsing
        self.parsing = sofar

    def end_comment(self):
        sofar = self.parse_stack.pop()
        sofar.append(self.parsing)
        self.parsing = sofar

    def data_likes(self, data):
        self.parse_stack[-1]["likes"] = data

    def start_div(self, tag, attrs):
        # We have some divs without any class attributes. Thanks Facebook!
        # Note: most of these are the text that was fetched from a remote website, and comes right after
        # a table which has the classname "walllink" ...
        if len(attrs) == 0:
            self.data_handlers.appendleft((None, None))

        for (name, val) in attrs:
            if name == 'class':
                if val == 'feedentry':
                    # Any entry on our wall is a feedentry ... no difference between ours or others posts!
                    self.data_handlers.appendleft((self.data_feedentry, self.end_feedentry))
                    self.feedentry += 1

                elif val == 'timerow':
                    # Contains the lock icon, and the time this post was made.
                    self.data_handlers.appendleft((None, None))

                elif val == 'comments':
                    # Contains all of the comments

                    # We want a list of comments, so we move the current parsed stuff to a queue
                    # so that we can reset self.parsing to an empty list when we encounter a comment
                    # it will be added to the stack, and self.parsing will be set back to {} so that
                    # the rest of the data can be added much like a normal feed entry, we unwind the stack
                    # in the end_comments() and end_comment() funtions, so we build up an entire feed entry
                    self.parse_stack.append(self.parsing)
                    self.parsing = []
                    self.data_handlers.appendleft((None, self.end_comments))

                elif val == 'comment':
                    # Contains a single comment
                    self.parse_stack.append(self.parsing)
                    self.parsing = {}
                    self.data_handlers.appendleft((self.data_feedentry, self.end_comment))

                elif val == 'comment like':
                    # Contains the amount of likes on our wall post
                    self.data_handlers.appendleft((self.data_likes, None))

                elif val == 'tabwall':
                    # We are now parsing the actual wall data...
                    self.data_handlers.appendleft((None, None))

                elif val == 'downloadnotice':
                    # Contains the date this data dump was downloaded
                    self.data_handlers.appendleft((None, None))

                else:
                    self.data_handlers.appendleft((None, None))
                    print >> sys.stderr, "Found as of yet unknown class name: div:%s" % val

    def start_span(self, tag, attrs):
        for (name, val) in attrs:
            if name == 'class':
                if val == 'profile':
                # Contains the profile name who left the item behind in our feed
                    self.data_handlers.appendleft((self.data_profile, None))

                elif val == 'time':
                # Contains the time the item was added to our wall
                    self.data_handlers.appendleft((self.data_time, None))

                else:
                    self.data_handlers.appendleft((None, None))
                    print >> sys.stderr, "Found as of yet unknown class name: span:%s" % val
                pass

    def handle_br(self, tag, attrs):
        self.data_feedentry('\n')


    def end_tag(self, tag):
        if tag not in self.handlers:
            return

        if self.data_handlers:
            if self.data_handlers[0][1]:
                self.data_handlers[0][1]()

            self.data_handlers.popleft()

class facebookWallParser(HTMLParser):
    """Parse the Facebook backup wall.html file"""

    def __init__(self, *args, **kw):
        HTMLParser.__init__(self, *args, **kw)

        self.state_machine = _parserStateMachine()
        self.handlers = self.state_machine.get_handlers()

    def handle_starttag(self, tag, attrs):
        if tag in self.handlers:
            self.handlers[tag][0](tag, attrs)
        else:
            print >> sys.stderr, "Unknown tag: %s" % tag

    def handle_endtag(self, tag):
        if tag in self.handlers:
            if self.handlers[tag][1]:
                self.handlers[tag][1](tag)

    def handle_data(self, data):
        self.state_machine.get_data_handler()(data)

    def handle_entityref(self, name):
        # I would really have hoped that the HTMLParser class would do something similar itself ...
        entity = None

        if name == 'quot':
           entity = '"'
        elif name == 'lt':
            entity = '<'
        elif name == 'gt':
            entity = '>'
        elif name == 'amp':
            entity = '&'

        if entity:
            self.state_machine.get_data_handler()(entity)
        else:
            print >> sys.stderr, "Unknown entity: %s" % name
