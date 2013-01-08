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

    def test_str_empty(self):
        mod = conversions.Modifier()

        self.assertEqual(str(mod), '')

    def test_str_codes_reject(self):
        mod = conversions.Modifier()
        mod.codes = set([101, 202])

        self.assertEqual(str(mod), '!101,202')

    def test_str_codes_noreject(self):
        mod = conversions.Modifier()
        mod.codes = set([101, 202])
        mod.reject = False

        self.assertEqual(str(mod), '101,202')

    def test_str_param(self):
        mod = conversions.Modifier()
        mod.param = 'param'

        self.assertEqual(str(mod), '{param}')

    def test_str_all(self):
        mod = conversions.Modifier()
        mod.codes = set([101, 202])
        mod.param = 'param'

        self.assertEqual(str(mod), '!101,202{param}')

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

    def test_str(self):
        conv = ConversionForTest('a', '{modifier}')

        self.assertEqual(str(conv), '%{modifier}a')

    def test_str_long(self):
        conv = ConversionForTest('conv', '{modifier}')

        self.assertEqual(str(conv), '%{modifier}(conv)')

    def test_prepare(self):
        conv = ConversionForTest('a', 'modifier')

        self.assertEqual(conv.prepare('request'), {})


class StringConversionTest(unittest2.TestCase):
    def test_init(self):
        conv = conversions.StringConversion("a string")

        self.assertEqual(conv.conv_chr, None)
        self.assertIsInstance(conv.modifier, conversions.Modifier)
        self.assertEqual(conv.modifier.codes, set())
        self.assertEqual(conv.modifier.reject, True)
        self.assertEqual(conv.string, "a string")

    def test_str(self):
        conv = conversions.StringConversion("a string")

        self.assertEqual(str(conv), 'a string')

    def test_append(self):
        conv = conversions.StringConversion("")

        conv.append("a string")

        self.assertEqual(conv.string, "a string")

    def test_convert(self):
        conv = conversions.StringConversion("a string")

        result = conv.convert('request', 'response', 'data')

        self.assertEqual(result, "a string")


class AddressConversionTest(unittest2.TestCase):
    def test_convert_noaddr(self):
        modifier = conversions.Modifier()
        conv = conversions.AddressConversion('a', modifier)
        request = mock.Mock(environ={})

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, '-')

    def test_convert_withaddr(self):
        modifier = conversions.Modifier()
        conv = conversions.AddressConversion('a', modifier)
        request = mock.Mock(environ=dict(REMOTE_ADDR="remote_address"))

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, 'remote_address')

    def test_convert_withuseragent(self):
        modifier = conversions.Modifier()
        conv = conversions.AddressConversion('a', modifier)
        request = mock.Mock(environ={
            'REMOTE_ADDR': 'remote_address',
            'bark.useragent_ip': 'useragent_address',
        })

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, 'useragent_address')

    def test_convert_withuseragent_inhibit(self):
        modifier = conversions.Modifier()
        modifier.set_param('c')
        conv = conversions.AddressConversion('a', modifier)
        request = mock.Mock(environ={
            'REMOTE_ADDR': 'remote_address',
            'bark.useragent_ip': 'useragent_address',
        })

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, 'remote_address')


class CookieConversionTest(unittest2.TestCase):
    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert_cookie1(self):
        modifier = conversions.Modifier()
        modifier.set_param('cookie1')
        conv = conversions.CookieConversion('C', modifier)
        request = mock.Mock(cookies=dict(cookie1='one', cookie2='two'))

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, 'one')

    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert_cookie2(self):
        modifier = conversions.Modifier()
        modifier.set_param('cookie2')
        conv = conversions.CookieConversion('C', modifier)
        request = mock.Mock(cookies=dict(cookie1='one', cookie2='two'))

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, 'two')


class EnvironmentConversionTest(unittest2.TestCase):
    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    @mock.patch.dict('os.environ', FOO="one", BAR="two")
    def test_convert_foo(self):
        modifier = conversions.Modifier()
        modifier.set_param('FOO')
        conv = conversions.EnvironmentConversion('e', modifier)

        result = conv.convert('request', 'response', 'data')

        self.assertEqual(result, 'one')

    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    @mock.patch.dict('os.environ', FOO="one", BAR="two")
    def test_convert_foo(self):
        modifier = conversions.Modifier()
        modifier.set_param('BAR')
        conv = conversions.EnvironmentConversion('e', modifier)

        result = conv.convert('request', 'response', 'data')

        self.assertEqual(result, 'two')


