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


class ParseStateTest(unittest2.TestCase):
    def test_init(self):
        state = format.ParseState('fmt', 'format')

        self.assertEqual(state.fmt, 'fmt')
        self.assertEqual(state.format, 'format')
        self.assertEqual(state.state, ['string'])
        self.assertEqual(state.str_begin, 0)
        self.assertEqual(state.param_begin, None)
        self.assertEqual(state.conv_begin, None)
        self.assertEqual(state.modifier, None)
        self.assertEqual(state.codes, [])
        self.assertEqual(state.reject, False)
        self.assertEqual(state.ignore, 0)
        self.assertEqual(state.code_last, False)

    def test_eq(self):
        state = format.ParseState('fmt', 'format')
        state.state = ['string', 'other']

        self.assertFalse(state == 'string')
        self.assertTrue(state == 'other')

    def test_pop_state_noidx(self):
        state = format.ParseState('fmt', 'format')
        state.state = ['string', 'other']

        state.pop_state()

        self.assertEqual(state.state, ['string'])
        self.assertEqual(state.str_begin, 0)

    def test_pop_state_withidx(self):
        state = format.ParseState('fmt', 'format')
        state.state = ['string', 'other']

        state.pop_state(5)

        self.assertEqual(state.state, ['string'])
        self.assertEqual(state.str_begin, 5)

    def test_check_ignore(self):
        state = format.ParseState('fmt', 'format')
        state.ignore = 1

        self.assertTrue(state.check_ignore())
        self.assertEqual(state.ignore, 0)
        self.assertFalse(state.check_ignore())
        self.assertEqual(state.ignore, 0)

    def test_set_ignore(self):
        state = format.ParseState('fmt', 'format')

        state.set_ignore(1)

        self.assertEqual(state.ignore, 1)

        state.set_ignore(2)

        self.assertEqual(state.ignore, 3)

    def test_add_text_empty(self):
        state = format.ParseState(mock.Mock(), 'a format string')
        state.str_begin = 2

        state.add_text(2)

        self.assertFalse(state.fmt.append_text.called)
        self.assertEqual(state.str_begin, 2)

    def test_add_text_nonext(self):
        state = format.ParseState(mock.Mock(), 'a format string')
        state.str_begin = 2

        state.add_text(8)

        state.fmt.append_text.assert_called_once_with('format')
        self.assertEqual(state.str_begin, 2)

    def test_add_text_withnext(self):
        state = format.ParseState(mock.Mock(), 'a format string')
        state.str_begin = 2

        state.add_text(8, 8)

        state.fmt.append_text.assert_called_once_with('format')
        self.assertEqual(state.str_begin, 8)

    def test_add_escape_available(self):
        state = format.ParseState(mock.Mock(
            _unescape={'\\n': '\n'}), 'a \\n format string')
        state.str_begin = 2

        state.add_escape(4, 'n')

        state.fmt.append_text.assert_called_once_with('\n')

    def test_add_escape_unavailable(self):
        state = format.ParseState(mock.Mock(
            _unescape={'\\n': '\n'}), 'a \\t format string')
        state.str_begin = 2

        state.add_escape(4, 't')

        state.fmt.append_text.assert_called_once_with('t')

    def test_set_param(self):
        state = format.ParseState('fmt', 'a format string')
        state.modifier = mock.Mock()
        state.param_begin = 2

        state.set_param(8)

        state.modifier.set_param.assert_called_once_with('format')

    def test_set_conversion_noconv_nocodes(self):
        state = format.ParseState(mock.Mock(**{
            '_get_conversion.return_value': 'fake_conversion',
        }), 'a format string')
        modifier = mock.Mock()
        state.modifier = modifier
        state.param_begin = 2
        state.reject = True
        state.code_last = True

        state.set_conversion(7)

        self.assertFalse(modifier.set_codes.called)
        state.fmt._get_conversion.assert_called_once_with('t', modifier)
        state.fmt.append_conv.assert_called_once_with('fake_conversion')
        self.assertEqual(state.param_begin, None)
        self.assertEqual(state.conv_begin, None)
        self.assertEqual(state.modifier, None)
        self.assertEqual(state.codes, [])
        self.assertEqual(state.reject, False)
        self.assertEqual(state.code_last, False)

    def test_set_conversion_withconv(self):
        state = format.ParseState(mock.Mock(**{
            '_get_conversion.return_value': 'fake_conversion',
        }), 'a format string')
        modifier = mock.Mock()
        state.modifier = modifier
        state.param_begin = 2
        state.conv_begin = 2
        state.reject = True
        state.code_last = True

        state.set_conversion(8)

        self.assertFalse(modifier.set_codes.called)
        state.fmt._get_conversion.assert_called_once_with('format', modifier)
        state.fmt.append_conv.assert_called_once_with('fake_conversion')
        self.assertEqual(state.param_begin, None)
        self.assertEqual(state.conv_begin, None)
        self.assertEqual(state.modifier, None)
        self.assertEqual(state.codes, [])
        self.assertEqual(state.reject, False)
        self.assertEqual(state.code_last, False)

    def test_set_conversion_withcodes(self):
        state = format.ParseState(mock.Mock(**{
            '_get_conversion.return_value': 'fake_conversion',
        }), 'a format string')
        modifier = mock.Mock()
        state.modifier = modifier
        state.param_begin = 2
        state.codes = [101, 202, 303]
        state.reject = 'reject'
        state.code_last = True

        state.set_conversion(7)

        modifier.set_codes.assert_called_once_with([101, 202, 303], 'reject')
        state.fmt._get_conversion.assert_called_once_with('t', modifier)
        state.fmt.append_conv.assert_called_once_with('fake_conversion')
        self.assertEqual(state.param_begin, None)
        self.assertEqual(state.conv_begin, None)
        self.assertEqual(state.modifier, None)
        self.assertEqual(state.codes, [])
        self.assertEqual(state.reject, False)
        self.assertEqual(state.code_last, False)

    def test_set_reject(self):
        state = format.ParseState('fmt', 'format')

        state.set_reject()

        self.assertEqual(state.reject, True)

    def test_set_code_short(self):
        state = format.ParseState('fmt', 'a 1')

        result = state.set_code(2)

        self.assertEqual(result, False)
        self.assertEqual(state.codes, [])
        self.assertEqual(state.ignore, 0)
        self.assertEqual(state.code_last, False)

    def test_set_code_bad(self):
        state = format.ParseState('fmt', 'a 10o')

        result = state.set_code(2)

        self.assertEqual(result, False)
        self.assertEqual(state.codes, [])
        self.assertEqual(state.ignore, 0)
        self.assertEqual(state.code_last, False)

    def test_set_code(self):
        state = format.ParseState('fmt', 'a 101')

        result = state.set_code(2)

        self.assertEqual(result, True)
        self.assertEqual(state.codes, [101])
        self.assertEqual(state.ignore, 2)
        self.assertEqual(state.code_last, True)

    def test_end_state_nostr(self):
        state = format.ParseState(mock.Mock(), 'format')
        state.str_begin = 6

        result = state.end_state()

        self.assertFalse(state.fmt.append_text.called)
        self.assertEqual(result, state.fmt)

    def test_end_state_longstack(self):
        state = format.ParseState(mock.Mock(), 'format')
        state.state = ['string', 'other']

        result = state.end_state()

        state.fmt.append_text.assert_called_once_with(
            "(Bad format string; ended in state 'other')")
        self.assertEqual(result, state.fmt)

    def test_end_state_wrongstate(self):
        state = format.ParseState(mock.Mock(), 'format')
        state.state = ['other']

        result = state.end_state()

        state.fmt.append_text.assert_called_once_with(
            "(Bad format string; ended in state 'other')")
        self.assertEqual(result, state.fmt)

    def test_end_state(self):
        state = format.ParseState(mock.Mock(), 'format')

        result = state.end_state()

        state.fmt.append_text.assert_called_once_with('format')
        self.assertEqual(result, state.fmt)

    @mock.patch.object(conversions, 'Modifier', return_value='some_conv')
    def test_conversion(self, mock_Modifier):
        state = format.ParseState('fmt', 'format')
        state.str_begin = 2
        state.param_begin = 2
        state.conv_begin = 2
        state.modifier = 'modifier'
        state.codes = [101, 202]
        state.reject = True
        state.code_last = True

        state.conversion(8)

        self.assertEqual(state.state, ['string', 'conversion'])
        self.assertEqual(state.str_begin, 8)
        self.assertEqual(state.param_begin, None)
        self.assertEqual(state.conv_begin, None)
        self.assertEqual(state.modifier, 'some_conv')
        self.assertEqual(state.codes, [])
        self.assertEqual(state.reject, False)
        self.assertEqual(state.code_last, False)
        mock_Modifier.assert_called_once_with()

    def test_escape(self):
        state = format.ParseState('fmt', 'format')
        state.str_begin = 2

        state.escape(8)

        self.assertEqual(state.state, ['string', 'escape'])
        self.assertEqual(state.str_begin, 8)

    def test_param(self):
        state = format.ParseState('fmt', 'format')
        state.param_begin = 2

        state.param(8)

        self.assertEqual(state.state, ['string', 'param'])
        self.assertEqual(state.param_begin, 8)

    def test_conv(self):
        state = format.ParseState('fmt', 'format')
        state.conv_begin = 2

        state.conv(8)

        self.assertEqual(state.state, ['string', 'conv'])
        self.assertEqual(state.conv_begin, 8)


