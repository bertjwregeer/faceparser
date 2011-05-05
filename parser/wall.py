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

import sys

from HTMLParser import HTMLParser
from collections import deque

class _parserStateMachine():
    def __init__(self):
        self.handlers = {
                "div": (self.start_div, self.end_div),
                "span": (self.start_span, self.end_span),
                }

        self.data_handlers = deque()

    def get_handlers(self):
        return self.handlers

    def start_div(self, tag, attrs):
        for (name, val) in attrs:
            if name == 'class':
                if val == 'feedentry':
                    # Any entry on our wall is a feedentry ... no difference between ours or others posts!
                    pass
                elif val == 'timerow':
                    # Contains the lock icon, and the time this post was made.
                    pass
                elif val == 'comments':
                    # Contains all of the comments
                    pass
                elif val == 'comment':
                    # Contains a single comment
                    pass
                elif val == 'comment like':
                    # Contains the amount of likes on our wall post
                    pass
                elif val == 'tabwall':
                    # We are now parsing the actual wall data...
                    pass
                elif val == 'downloadnotice':
                    # Contains the date this data dump was downloaded
                    pass
                else:
                    print >> sys.stderr, "Found as of yet unknown class name: div:%s" % val

    def end_div(self, tag):
        pass

    def start_span(self, tag, attrs):
        for (name, val) in attrs:
            if name == 'class':
                if val == 'profile':
                    pass
                elif val == 'time':
                    pass
                else:
                    print >> sys.stderr, "Found as of yet unknown class name: span:%s" % val
                pass

    def end_span(self, tag):
        pass



class facebookWallParser(HTMLParser):
    """Parse the Facebook backup wall.html file"""

    def __init__(self, *args, **kw):
        HTMLParser.__init__(self, *args, **kw)

        self.state_machine = _parserStateMachine()
        self.handlers = self.state_machine.get_handlers()

    def handle_starttag(self, tag, attrs):
        if tag in self.handlers:
            self.handlers[tag][0](tag, attrs)

    def handle_endtag(self, tag):
        if tag in self.handlers:
            self.handlers[tag][1](tag)
