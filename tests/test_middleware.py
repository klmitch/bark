# Copyright 2012 Rackspace
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

import mock
import unittest2

from bark import middleware


class BarkMiddlewareTest(unittest2.TestCase):
    def test_init(self):
        mid = middleware.BarkMiddleware('app', 'handlers', 'proxies')

        self.assertEqual(mid.app, 'app')
        self.assertEqual(mid.handlers, 'handlers')
        self.assertEqual(mid.proxies, 'proxies')

    def test_call_noproxies(self):
        handlers = {
            'log1': (mock.Mock(**{
                'prepare.return_value': 'log1',
                'convert.return_value': 'result1',
            }), mock.Mock()),
            'log2': (mock.Mock(**{
                'prepare.return_value': 'log2',
                'convert.return_value': 'result2',
            }), mock.Mock()),
        }
        request = mock.Mock(**{'get_response.return_value': 'response'})

        mid = middleware.BarkMiddleware('app', handlers, None)

        result = mid(request)

        handlers['log1'][0].prepare.assert_called_once_with(request)
        handlers['log2'][0].prepare.assert_called_once_with(request)
        request.get_response.assert_called_once_with('app')
        handlers['log1'][0].convert.assert_called_once_with(
            request, 'response', 'log1')
        handlers['log1'][1].assert_called_once_with('result1')
        handlers['log2'][0].convert.assert_called_once_with(
            request, 'response', 'log2')
        handlers['log2'][1].assert_called_once_with('result2')
        self.assertEqual(result, 'response')

    def test_call_withproxies(self):
        proxies = mock.Mock()
        handlers = {
            'log1': (mock.Mock(**{
                'prepare.return_value': 'log1',
                'convert.return_value': 'result1',
            }), mock.Mock()),
            'log2': (mock.Mock(**{
                'prepare.return_value': 'log2',
                'convert.return_value': 'result2',
            }), mock.Mock()),
        }
        request = mock.Mock(**{'get_response.return_value': 'response'})

        mid = middleware.BarkMiddleware('app', handlers, proxies)

        result = mid(request)

        proxies.assert_called_once_with(request)
        handlers['log1'][0].prepare.assert_called_once_with(request)
        handlers['log2'][0].prepare.assert_called_once_with(request)
        request.get_response.assert_called_once_with('app')
        handlers['log1'][0].convert.assert_called_once_with(
            request, 'response', 'log1')
        handlers['log1'][1].assert_called_once_with('result1')
        handlers['log2'][0].convert.assert_called_once_with(
            request, 'response', 'log2')
        handlers['log2'][1].assert_called_once_with('result2')
        self.assertEqual(result, 'response')


class BarkFilterTest(unittest2.TestCase):
    @mock.patch('ConfigParser.SafeConfigParser')
    @mock.patch('bark.proxy.ProxyConfig')
    @mock.patch('bark.format.Format.parse')
    @mock.patch('bark.handlers.get_handler')
    @mock.patch.object(middleware, 'BarkMiddleware', return_result='mid')
    def test_noconf(self, mock_BarkMiddleware, mock_get_handler, mock_parse,
                    mock_ProxyConfig, mock_SafeConfigParser):
        filt = middleware.bark_filter({})

        self.assertFalse(mock_SafeConfigParser.called)
        self.assertFalse(mock_ProxyConfig.called)
        self.assertFalse(mock_parse.called)
        self.assertFalse(mock_get_handler.called)
        self.assertFalse(mock_BarkMiddleware.called)

        mid = filt('app')

        mock_BarkMiddleware.assert_called_once_with('app', {}, None)