class FilenameConversionTest(unittest2.TestCase):
    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert(self):
        modifier = conversions.Modifier()
        conv = conversions.FilenameConversion('f', modifier)
        request = mock.Mock(path='/some/path/somewhere')

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, '/some/path/somewhere')


class FirstLineConversionTest(unittest2.TestCase):
    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert_nopass(self):
        modifier = conversions.Modifier()
        conv = conversions.FirstLineConversion('r', modifier)
        request = mock.Mock(
            url='http://example.com/some/path',
            method='GET',
            environ=dict(SERVER_PROTOCOL='HTTP/1.1'),
        )

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, 'GET http://example.com/some/path HTTP/1.1')

    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert_withpass_nohost_noport(self):
        modifier = conversions.Modifier()
        conv = conversions.FirstLineConversion('r', modifier)
        request = mock.Mock(
            url='http://klmitch:password@/some/path',
            method='GET',
            environ=dict(SERVER_PROTOCOL='HTTP/1.1'),
        )

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, 'GET http://klmitch:XXXXXXXX@/some/path '
                         'HTTP/1.1')

    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert_withpass_withhost_withport(self):
        modifier = conversions.Modifier()
        conv = conversions.FirstLineConversion('r', modifier)
        request = mock.Mock(
            url='http://klmitch:password@example.com:443/some/path',
            method='GET',
            environ=dict(SERVER_PROTOCOL='HTTP/1.1'),
        )

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, 'GET http://klmitch:XXXXXXXX@example.com:443'
                         '/some/path HTTP/1.1')


class HostnameConversionTest(unittest2.TestCase):
    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert_noaddr(self):
        modifier = conversions.Modifier()
        conv = conversions.HostnameConversion('h', modifier)
        request = mock.Mock(remote_addr=None)

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, '')

    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert_withaddr(self):
        modifier = conversions.Modifier()
        conv = conversions.HostnameConversion('h', modifier)
        request = mock.Mock(remote_addr='remote_addr')

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, 'remote_addr')


class KeepAliveConversionTest(unittest2.TestCase):
    def test_convert(self):
        modifier = conversions.Modifier()
        conv = conversions.KeepAliveConversion('k', modifier)

        result = conv.convert('request', 'response', 'data')

        self.assertEqual(result, '0')


class LocalAddressConversionTest(unittest2.TestCase):
    def test_convert(self):
        modifier = conversions.Modifier()
        conv = conversions.LocalAddressConversion('A', modifier)
        request = mock.Mock(environ=dict(SERVER_NAME='server_name'))

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, 'server_name')


class NoteConversionTest(unittest2.TestCase):
    def test_convert_withnote(self):
        modifier = conversions.Modifier()
        modifier.set_param('remoteip-proxy-ip-list')
        conv = conversions.NoteConversion('n', modifier)
        request = mock.Mock(environ={
            'bark.notes': {
                'remoteip-proxy-ip-list': "ip1,ip2",
            },
        })

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, 'ip1,ip2')

    def test_convert_nonote(self):
        modifier = conversions.Modifier()
        modifier.set_param('remoteip-proxy-ip-list')
        conv = conversions.NoteConversion('n', modifier)
        request = mock.Mock(environ={'bark.notes': {}})

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, '-')

    def test_convert_notesmissing(self):
        modifier = conversions.Modifier()
        modifier.set_param('remoteip-proxy-ip-list')
        conv = conversions.NoteConversion('n', modifier)
        request = mock.Mock(environ={})

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, '-')


class ProcessIDConversionTest(unittest2.TestCase):
    @mock.patch('os.getpid', return_value=12345)
    def test_convert_none(self, _mock_getpid):
        modifier = conversions.Modifier()
        conv = conversions.ProcessIDConversion('P', modifier)

        result = conv.convert('request', 'response', 'data')

        self.assertEqual(result, '12345')

    @mock.patch('os.getpid', return_value=12345)
    def test_convert_pid(self, _mock_getpid):
        modifier = conversions.Modifier()
        modifier.set_param('pid')
        conv = conversions.ProcessIDConversion('P', modifier)

        result = conv.convert('request', 'response', 'data')

        self.assertEqual(result, '12345')

    @mock.patch('thread.get_ident', return_value=12345)
    def test_convert_tid(self, _mock_get_ident):
        modifier = conversions.Modifier()
        modifier.set_param('tid')
        conv = conversions.ProcessIDConversion('P', modifier)

        result = conv.convert('request', 'response', 'data')

        self.assertEqual(result, '12345')

    @mock.patch('thread.get_ident', return_value=12345)
    def test_convert_hextid(self, _mock_get_ident):
        modifier = conversions.Modifier()
        modifier.set_param('hextid')
        conv = conversions.ProcessIDConversion('P', modifier)

        result = conv.convert('request', 'response', 'data')

        self.assertEqual(result, '0x3039')

    def test_convert_other(self):
        modifier = conversions.Modifier()
        modifier.set_param('other')
        conv = conversions.ProcessIDConversion('P', modifier)

        result = conv.convert('request', 'response', 'data')

        self.assertEqual(result, 'other')


