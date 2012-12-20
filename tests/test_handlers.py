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

import logging
import logging.handlers
import sys

import mock
import unittest2

from bark import handlers
from bark import middleware


class SimpleFormatterTest(unittest2.TestCase):
    def test_format(self):
        fmt = handlers.SimpleFormatter()
        record = logging.LogRecord('bark', logging.INFO, __file__, 27,
                                   'a test message', (), None, 'test_format')

        result = fmt.format(record)

        self.assertEqual(result, 'a test message')


class WrapLogHandlerTest(unittest2.TestCase):
    @mock.patch.object(handlers, 'SimpleFormatter', return_value='simple')
    @mock.patch('inspect.getsourcefile', return_value='bark/middleware.py')
    @mock.patch('inspect.getsourcelines', return_value=([], 127))
    def test_wrap_log_handler(self, mock_getsourcelines, mock_getsourcefile,
                              mock_SimpleFormatter):
        handler = mock.Mock(**{'emit.__name__': 'emit'})
        emit = handlers.wrap_log_handler(handler)

        mock_SimpleFormatter.assert_called_once_with()
        handler.setFormatter.assert_called_once_with('simple')
        self.assertFalse(handler.emit.called)

        emit("test message")

        self.assertEqual(handler.emit.call_count, 1)

        record = handler.emit.call_args[0][0]
        self.assertEqual(record.name, 'bark')
        self.assertEqual(record.levelno, logging.INFO)
        self.assertEqual(record.filename, 'middleware.py')
        self.assertEqual(record.module, 'middleware')
        self.assertEqual(record.lineno, 127)
        self.assertEqual(record.msg, 'test message')
        self.assertEqual(record.args, ())
        self.assertEqual(record.exc_info, None)
        self.assertEqual(record.funcName, '__call__')


class ArgTypesTest(unittest2.TestCase):
    def test_arg_types(self):
        @handlers.arg_types(foo=1, bar=2)
        @handlers.arg_types(bar=3, baz=4)
        def test():
            pass

        self.assertEqual(test._bark_types, dict(foo=1, bar=2, baz=4))


class BooleanTest(unittest2.TestCase):
    def test_boolean_true(self):
        for text in ['1', '1000', 't', 'T', 'TrUe', 'oN', 'yEs']:
            self.assertEqual(handlers.boolean(text), True)

    def test_boolean_false(self):
        for text in ['0', '0000', 'f', 'F', 'FaLsE', 'oFf', 'No']:
            self.assertEqual(handlers.boolean(text), False)

    def test_boolean_invalid(self):
        for text in ['tT', 'fF', 'tRu', 'FaL', 'o', 'yEs/nO']:
            self.assertRaises(ValueError, handlers.boolean, text)


class CommaTest(unittest2.TestCase):
    def test_comma_singular(self):
        self.assertEqual(handlers.comma('test'), ['test'])

    def test_comma_multiple(self):
        self.assertEqual(handlers.comma('test1,test2,test3'),
                         ['test1', 'test2', 'test3'])

    def test_comma_strip(self):
        self.assertEqual(handlers.comma('test1   ,   test2'),
                         ['test1', 'test2'])


class AddressTest(unittest2.TestCase):
    def test_address_noport(self):
        self.assertEqual(handlers.address('/dev/log'), '/dev/log')

    def test_address_withport(self):
        self.assertEqual(handlers.address('1:2:3'), ('1:2', 3))

    def test_address_badport(self):
        self.assertRaises(ValueError, handlers.address, '1:2:port')


class ChoiceTest(unittest2.TestCase):
    def test_init(self):
        ch = handlers.choice('foo', 'bar', 'baz')

        self.assertEqual(ch.choices, set(['foo', 'bar', 'baz']))

    def test_call_accept(self):
        ch = handlers.choice('foo', 'bar', 'baz')

        self.assertEqual(ch('foo'), 'foo')
        self.assertEqual(ch('bar'), 'bar')
        self.assertEqual(ch('baz'), 'baz')

    def test_call_reject(self):
        ch = handlers.choice('foo', 'bar', 'baz')

        self.assertRaises(ValueError, ch, 'spam')


class ArgMapTest(unittest2.TestCase):
    def test_init(self):
        am = handlers.argmap(dict(foo=1, bar=2, baz=3))

        self.assertEqual(am.argmap, dict(foo=1, bar=2, baz=3))

    def test_call_accept(self):
        am = handlers.argmap(dict(foo=1, bar=2, baz=3))

        self.assertEqual(am('foo'), 1)
        self.assertEqual(am('bar'), 2)
        self.assertEqual(am('baz'), 3)

    def test_call_reject(self):
        am = handlers.argmap(dict(foo=1, bar=2, baz=3))

        self.assertRaises(ValueError, am, 'spam')


