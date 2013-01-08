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


class TestException(Exception):
    pass


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


def missing_handler(name, logname, args):
    if logname == 'log1':
        raise TestException("failure")
    return name


class BarkFilterTest(unittest2.TestCase):
    @mock.patch.object(middleware.LOG, 'warn')
    @mock.patch('ConfigParser.SafeConfigParser')
    @mock.patch('bark.proxy.ProxyConfig')
    @mock.patch('bark.format.Format.parse')
    @mock.patch('bark.handlers.get_handler')
    @mock.patch.object(middleware, 'BarkMiddleware', return_value='mid')
    def test_noconf(self, mock_BarkMiddleware, mock_get_handler, mock_parse,
                    mock_ProxyConfig, mock_SafeConfigParser, mock_warn):
        filt = middleware.bark_filter({})

        self.assertFalse(mock_SafeConfigParser.called)
        self.assertFalse(mock_ProxyConfig.called)
        self.assertFalse(mock_parse.called)
        self.assertFalse(mock_get_handler.called)
        self.assertFalse(mock_warn.called)
        self.assertFalse(mock_BarkMiddleware.called)

        mid = filt('app')

        mock_BarkMiddleware.assert_called_once_with('app', {}, None)
        self.assertEqual(mid, 'mid')

    @mock.patch.object(middleware.LOG, 'warn')
    @mock.patch('ConfigParser.SafeConfigParser')
    @mock.patch('bark.proxy.ProxyConfig')
    @mock.patch('bark.format.Format.parse', side_effect=lambda x: x)
    @mock.patch('bark.handlers.get_handler', side_effect=lambda x, y, z: x)
    @mock.patch.object(middleware, 'BarkMiddleware', return_value='mid')
    def test_localonly(self, mock_BarkMiddleware, mock_get_handler, mock_parse,
                       mock_ProxyConfig, mock_SafeConfigParser, mock_warn):
        local_conf = {
            'ignored': 'should be ignored',
            'log1.format': 'format string for log1',
            'log1.arg1': 'argument 1',
            'log1.arg2': 'argument 2',
            'log2.format': 'format string for log2',
            'log2.type': 'other',
            'log2.arg3': 'argument 3',
            'log2.arg4': 'argument 4',
        }

        filt = middleware.bark_filter({}, **local_conf)

        self.assertFalse(mock_SafeConfigParser.called)
        self.assertFalse(mock_ProxyConfig.called)
        mock_parse.assert_has_calls([
            mock.call('format string for log1'),
            mock.call('format string for log2'),
        ], any_order=True)
        mock_get_handler.assert_has_calls([
            mock.call('file', 'log1',
                      dict(arg1='argument 1', arg2='argument 2')),
            mock.call('other', 'log2',
                      dict(arg3='argument 3', arg4='argument 4')),
        ], any_order=True)
        self.assertFalse(mock_warn.called)
        self.assertFalse(mock_BarkMiddleware.called)

        mid = filt('app')

        mock_BarkMiddleware.assert_called_once_with('app', {
            'log1': ('format string for log1', 'file'),
            'log2': ('format string for log2', 'other'),
        }, None)
        self.assertEqual(mid, 'mid')

    @mock.patch.object(middleware.LOG, 'warn')
    @mock.patch('ConfigParser.SafeConfigParser')
    @mock.patch('bark.proxy.ProxyConfig')
    @mock.patch('bark.format.Format.parse', side_effect=lambda x: x)
    @mock.patch('bark.handlers.get_handler', side_effect=lambda x, y, z: x)
    @mock.patch.object(middleware, 'BarkMiddleware', return_value='mid')
    def test_missingformat(self, mock_BarkMiddleware, mock_get_handler,
                           mock_parse, mock_ProxyConfig, mock_SafeConfigParser,
                           mock_warn):
        local_conf = {
            'ignored': 'should be ignored',
            'log1.arg1': 'argument 1',
            'log1.arg2': 'argument 2',
            'log2.format': 'format string for log2',
            'log2.type': 'other',
            'log2.arg3': 'argument 3',
            'log2.arg4': 'argument 4',
        }

        filt = middleware.bark_filter({}, **local_conf)

        self.assertFalse(mock_SafeConfigParser.called)
        self.assertFalse(mock_ProxyConfig.called)
        mock_parse.assert_called_once_with('format string for log2')
        mock_get_handler.assert_called_once_with('other', 'log2',
                                                 dict(arg3='argument 3',
                                                      arg4='argument 4'))
        mock_warn.assert_called_once_with(
            "No format specified for log 'log1'; skipping.")
        self.assertFalse(mock_BarkMiddleware.called)

        mid = filt('app')

        mock_BarkMiddleware.assert_called_once_with('app', {
            'log2': ('format string for log2', 'other'),
        }, None)
        self.assertEqual(mid, 'mid')

    @mock.patch.object(middleware.LOG, 'warn')
    @mock.patch('ConfigParser.SafeConfigParser')
    @mock.patch('bark.proxy.ProxyConfig')
    @mock.patch('bark.format.Format.parse', side_effect=lambda x: x)
    @mock.patch('bark.handlers.get_handler', side_effect=missing_handler)
    @mock.patch.object(middleware, 'BarkMiddleware', return_value='mid')
    def test_missinghandler(self, mock_BarkMiddleware, mock_get_handler,
                            mock_parse, mock_ProxyConfig,
                            mock_SafeConfigParser, mock_warn):
        local_conf = {
            'ignored': 'should be ignored',
            'log1.format': 'format string for log1',
            'log1.arg1': 'argument 1',
            'log1.arg2': 'argument 2',
            'log2.format': 'format string for log2',
            'log2.type': 'other',
            'log2.arg3': 'argument 3',
            'log2.arg4': 'argument 4',
        }

        filt = middleware.bark_filter({}, **local_conf)

        self.assertFalse(mock_SafeConfigParser.called)
        self.assertFalse(mock_ProxyConfig.called)
        mock_parse.assert_has_calls([
            mock.call('format string for log1'),
            mock.call('format string for log2'),
        ], any_order=True)
        mock_get_handler.assert_has_calls([
            mock.call('file', 'log1',
                      dict(arg1='argument 1', arg2='argument 2')),
            mock.call('other', 'log2',
                      dict(arg3='argument 3', arg4='argument 4')),
        ], any_order=True)
        print mock_warn.mock_calls
        mock_warn.assert_called_once_with(
            "Cannot load handler of type 'file' for log 'log1': failure")
        self.assertFalse(mock_BarkMiddleware.called)

        mid = filt('app')

        mock_BarkMiddleware.assert_called_once_with('app', {
            'log2': ('format string for log2', 'other'),
        }, None)
        self.assertEqual(mid, 'mid')

    @mock.patch.object(middleware.LOG, 'warn')
    @mock.patch('ConfigParser.SafeConfigParser', return_value=mock.Mock(**{
        'sections.return_value': ['log1', 'log3'],
        'options.side_effect': lambda x: {
            'log1': [('arg1', 'override'), ('arg3', 'argument 3')],
            'log3': [('format', 'format 3'), ('arg5', 'argument 5')],
        }[x],
    }))
    @mock.patch('bark.proxy.ProxyConfig')
    @mock.patch('bark.format.Format.parse', side_effect=lambda x: x)
    @mock.patch('bark.handlers.get_handler', side_effect=lambda x, y, z: x)
    @mock.patch.object(middleware, 'BarkMiddleware', return_value='mid')
    def test_conffile(self, mock_BarkMiddleware, mock_get_handler, mock_parse,
                      mock_ProxyConfig, mock_SafeConfigParser, mock_warn):
        local_conf = {
            'ignored': 'should be ignored',
            'config': '/etc/config',
            'log1.format': 'format string for log1',
            'log1.arg1': 'argument 1',
            'log1.arg2': 'argument 2',
            'log2.format': 'format string for log2',
            'log2.type': 'other',
            'log2.arg3': 'argument 3',
            'log2.arg4': 'argument 4',
        }

        filt = middleware.bark_filter({}, **local_conf)

        mock_SafeConfigParser.assert_called_once_with()
        mock_SafeConfigParser.return_value.assert_has_calls([
            mock.call.read(['/etc/config']),
            mock.call.sections(),
            mock.call.options('log1'),
            mock.call.options('log3'),
        ])
        self.assertFalse(mock_ProxyConfig.called)
        mock_parse.assert_has_calls([
            mock.call('format string for log1'),
            mock.call('format string for log2'),
            mock.call('format 3'),
        ], any_order=True)
        mock_get_handler.assert_has_calls([
            mock.call('file', 'log1',
                      dict(arg1='argument 1', arg2='argument 2',
                           arg3='argument 3')),
            mock.call('other', 'log2',
                      dict(arg3='argument 3', arg4='argument 4')),
            mock.call('file', 'log3', dict(arg5='argument 5')),
        ], any_order=True)
        self.assertFalse(mock_warn.called)
        self.assertFalse(mock_BarkMiddleware.called)

        mid = filt('app')

        mock_BarkMiddleware.assert_called_once_with('app', {
            'log1': ('format string for log1', 'file'),
            'log2': ('format string for log2', 'other'),
            'log3': ('format 3', 'file'),
        }, None)
        self.assertEqual(mid, 'mid')

    @mock.patch.object(middleware.LOG, 'warn')
    @mock.patch('ConfigParser.SafeConfigParser')
    @mock.patch('bark.proxy.ProxyConfig', return_value='proxies')
    @mock.patch('bark.format.Format.parse')
    @mock.patch('bark.handlers.get_handler')
    @mock.patch.object(middleware, 'BarkMiddleware', return_value='mid')
    def test_proxies(self, mock_BarkMiddleware, mock_get_handler, mock_parse,
                     mock_ProxyConfig, mock_SafeConfigParser, mock_warn):
        local_conf = {
            'proxies.arg1': 'arg1',
            'proxies.arg2': 'arg2',
            'proxies.arg3': 'arg3',
        }

        filt = middleware.bark_filter({}, **local_conf)

        self.assertFalse(mock_SafeConfigParser.called)
        mock_ProxyConfig.assert_called_once_with(dict(
            arg1='arg1',
            arg2='arg2',
            arg3='arg3',
        ))
        self.assertFalse(mock_parse.called)
        self.assertFalse(mock_get_handler.called)
        self.assertFalse(mock_warn.called)
        self.assertFalse(mock_BarkMiddleware.called)

        mid = filt('app')

        mock_BarkMiddleware.assert_called_once_with('app', {}, 'proxies')
        self.assertEqual(mid, 'mid')

    @mock.patch.object(middleware.LOG, 'warn')
    @mock.patch('ConfigParser.SafeConfigParser')
    @mock.patch('bark.proxy.ProxyConfig', side_effect=KeyError('foo'))
    @mock.patch('bark.format.Format.parse')
    @mock.patch('bark.handlers.get_handler')
    @mock.patch.object(middleware, 'BarkMiddleware', return_value='mid')
    def test_badproxies(self, mock_BarkMiddleware, mock_get_handler,
                        mock_parse, mock_ProxyConfig, mock_SafeConfigParser,
                        mock_warn):
        local_conf = {
            'proxies.arg1': 'arg1',
            'proxies.arg2': 'arg2',
            'proxies.arg3': 'arg3',
        }

        filt = middleware.bark_filter({}, **local_conf)

        self.assertFalse(mock_SafeConfigParser.called)
        mock_ProxyConfig.assert_called_once_with(dict(
            arg1='arg1',
            arg2='arg2',
            arg3='arg3',
        ))
        self.assertFalse(mock_parse.called)
        self.assertFalse(mock_get_handler.called)
        mock_warn.assert_called_once_with(
            "Cannot configure proxy handling: option 'foo' is "
            "missing from the proxy configuration")
        self.assertFalse(mock_BarkMiddleware.called)

        mid = filt('app')

        mock_BarkMiddleware.assert_called_once_with('app', {}, None)
        self.assertEqual(mid, 'mid')

    @mock.patch.object(middleware.LOG, 'warn')
    @mock.patch('ConfigParser.SafeConfigParser', return_value=mock.Mock(**{
        'sections.return_value': ['log1', 'proxies'],
        'options.side_effect': lambda x: {
            'log1': [('arg1', 'override'), ('arg5', 'argument 5')],
            'proxies': [('arg6', 'argument 6'), ('arg7', 'argument 7')],
        }[x],
    }))
    @mock.patch('bark.proxy.ProxyConfig', return_value='proxies')
    @mock.patch('bark.format.Format.parse', side_effect=lambda x: x)
    @mock.patch('bark.handlers.get_handler', side_effect=lambda x, y, z: x)
    @mock.patch.object(middleware, 'BarkMiddleware', return_value='mid')
    def test_together(self, mock_BarkMiddleware, mock_get_handler, mock_parse,
                      mock_ProxyConfig, mock_SafeConfigParser, mock_warn):
        local_conf = {
            'ignored': 'should be ignored',
            'config': '/etc/config',
            'log1.format': 'format string for log1',
            'log1.arg1': 'argument 1',
            'log1.arg2': 'argument 2',
            'log2.format': 'format string for log2',
            'log2.type': 'other',
            'log2.arg3': 'argument 3',
            'log2.arg4': 'argument 4',
            'proxies.arg8': 'argument 8',
            'proxies.arg9': 'argument 9',
        }

        filt = middleware.bark_filter({}, **local_conf)

        mock_SafeConfigParser.assert_called_once_with()
        mock_SafeConfigParser.return_value.assert_has_calls([
            mock.call.read(['/etc/config']),
            mock.call.sections(),
            mock.call.options('log1'),
            mock.call.options('proxies'),
        ])
        mock_ProxyConfig.assert_called_once_with(dict(
            arg6='argument 6',
            arg7='argument 7',
            arg8='argument 8',
            arg9='argument 9',
        ))
        mock_parse.assert_has_calls([
            mock.call('format string for log1'),
            mock.call('format string for log2'),
        ], any_order=True)
        mock_get_handler.assert_has_calls([
            mock.call('file', 'log1',
                      dict(arg1='argument 1', arg2='argument 2',
                           arg5='argument 5')),
            mock.call('other', 'log2',
                      dict(arg3='argument 3', arg4='argument 4')),
        ], any_order=True)
        self.assertFalse(mock_warn.called)
        self.assertFalse(mock_BarkMiddleware.called)

        mid = filt('app')

        mock_BarkMiddleware.assert_called_once_with('app', {
            'log1': ('format string for log1', 'file'),
            'log2': ('format string for log2', 'other'),
        }, 'proxies')
        self.assertEqual(mid, 'mid')
