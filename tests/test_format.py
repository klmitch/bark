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
import pkg_resources
import unittest2

from bark import conversions
from bark import format


class TestException(Exception):
    pass


class FakeStringConversion(object):
    def __init__(self, *text):
        self.text = list(text)

    def append(self, text):
        self.text.append(text)


class FormatTest(unittest2.TestCase):
    @mock.patch.dict(format.Format._conversion_cache)
    @mock.patch.object(conversions, 'StringConversion',
                       return_value=mock.Mock())
    @mock.patch('pkg_resources.iter_entry_points',
                return_value=[
                    mock.Mock(**{'load.side_effect': ImportError}),
                    mock.Mock(**{'load.side_effect': ImportError}),
                ])
    def test_get_conversion_error(self, mock_iter_entry_points,
                                  mock_StringConversion):
        result = format.Format._get_conversion('a', 'modifier')

        self.assertEqual(id(result), id(mock_StringConversion.return_value))
        mock_iter_entry_points.assert_called_once_with('bark.conversion', 'a')
        mock_iter_entry_points.return_value[0].load.assert_called_once_with()
        mock_iter_entry_points.return_value[1].load.assert_called_once_with()
        mock_StringConversion.assert_called_once_with(
            "(Unknown conversion '%a')")
        self.assertEqual(format.Format._conversion_cache, dict(a=None))

    @mock.patch.dict(format.Format._conversion_cache)
    @mock.patch.object(conversions, 'StringConversion',
                       return_value=mock.Mock())
    @mock.patch('pkg_resources.iter_entry_points',
                return_value=[
                    mock.Mock(**{
                        'load.side_effect': pkg_resources.UnknownExtra,
                    }),
                    mock.Mock(**{
                        'load.side_effect': pkg_resources.UnknownExtra,
                    }),
                ])
    def test_get_conversion_unknown_extra(self, mock_iter_entry_points,
                                          mock_StringConversion):
        result = format.Format._get_conversion('a', 'modifier')

        self.assertEqual(id(result), id(mock_StringConversion.return_value))
        mock_iter_entry_points.assert_called_once_with('bark.conversion', 'a')
        mock_iter_entry_points.return_value[0].load.assert_called_once_with()
        mock_iter_entry_points.return_value[1].load.assert_called_once_with()
        mock_StringConversion.assert_called_once_with(
            "(Unknown conversion '%a')")
        self.assertEqual(format.Format._conversion_cache, dict(a=None))

    @mock.patch.dict(format.Format._conversion_cache)
    @mock.patch.object(conversions, 'StringConversion',
                       return_value=mock.Mock())
    @mock.patch('pkg_resources.iter_entry_points',
                return_value=[
                    mock.Mock(**{'load.side_effect': TestException}),
                    mock.Mock(**{'load.side_effect': TestException}),
                ])
    def test_get_conversion_other_exception(self, mock_iter_entry_points,
                                            mock_StringConversion):
        self.assertRaises(TestException, format.Format._get_conversion,
                          'a', 'modifier')
        mock_iter_entry_points.assert_called_once_with('bark.conversion', 'a')
        mock_iter_entry_points.return_value[0].load.assert_called_once_with()
        self.assertFalse(mock_iter_entry_points.return_value[1].load.called)
        self.assertFalse(mock_StringConversion.called)
        self.assertEqual(format.Format._conversion_cache, {})

    @mock.patch.dict(format.Format._conversion_cache)
    @mock.patch.object(conversions, 'StringConversion',
                       return_value=mock.Mock())
    @mock.patch('pkg_resources.iter_entry_points',
                return_value=[mock.Mock(**{
                    'load.return_value': mock.Mock(return_value='fake_conv'),
                })])
    def test_get_conversion_load(self, mock_iter_entry_points,
                                 mock_StringConversion):
        result = format.Format._get_conversion('a', 'modifier')

        self.assertEqual(result, 'fake_conv')
        mock_iter_entry_points.assert_called_once_with('bark.conversion', 'a')
        mock_load = mock_iter_entry_points.return_value[0].load
        mock_load.assert_called_once_with()
        mock_load.return_value.assert_called_once_with('a', 'modifier')
        self.assertFalse(mock_StringConversion.called)
        self.assertEqual(format.Format._conversion_cache,
                         dict(a=mock_load.return_value))

    @mock.patch.dict(format.Format._conversion_cache,
                     a=mock.Mock(return_value='fake_conv'))
    @mock.patch.object(conversions, 'StringConversion',
                       return_value=mock.Mock())
    @mock.patch('pkg_resources.iter_entry_points',
                side_effect=Exception)
    def test_get_conversion_cached(self, mock_iter_entry_points,
                                   mock_StringConversion):
        result = format.Format._get_conversion('a', 'modifier')

        self.assertEqual(result, 'fake_conv')
        self.assertFalse(mock_iter_entry_points.called)
        self.assertNotEqual(format.Format._conversion_cache, {})
        format.Format._conversion_cache['a'].assert_called_once_with(
            'a', 'modifier')
        self.assertFalse(mock_StringConversion.called)

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