class CredentialsTest(unittest2.TestCase):
    def test_credentials_nocolon(self):
        self.assertEqual(handlers.credentials('user'), ('user', ''))

    def test_credentials_emptypass(self):
        self.assertEqual(handlers.credentials('user:'), ('user', ''))

    def test_credentials_emptyuser(self):
        self.assertEqual(handlers.credentials(':pass'), ('', 'pass'))

    def test_credentials_full(self):
        self.assertEqual(handlers.credentials('user:pass'), ('user', 'pass'))


class NullHandlerTest(unittest2.TestCase):
    def test_handler(self):
        emit = handlers.null_handler('null', 'test')

        self.assertTrue(callable(emit))

        # Make sure it doesn't raise any failures
        emit('this is a test')


class StdOutHandlerTest(unittest2.TestCase):
    @mock.patch('logging.StreamHandler',
                return_value=mock.Mock(**{'emit.__name__': 'emit'}))
    def test_handler(self, mock_StreamHandler):
        emit = handlers.stdout_handler('stdout', 'test')

        self.assertTrue(callable(emit))
        mock_StreamHandler.assert_called_once_with(sys.stdout)


class StdErrHandlerTest(unittest2.TestCase):
    @mock.patch('logging.StreamHandler',
                return_value=mock.Mock(**{'emit.__name__': 'emit'}))
    def test_handler(self, mock_StreamHandler):
        emit = handlers.stderr_handler('stderr', 'test')

        self.assertTrue(callable(emit))
        mock_StreamHandler.assert_called_once_with(sys.stderr)


class FileHandlerTest(unittest2.TestCase):
    def test_arg_types(self):
        self.assertEqual(handlers.file_handler._bark_types,
                         dict(delay=handlers.boolean))

    @mock.patch('logging.FileHandler',
                return_value=mock.Mock(**{'emit.__name__': 'emit'}))
    def test_handler(self, mock_FileHandler):
        args = dict(filename='filename', mode='b', encoding='encoding',
                    delay=True)
        emit = handlers.file_handler('file', 'test', **args)

        self.assertTrue(callable(emit))
        mock_FileHandler.assert_called_once_with(
            'filename', mode='b', encoding='encoding', delay=True)


class WatchedFileHandlerTest(unittest2.TestCase):
    def test_arg_types(self):
        self.assertEqual(handlers.watched_file_handler._bark_types,
                         dict(delay=handlers.boolean))

    @mock.patch('logging.handlers.WatchedFileHandler',
                return_value=mock.Mock(**{'emit.__name__': 'emit'}))
    def test_handler(self, mock_WatchedFileHandler):
        args = dict(filename='filename', mode='b', encoding='encoding',
                    delay=True)
        emit = handlers.watched_file_handler('watched_file', 'test', **args)

        self.assertTrue(callable(emit))
        mock_WatchedFileHandler.assert_called_once_with(
            'filename', mode='b', encoding='encoding', delay=True)


class RotatingFileHandlerTest(unittest2.TestCase):
    def test_arg_types(self):
        self.assertEqual(handlers.rotating_file_handler._bark_types,
                         dict(maxBytes=int, backupCount=int,
                              delay=handlers.boolean))

    @mock.patch('logging.handlers.RotatingFileHandler',
                return_value=mock.Mock(**{'emit.__name__': 'emit'}))
    def test_handler(self, mock_RotatingFileHandler):
        args = dict(filename='filename', mode='b', maxBytes=23,
                    backupCount=14, encoding='encoding', delay=True)
        emit = handlers.rotating_file_handler('rotating_file', 'test', **args)

        self.assertTrue(callable(emit))
        mock_RotatingFileHandler.assert_called_once_with(
            'filename', mode='b', maxBytes=23, backupCount=14,
            encoding='encoding', delay=True)


class TimedRotatingFileHandlerTest(unittest2.TestCase):
    def test_arg_types(self):
        self.assertEqual(handlers.timed_rotating_file_handler._bark_types,
                         dict(interval=int, backupCount=int,
                              delay=handlers.boolean, utc=handlers.boolean))

    @mock.patch('logging.handlers.TimedRotatingFileHandler',
                return_value=mock.Mock(**{'emit.__name__': 'emit'}))
    def test_handler(self, mock_TimedRotatingFileHandler):
        args = dict(filename='filename', when='b', interval=23,
                    backupCount=14, encoding='encoding', delay=True, utc=True)
        emit = handlers.timed_rotating_file_handler('timed_rotating_file',
                                                    'test', **args)

        self.assertTrue(callable(emit))
        mock_TimedRotatingFileHandler.assert_called_once_with(
            'filename', when='b', interval=23, backupCount=14,
            encoding='encoding', delay=True, utc=True)