class FakeConversion(conversions.Conversion):
    def convert(self, request, response, data):
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

    @mock.patch.object(format, 'ParseState')
    def test_parse_empty(self, mock_ParseState):
        fmt = format.Format.parse('')

        self.assertFalse(mock_ParseState.called)
        self.assertIsInstance(fmt, format.Format)
        self.assertEqual(fmt.conversions, [])

    @mock.patch.object(format.Format, '_get_conversion', FakeConversion)
    @mock.patch.object(format.Format, 'append_text',
                       lambda self, text: self.conversions.append(text))
    def test_parse(self):
        fmt = format.Format.parse(
            # Start off with some basic string stuff
            r'string %% \t \n \\'
            # Add in a simple conversion
            '%a'
            # Check the Apache compatibility
            '%<b'
            '%>c'
            # Try code stuff...
            '%101d'
            '%!202e'
            # How about multiple codes?
            '%303,404f'
            '%!505,606g'
            # What about an invalid code?
            '%10h'
            # Add a parameter
            '%{param}i'
            # Try a multi-character conversion spec
            '%(spec)'
        )

        self.assertEqual(fmt.conversions[:7],
                         ['string %', ' ', '\t', ' ', '\n', ' ', '\\'])

        expected = ['%a', '%b', '%c', '%101d', '%!202e', '%303,404f',
                    '%!505,606g', '%1']
        for conv, expect in zip(fmt.conversions[7:15], expected):
            self.assertIsInstance(conv, FakeConversion)
            self.assertEqual(str(conv), expect)

        self.assertEqual(fmt.conversions[15], '0h')

        expected = ['%{param}i', '%(spec)']
        for conv, expect in zip(fmt.conversions[16:], expected):
            self.assertIsInstance(conv, FakeConversion)
            self.assertEqual(str(conv), expect)

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