class ProtocolConversionTest(unittest2.TestCase):
    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert(self):
        modifier = conversions.Modifier()
        conv = conversions.ProtocolConversion('H', modifier)
        request = mock.Mock(environ=dict(SERVER_PROTOCOL='HTTP/1.1'))

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, 'HTTP/1.1')


class QueryStringConversionTest(unittest2.TestCase):
    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert_noqstr(self):
        modifier = conversions.Modifier()
        conv = conversions.QueryStringConversion('q', modifier)
        request = mock.Mock(query_string=None)

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, '')

    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert_withqstr(self):
        modifier = conversions.Modifier()
        conv = conversions.QueryStringConversion('q', modifier)
        request = mock.Mock(query_string='i=1&b=2')

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, '?i=1&b=2')


class RemoteUserConversionTest(unittest2.TestCase):
    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert_remote_user_unset(self):
        modifier = conversions.Modifier()
        conv = conversions.RemoteUserConversion('u', modifier)
        request = mock.Mock(remote_user=None)

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, '-')

    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert_remote_user_empty(self):
        modifier = conversions.Modifier()
        conv = conversions.RemoteUserConversion('u', modifier)
        request = mock.Mock(remote_user='')

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, '""')

    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert_remote_user_set(self):
        modifier = conversions.Modifier()
        conv = conversions.RemoteUserConversion('u', modifier)
        request = mock.Mock(remote_user='klmitch')

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, 'klmitch')


class RequestHeaderConversionTest(unittest2.TestCase):
    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert_x_foo(self):
        modifier = conversions.Modifier()
        modifier.set_param('X-Foo')
        conv = conversions.RequestHeaderConversion('i', modifier)
        request = mock.Mock(headers={
            'X-Foo': 'one',
            'X-Bar': 'two',
        })

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, 'one')

    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert_x_bar(self):
        modifier = conversions.Modifier()
        modifier.set_param('X-Bar')
        conv = conversions.RequestHeaderConversion('i', modifier)
        request = mock.Mock(headers={
            'X-Foo': 'one',
            'X-Bar': 'two',
        })

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, 'two')


class RequestMethodConversionTest(unittest2.TestCase):
    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert(self):
        modifier = conversions.Modifier()
        conv = conversions.RequestMethodConversion('m', modifier)
        request = mock.Mock(method='GET')

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, 'GET')


class ResponseHeaderConversionTest(unittest2.TestCase):
    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert_x_foo(self):
        modifier = conversions.Modifier()
        modifier.set_param('X-Foo')
        conv = conversions.ResponseHeaderConversion('i', modifier)
        response = mock.Mock(headers={
            'X-Foo': 'one',
            'X-Bar': 'two',
        })

        result = conv.convert('request', response, 'data')

        self.assertEqual(result, 'one')

    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert_x_bar(self):
        modifier = conversions.Modifier()
        modifier.set_param('X-Bar')
        conv = conversions.ResponseHeaderConversion('i', modifier)
        response = mock.Mock(headers={
            'X-Foo': 'one',
            'X-Bar': 'two',
        })

        result = conv.convert('request', response, 'data')

        self.assertEqual(result, 'two')


class ResponseSizeConversionTest(unittest2.TestCase):
    def test_convert_0_lower(self):
        modifier = conversions.Modifier()
        conv = conversions.ResponseSizeConversion('b', modifier)
        response = mock.Mock(content_length=0)

        result = conv.convert('request', response, 'data')

        self.assertEqual(result, '-')

    def test_convert_0_upper(self):
        modifier = conversions.Modifier()
        conv = conversions.ResponseSizeConversion('B', modifier)
        response = mock.Mock(content_length=0)

        result = conv.convert('request', response, 'data')

        self.assertEqual(result, '0')

    def test_convert_non0_lower(self):
        modifier = conversions.Modifier()
        conv = conversions.ResponseSizeConversion('b', modifier)
        response = mock.Mock(content_length=1000)

        result = conv.convert('request', response, 'data')

        self.assertEqual(result, '1000')

    def test_convert_non0_upper(self):
        modifier = conversions.Modifier()
        conv = conversions.ResponseSizeConversion('B', modifier)
        response = mock.Mock(content_length=1000)

        result = conv.convert('request', response, 'data')

        self.assertEqual(result, '1000')


