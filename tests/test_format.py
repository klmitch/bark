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
from bark import format


class FakeStringConversion(object):
    def __init__(self, *text):
        self.text = list(text)

    def append(self, text):
        self.text.append(text)


class FormatTest(unittest2.TestCase):
    def test_init(self):
        fmt = format.Format()

        self.assertEqual(fmt.conversions, [])

    def test_str(self):
        fmt = format.Format()
        fmt.conversions = ["this is ", 1, " test"]

        self.assertEqual(str(fmt), "this is 1 test")

    @mock.patch.object(conversions, 'StringConversion',
                       return_value=mock.Mock())
    def test_append_text_empty(self, mock_StringConversion):
        fmt = format.Format()

        fmt.append_text('some text')

        self.assertEqual(fmt.conversions, [mock_StringConversion.return_value])
        mock_StringConversion.assert_called_once_with('some text')

    @mock.patch.object(conversions, 'StringConversion', FakeStringConversion)
    def test_append_text_nonempty(self):
        fmt = format.Format()
        fmt.conversions.append("something")

        fmt.append_text('some text')

        self.assertEqual(len(fmt.conversions), 2)
        self.assertEqual(fmt.conversions[0], "something")
        self.assertIsInstance(fmt.conversions[1], FakeStringConversion)
        self.assertEqual(fmt.conversions[1].text, ['some text'])

    @mock.patch.object(conversions, 'StringConversion', FakeStringConversion)
    def test_append_text_preceed(self):
        fmt = format.Format()
        fmt.conversions.extend(["something",
                                FakeStringConversion("other text")])

        fmt.append_text('some text')

        self.assertEqual(len(fmt.conversions), 2)
        self.assertEqual(fmt.conversions[0], "something")
        self.assertIsInstance(fmt.conversions[1], FakeStringConversion)
        self.assertEqual(fmt.conversions[1].text, ['other text', 'some text'])

    def test_append_conv(self):
        fmt = format.Format()

        fmt.append_conv('conversion')

        self.assertEqual(fmt.conversions, ['conversion'])

    def test_prepare(self):
        fmt = format.Format()
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
        fmt = format.Format()
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
