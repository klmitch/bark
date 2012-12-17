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

from bark import conversions


class ModifierTest(unittest2.TestCase):
    def test_init(self):
        mod = conversions.Modifier()

        self.assertEqual(mod.codes, set())
        self.assertEqual(mod.reject, True)
        self.assertEqual(mod.param, None)

    def test_set_codes_noreject(self):
        mod = conversions.Modifier()

        mod.set_codes([404, 501])

        self.assertEqual(mod.codes, set([404, 501]))
        self.assertEqual(mod.reject, False)

    def test_set_codes_reject(self):
        mod = conversions.Modifier()

        mod.set_codes([404, 501], True)

        self.assertEqual(mod.codes, set([404, 501]))
        self.assertEqual(mod.reject, True)

    def test_set_param(self):
        mod = conversions.Modifier()

        mod.set_param('spam')

        self.assertEqual(mod.param, 'spam')

    def test_accept_empty(self):
        mod = conversions.Modifier()

        self.assertEqual(mod.accept(200), True)
        self.assertEqual(mod.accept(404), True)
        self.assertEqual(mod.accept(501), True)

    def test_accept_noreject(self):
        mod = conversions.Modifier()
        mod.set_codes([404, 501])

        self.assertEqual(mod.accept(200), False)
        self.assertEqual(mod.accept(404), True)
        self.assertEqual(mod.accept(501), True)

    def test_accept_reject(self):
        mod = conversions.Modifier()
        mod.set_codes([404, 501], True)

        self.assertEqual(mod.accept(200), True)
        self.assertEqual(mod.accept(404), False)
        self.assertEqual(mod.accept(501), False)


class EscapeDictTest(unittest2.TestCase):
    def test_missing(self):
        edict = conversions.EscapeDict(dict(a='a', b='b', c='c'))

        self.assertEqual(edict['a'], 'a')
        self.assertEqual(edict['b'], 'b')
        self.assertEqual(edict['c'], 'c')
        self.assertEqual(edict['d'], '\\x64')
        self.assertEqual(edict['e'], '\\x65')
        self.assertEqual(edict['f'], '\\x66')
        self.assertEqual(edict['\0'], '\\x00')
        self.assertEqual(edict['\1'], '\\x01')


class ConversionForTest(conversions.Conversion):
    def convert(self, request, response, data):
        pass


class ConversionTest(unittest2.TestCase):
    def test_needescape(self):
        self.assertEqual(conversions.Conversion._needescape('a'), False)
        self.assertEqual(conversions.Conversion._needescape('"'), True)
        self.assertEqual(conversions.Conversion._needescape('\\'), True)
        self.assertEqual(conversions.Conversion._needescape('\1'), True)
        self.assertEqual(conversions.Conversion._needescape('\177'), True)
        self.assertEqual(conversions.Conversion._needescape('\176'), False)

    def test_escape(self):
        exemplar = u"\0\1\b\n\r\t\v\\\"\u3f26test"
        expected = "\\x00\\x01\\b\\n\\r\\t\\v\\\\\\\"\\xe3\\xbc\\xa6test"

        self.assertEqual(conversions.Conversion.escape(exemplar), expected)

    def test_init(self):
        conv = ConversionForTest('a', 'modifier')

        self.assertEqual(conv.conv_chr, 'a')
        self.assertEqual(conv.modifier, 'modifier')

    def test_prepare(self):
        conv = ConversionForTest('a', 'modifier')

        self.assertEqual(conv.prepare('request'), {})


class FakeStringConversion(object):
    def __init__(self, *text):
        self.text = list(text)

    def append(self, text):
        self.text.append(text)


class FormatTest(unittest2.TestCase):
    def test_init(self):
        fmt = conversions.Format()

        self.assertEqual(fmt.conversions, [])

    @mock.patch.object(conversions, 'StringConversion',
                       return_value=mock.Mock())
    def test_append_text_empty(self, mock_StringConversion):
        fmt = conversions.Format()

        fmt.append_text('some text')

        self.assertEqual(fmt.conversions, [mock_StringConversion.return_value])
        mock_StringConversion.assert_called_once_with('some text')

    @mock.patch.object(conversions, 'StringConversion', FakeStringConversion)
    def test_append_text_nonempty(self):
        fmt = conversions.Format()
        fmt.conversions.append("something")

        fmt.append_text('some text')

        self.assertEqual(len(fmt.conversions), 2)
        self.assertEqual(fmt.conversions[0], "something")
        self.assertIsInstance(fmt.conversions[1], FakeStringConversion)
        self.assertEqual(fmt.conversions[1].text, ['some text'])

    @mock.patch.object(conversions, 'StringConversion', FakeStringConversion)
    def test_append_text_preceed(self):
        fmt = conversions.Format()
        fmt.conversions.extend(["something",
                                FakeStringConversion("other text")])

        fmt.append_text('some text')

        self.assertEqual(len(fmt.conversions), 2)
        self.assertEqual(fmt.conversions[0], "something")
        self.assertIsInstance(fmt.conversions[1], FakeStringConversion)
        self.assertEqual(fmt.conversions[1].text, ['other text', 'some text'])

    def test_append_conv(self):
        fmt = conversions.Format()

        fmt.append_conv('conversion')

        self.assertEqual(fmt.conversions, ['conversion'])

    def test_prepare(self):
        fmt = conversions.Format()
        fmt.conversions = [
            mock.Mock(**{'prepare.return_value': 'data1'}),
            mock.Mock(**{'prepare.return_value': 'data2'}),
            mock.Mock(**{'prepare.return_value': 'data3'}),
        ]

        result = fmt.prepare('request')

        self.assertEqual(result, ['data1', 'data2', 'data3'])
        for conv in fmt.conversions:
            conv.prepare.assert_called_once_with('request')

    def test_convert(self):
        fmt = conversions.Format()
        fmt.conversions = [
            mock.Mock(**{
                'convert.return_value': 'conv1',
                'modifier': mock.Mock(**{'accept.return_value': True}),
            }),
            mock.Mock(**{
                'convert.return_value': 'conv2',
                'modifier': mock.Mock(**{'accept.return_value': False}),
            }),
            mock.Mock(**{
                'convert.return_value': 'conv3',
                'modifier': mock.Mock(**{'accept.return_value': True}),
            }),
        ]
        data = ['data1', 'data2', 'data3']
        response = mock.Mock(status_code=200)

        result = fmt.convert('request', response, data)

        self.assertEqual(result, 'conv1-conv3')
        for conv, datum in zip(fmt.conversions, data):
            conv.modifier.accept.assert_called_once_with(200)
            if conv.modifier.accept.return_value:
                conv.convert.assert_called_once_with('request', response,
                                                     datum)
            else:
                self.assertFalse(conv.convert.called)
