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

from bark import format
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

    @mock.patch.dict(format.Format._conversion_cache)
    def test_basic(self):
        stack = construct(basic="%m %U%q %H -> %s %B")
        req = webob.Request.blank('/sample/path?i=j')
        resp = req.get_response(stack)

        msgs = MemoryHandler.get('basic')

        self.assertEqual(msgs, ['GET /sample/path?i=j HTTP/1.0 -> 200 19'])

    @mock.patch.dict(format.Format._conversion_cache)
    def test_proxy(self):
        proxies = {
            'header': 'X-FORWARDED-FOR',
            'proxies': 'internal(10.5.23.18)',
        }
        stack = construct(proxies=proxies, proxy="%a %{c}a")

        req = webob.Request.blank('/sample/path?i=j')
        resp = req.get_response(stack)

        msgs = MemoryHandler.get('proxy')
        MemoryHandler.clear('proxy')

        self.assertEqual(msgs, ['- -'])

        req = webob.Request.blank('/sample/path?i=j')
        req.environ['REMOTE_ADDR'] = '10.3.21.18'
        resp = req.get_response(stack)

        msgs = MemoryHandler.get('proxy')
        MemoryHandler.clear('proxy')

        self.assertEqual(msgs, ['10.3.21.18 10.3.21.18'])

        req = webob.Request.blank('/sample/path?i=j')
        req.environ['REMOTE_ADDR'] = '10.3.21.18'
        req.headers['x-forwarded-for'] = '10.5.23.18'
        resp = req.get_response(stack)

        msgs = MemoryHandler.get('proxy')
        MemoryHandler.clear('proxy')

        self.assertEqual(msgs, ['10.3.21.18 10.3.21.18'])

        req = webob.Request.blank('/sample/path?i=j')
        req.environ['REMOTE_ADDR'] = '10.5.23.18'
        req.headers['x-forwarded-for'] = '10.3.21.18'
        resp = req.get_response(stack)

        msgs = MemoryHandler.get('proxy')
        MemoryHandler.clear('proxy')

        self.assertEqual(msgs, ['10.3.21.18 10.5.23.18'])

    @mock.patch.dict(format.Format._conversion_cache)
    def test_proxy_chain(self):
        proxies = {
            'header': 'X-Forwarded-For',
            'proxies': ('internal(10.5.23.1), internal(10.5.23.2), '
                        'internal(10.5.23.3), internal(10.5.23.4)'),
        }
        stack = construct(proxies=proxies,
                          chain=("%a %{c}a %{remoteip-proxy-ip-list}n "
                                 "%{x-forwarded-for}i"))

        req = webob.Request.blank('/sample/path?i=j')
        req.environ['REMOTE_ADDR'] = '10.5.23.1'
        req.headers['x-forwarded-for'] = (
            '10.5.23.7,10.5.23.6,10.5.23.5,10.5.23.4,10.5.23.3,10.5.23.2')
        resp = req.get_response(stack)

        msgs = MemoryHandler.get('chain')

        self.assertEqual(msgs, [
            '10.5.23.5 10.5.23.1 10.5.23.4,10.5.23.3,10.5.23.2,10.5.23.1 '
            '10.5.23.7,10.5.23.6'
        ])