class ServerNameConversionTest(unittest2.TestCase):
    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert_lower(self):
        modifier = conversions.Modifier()
        conv = conversions.ServerNameConversion('v', modifier)
        request = mock.Mock(environ=dict(HTTP_HOST='www.example.com'))

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, 'www.example.com')

    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert_upper(self):
        modifier = conversions.Modifier()
        conv = conversions.ServerNameConversion('V', modifier)
        request = mock.Mock(environ=dict(HTTP_HOST='www.example.com'))

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, 'www.example.com')


class PortConversionTest(unittest2.TestCase):
    def test_convert_none(self):
        modifier = conversions.Modifier()
        conv = conversions.PortConversion('p', modifier)
        request = mock.Mock(environ=dict(SERVER_PORT='1234'))

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, '1234')

    def test_convert_canonical(self):
        modifier = conversions.Modifier()
        modifier.set_param('canonical')
        conv = conversions.PortConversion('p', modifier)
        request = mock.Mock(environ=dict(SERVER_PORT='1234'))

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, '1234')

    def test_convert_local(self):
        modifier = conversions.Modifier()
        modifier.set_param('local')
        conv = conversions.PortConversion('p', modifier)
        request = mock.Mock(environ=dict(SERVER_PORT='1234'))

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, '1234')

    def test_convert_remote_unset(self):
        modifier = conversions.Modifier()
        modifier.set_param('remote')
        conv = conversions.PortConversion('p', modifier)
        request = mock.Mock(environ=dict(SERVER_PORT='1234'))

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, '-')

    def test_convert_remote_set(self):
        modifier = conversions.Modifier()
        modifier.set_param('remote')
        conv = conversions.PortConversion('p', modifier)
        request = mock.Mock(environ=dict(SERVER_PORT='1234',
                                         REMOTE_PORT='4321'))

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, '4321')

    def test_convert_other(self):
        modifier = conversions.Modifier()
        modifier.set_param('other')
        conv = conversions.PortConversion('p', modifier)
        request = mock.Mock(environ=dict(SERVER_PORT='1234',
                                         REMOTE_PORT='4321'))

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, '-')


class ServeTimeConversionTest(unittest2.TestCase):
    @mock.patch('time.time', return_value=1355786023.072341)
    def test_prepare(self, _mock_time):
        modifier = conversions.Modifier()
        conv = conversions.ServeTimeConversion('T', modifier)

        result = conv.prepare('request')

        self.assertEqual(result, {'start': 1355786023.072341})

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_seconds(self, _mock_time):
        modifier = conversions.Modifier()
        conv = conversions.ServeTimeConversion('T', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '110')

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_microseconds(self, _mock_time):
        modifier = conversions.Modifier()
        conv = conversions.ServeTimeConversion('D', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '110705979')


class StatusConversionTest(unittest2.TestCase):
    def test_convert(self):
        modifier = conversions.Modifier()
        conv = conversions.StatusConversion('s', modifier)
        response = mock.Mock(status_code=200)

        result = conv.convert('request', response, 'data')

        self.assertEqual(result, '200')


