# Copyright 2013 Rackspace
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import time

import mock
import unittest2
import webob
import webob.dec

from bark import middleware


# First, need a memory handler
class MemoryHandler(object):
    _log_messages = {}

    @classmethod
    def get(cls, logname):
        return cls._log_messages.get(logname, [])

    @classmethod
    def clear(cls, logname=None):
        if logname:
            cls._log_messages[logname] = []
        else:
            for logname in cls._log_messages:
                cls._log_messages[logname] = []

    def __init__(self, name, logname):
        self.logname = logname
        self._log_messages.setdefault(logname, [])

    def __call__(self, msg):
        self._log_messages[self.logname].append(msg)


# Next, need an application
class Application(object):
    def __init__(self, delay):
        self.delay = delay

    @webob.dec.wsgify
    def __call__(self, request):
        if self.delay:
            time.sleep(self.delay)

        return "This is a response."


# Now, construct a mock WSGI stack
def construct(delay=None, proxies=None, **kwargs):
    # Build the configuration
    local_conf = {}
    for logname, format in kwargs.items():
        local_conf['%s.format' % logname] = format
        local_conf['%s.type' % logname] = 'memory'

    # Add proxy information
    if proxies:
        for key, value in proxies.items():
            local_conf['proxies.%s' % key] = value

    # Construct the filter
    with mock.patch('bark.handlers._lookup_handler',
                    return_value=MemoryHandler):
        filt = middleware.bark_filter({}, **local_conf)

    # Construct the application
    app = Application(delay=delay)

    # Return the stack
    return filt(app)


class BarkFunctionTest(unittest2.TestCase):
    def setUp(self):
        MemoryHandler.clear()

    def tearDown(self):
        MemoryHandler.clear()

    def test_basic(self):
        stack = construct(basic="%m %U%q %H -> %s %B")
        req = webob.Request.blank('/sample/path?i=j')
        resp = req.get_response(stack)

        msgs = MemoryHandler.get('basic')

        self.assertEqual(msgs, ['GET /sample/path?i=j HTTP/1.0 -> 200 19'])
