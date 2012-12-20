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