class TimeConversionTest(unittest2.TestCase):
    @mock.patch('time.time', return_value=1355786023.072341)
    def test_prepare(self, _mock_time):
        modifier = conversions.Modifier()
        conv = conversions.TimeConversion('t', modifier)

        result = conv.prepare('request')

        self.assertEqual(result, {'start': 1355786023.072341})

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_fmt_none(self, _mock_time):
        modifier = conversions.Modifier()
        conv = conversions.TimeConversion('t', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '[17/Dec/2012:23:13:43 +0000]')

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_fmt_begin(self, _mock_time):
        modifier = conversions.Modifier()
        modifier.set_param('begin')
        conv = conversions.TimeConversion('t', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '[17/Dec/2012:23:13:43 +0000]')

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_fmt_end(self, _mock_time):
        modifier = conversions.Modifier()
        modifier.set_param('end')
        conv = conversions.TimeConversion('t', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '[17/Dec/2012:23:15:33 +0000]')

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_fmt_iso8601(self, _mock_time):
        modifier = conversions.Modifier()
        modifier.set_param('%Y-%m-%dT%H:%M:%SZ')
        conv = conversions.TimeConversion('t', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '2012-12-17T23:13:43Z')

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_fmt_begin_iso8601(self, _mock_time):
        modifier = conversions.Modifier()
        modifier.set_param('begin:%Y-%m-%dT%H:%M:%SZ')
        conv = conversions.TimeConversion('t', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '2012-12-17T23:13:43Z')

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_fmt_end_iso8601(self, _mock_time):
        modifier = conversions.Modifier()
        modifier.set_param('end:%Y-%m-%dT%H:%M:%SZ')
        conv = conversions.TimeConversion('t', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '2012-12-17T23:15:33Z')

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_fmt_sec(self, _mock_time):
        modifier = conversions.Modifier()
        modifier.set_param('sec')
        conv = conversions.TimeConversion('t', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '1355786023')

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_fmt_begin_sec(self, _mock_time):
        modifier = conversions.Modifier()
        modifier.set_param('begin:sec')
        conv = conversions.TimeConversion('t', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '1355786023')

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_fmt_end_sec(self, _mock_time):
        modifier = conversions.Modifier()
        modifier.set_param('end:sec')
        conv = conversions.TimeConversion('t', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '1355786133')

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_fmt_msec(self, _mock_time):
        modifier = conversions.Modifier()
        modifier.set_param('msec')
        conv = conversions.TimeConversion('t', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '1355786023072')

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_fmt_begin_msec(self, _mock_time):
        modifier = conversions.Modifier()
        modifier.set_param('begin:msec')
        conv = conversions.TimeConversion('t', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '1355786023072')

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_fmt_end_msec(self, _mock_time):
        modifier = conversions.Modifier()
        modifier.set_param('end:msec')
        conv = conversions.TimeConversion('t', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '1355786133778')

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_fmt_usec(self, _mock_time):
        modifier = conversions.Modifier()
        modifier.set_param('usec')
        conv = conversions.TimeConversion('t', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '1355786023072341')

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_fmt_begin_usec(self, _mock_time):
        modifier = conversions.Modifier()
        modifier.set_param('begin:usec')
        conv = conversions.TimeConversion('t', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '1355786023072341')

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_fmt_end_usec(self, _mock_time):
        modifier = conversions.Modifier()
        modifier.set_param('end:usec')
        conv = conversions.TimeConversion('t', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '1355786133778320')

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_fmt_msec_frac(self, _mock_time):
        modifier = conversions.Modifier()
        modifier.set_param('msec_frac')
        conv = conversions.TimeConversion('t', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '072')

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_fmt_begin_msec_frac(self, _mock_time):
        modifier = conversions.Modifier()
        modifier.set_param('begin:msec_frac')
        conv = conversions.TimeConversion('t', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '072')

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_fmt_end_msec_frac(self, _mock_time):
        modifier = conversions.Modifier()
        modifier.set_param('end:msec_frac')
        conv = conversions.TimeConversion('t', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '778')

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_fmt_usec_frac(self, _mock_time):
        modifier = conversions.Modifier()
        modifier.set_param('usec_frac')
        conv = conversions.TimeConversion('t', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '072341')

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_fmt_begin_usec_frac(self, _mock_time):
        modifier = conversions.Modifier()
        modifier.set_param('begin:usec_frac')
        conv = conversions.TimeConversion('t', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '072341')

    @mock.patch('time.time', return_value=1355786133.77832)
    def test_convert_fmt_end_usec_frac(self, _mock_time):
        modifier = conversions.Modifier()
        modifier.set_param('end:usec_frac')
        conv = conversions.TimeConversion('t', modifier)
        data = {'start': 1355786023.072341}

        result = conv.convert('request', 'response', data)

        self.assertEqual(result, '778320')


class UnavailableConversionTest(unittest2.TestCase):
    def test_convert(self):
        modifier = conversions.Modifier()
        conv = conversions.UnavailableConversion('l', modifier)

        result = conv.convert('request', 'response', 'data')

        self.assertEqual(result, '-')


class URLConversionTest(unittest2.TestCase):
    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert(self):
        modifier = conversions.Modifier()
        conv = conversions.URLConversion('U', modifier)
        request = mock.Mock(path='/some/path')

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, '/some/path')


class WSGIEnvironmentConversionTest(unittest2.TestCase):
    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert_foo(self):
        modifier = conversions.Modifier()
        modifier.set_param('test.foo')
        conv = conversions.WSGIEnvironmentConversion('w', modifier)
        request = mock.Mock(environ={'test.foo': 'one', 'test.bar': 'two'})

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, 'one')

    @mock.patch.object(conversions.Conversion, 'escape', lambda cls, x: x)
    def test_convert_bar(self):
        modifier = conversions.Modifier()
        modifier.set_param('test.bar')
        conv = conversions.WSGIEnvironmentConversion('w', modifier)
        request = mock.Mock(environ={'test.foo': 'one', 'test.bar': 'two'})

        result = conv.convert(request, 'response', 'data')

        self.assertEqual(result, 'two')