class SocketHandlerTest(unittest2.TestCase):
    def test_arg_types(self):
        self.assertEqual(handlers.socket_handler._bark_types,
                         dict(port=int))

    @mock.patch('logging.handlers.SocketHandler',
                return_value=mock.Mock(**{'emit.__name__': 'emit'}))
    def test_handler(self, mock_SocketHandler):
        args = dict(host='host', port=4005)
        emit = handlers.socket_handler('socket', 'test', **args)

        self.assertTrue(callable(emit))
        mock_SocketHandler.assert_called_once_with(
            'host', 4005)


class DatagramHandlerTest(unittest2.TestCase):
    def test_arg_types(self):
        self.assertEqual(handlers.datagram_handler._bark_types,
                         dict(port=int))

    @mock.patch('logging.handlers.DatagramHandler',
                return_value=mock.Mock(**{'emit.__name__': 'emit'}))
    def test_handler(self, mock_DatagramHandler):
        args = dict(host='host', port=4005)
        emit = handlers.datagram_handler('datagram', 'test', **args)

        self.assertTrue(callable(emit))
        mock_DatagramHandler.assert_called_once_with('host', 4005)


class SysLogHandlerTest(unittest2.TestCase):
    def test_arg_types(self):
        types = handlers.syslog_handler._bark_types
        self.assertEqual(types.keys(), ['address', 'facility'])
        self.assertEqual(types['address'], handlers.address)
        self.assertIsInstance(types['facility'], handlers.argmap)
        self.assertEqual(types['facility'].argmap,
                         logging.handlers.SysLogHandler.facility_names)

    @mock.patch('logging.handlers.SysLogHandler',
                return_value=mock.Mock(**{'emit.__name__': 'emit'}))
    def test_handler(self, mock_SysLogHandler):
        args = dict(address='address', facility='facility')
        emit = handlers.syslog_handler('syslog', 'test', **args)

        self.assertTrue(callable(emit))
        mock_SysLogHandler.assert_called_once_with(
            address='address', facility='facility')


class NTEventLogHandlerTest(unittest2.TestCase):
    def test_arg_types(self):
        types = handlers.nt_event_log_handler._bark_types
        self.assertEqual(types.keys(), ['logtype'])
        self.assertIsInstance(types['logtype'], handlers.choice)
        self.assertEqual(types['logtype'].choices,
                         set(['Application', 'System', 'Security']))

    @mock.patch('logging.handlers.NTEventLogHandler',
                return_value=mock.Mock(**{'emit.__name__': 'emit'}))
    def test_handler(self, mock_NTEventLogHandler):
        args = dict(appname='appname', dllname='dllname', logtype='logtype')
        emit = handlers.nt_event_log_handler('nt_event_log', 'test', **args)

        self.assertTrue(callable(emit))
        mock_NTEventLogHandler.assert_called_once_with(
            'appname', dllname='dllname', logtype='logtype')


class SMTPHandlerTest(unittest2.TestCase):
    def test_arg_types(self):
        self.assertEqual(handlers.smtp_handler._bark_types,
                         dict(mailhost=handlers.address,
                              toaddrs=handlers.comma,
                              credentials=handlers.credentials))

    @mock.patch('logging.handlers.SMTPHandler',
                return_value=mock.Mock(**{'emit.__name__': 'emit'}))
    def test_handler(self, mock_SMTPHandler):
        args = dict(mailhost='mailhost', fromaddr='fromaddr',
                    toaddrs='toaddrs', subject='subject',
                    credentials='credentials')
        emit = handlers.smtp_handler('smtp', 'test', **args)

        self.assertTrue(callable(emit))
        mock_SMTPHandler.assert_called_once_with(
            'mailhost', 'fromaddr', 'toaddrs', 'subject',
            credentials='credentials')


class HTTPHandlerTest(unittest2.TestCase):
    def test_arg_types(self):
        types = handlers.http_handler._bark_types
        self.assertEqual(types.keys(), ['method'])
        self.assertIsInstance(types['method'], handlers.choice)
        self.assertEqual(types['method'].choices, set(['GET', 'POST']))

    @mock.patch('logging.handlers.HTTPHandler',
                return_value=mock.Mock(**{'emit.__name__': 'emit'}))
    def test_handler(self, mock_HTTPHandler):
        args = dict(host='host', url='url', method='method')
        emit = handlers.http_handler('http', 'test', **args)

        self.assertTrue(callable(emit))
        mock_HTTPHandler.assert_called_once_with(
            'host', 'url', method='method')
