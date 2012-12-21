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
import netaddr
import unittest2

from bark import proxy


class ParseIPTest(unittest2.TestCase):
    @mock.patch('netaddr.IPAddress', side_effect=ValueError)
    def test_parse_ip_value_error(self, mock_IPAddress):
        result = proxy._parse_ip(' 10.0.0.1 ')

        self.assertEqual(result, None)
        mock_IPAddress.assert_called_once_with('10.0.0.1')

    @mock.patch('netaddr.IPAddress', side_effect=netaddr.AddrFormatError)
    def test_parse_ip_addr_format_error(self, mock_IPAddress):
        result = proxy._parse_ip(' 10.0.0.1 ')

        self.assertEqual(result, None)
        mock_IPAddress.assert_called_once_with('10.0.0.1')

    @mock.patch('netaddr.IPAddress', return_value=mock.Mock(version=4))
    def test_parse_ip_v4(self, mock_IPAddress):
        result = proxy._parse_ip(' 10.0.0.1 ')

        self.assertEqual(id(result), id(mock_IPAddress.return_value))
        mock_IPAddress.assert_called_once_with('10.0.0.1')
        self.assertFalse(result.ipv4.called)

    @mock.patch('netaddr.IPAddress', return_value=mock.Mock(**{
        'version': 6,
        'ipv4.side_effect': netaddr.AddrConversionError,
    }))
    def test_parse_ip_v6_pure(self, mock_IPAddress):
        result = proxy._parse_ip(' 10.0.0.1 ')

        self.assertEqual(id(result), id(mock_IPAddress.return_value))
        mock_IPAddress.assert_called_once_with('10.0.0.1')
        result.ipv4.assert_called_once_with()

    @mock.patch('netaddr.IPAddress', return_value=mock.Mock(**{
        'version': 6,
        'ipv4.return_value': 'v4addr',
    }))
    def test_parse_ip_v6_v4(self, mock_IPAddress):
        result = proxy._parse_ip(' 10.0.0.1 ')

        self.assertEqual(result, 'v4addr')
        mock_IPAddress.assert_called_once_with('10.0.0.1')
        mock_IPAddress.return_value.ipv4.assert_called_once_with()


class ProxyTest(unittest2.TestCase):
    def test_init_restrictive(self):
        pxy = proxy.Proxy('10.0.0.1', restrictive=True)

        self.assertEqual(pxy.address, '10.0.0.1')
        self.assertFalse('207.97.209.147' in pxy.accepted)
        self.assertFalse('10.0.0.1' in pxy.accepted)
        self.assertFalse('127.0.0.1' in pxy.accepted)
        self.assertFalse('207.97.209.147' in pxy.excluded)
        self.assertTrue('10.0.0.1' in pxy.excluded)
        self.assertTrue('127.0.0.1' in pxy.excluded)

    def test_init_internal(self):
        pxy = proxy.Proxy('10.0.0.1', prohibit_internal=False)

        self.assertEqual(pxy.address, '10.0.0.1')
        self.assertTrue('207.97.209.147' in pxy.accepted)
        self.assertTrue('10.0.0.1' in pxy.accepted)
        self.assertTrue('127.0.0.1' in pxy.accepted)
        self.assertFalse('207.97.209.147' in pxy.excluded)
        self.assertFalse('10.0.0.1' in pxy.excluded)
        self.assertTrue('127.0.0.1' in pxy.excluded)

    def test_init_normal(self):
        pxy = proxy.Proxy('10.0.0.1')

        self.assertEqual(pxy.address, '10.0.0.1')
        self.assertTrue('207.97.209.147' in pxy.accepted)
        self.assertTrue('10.0.0.1' in pxy.accepted)
        self.assertTrue('127.0.0.1' in pxy.accepted)
        self.assertFalse('207.97.209.147' in pxy.excluded)
        self.assertTrue('10.0.0.1' in pxy.excluded)
        self.assertTrue('127.0.0.1' in pxy.excluded)

    def test_contains(self):
        pxy = proxy.Proxy('10.0.0.1')

        self.assertTrue('207.97.209.147' in pxy)
        self.assertFalse('10.0.0.1' in pxy)
        self.assertFalse('127.0.0.1' in pxy)

    @mock.patch.object(proxy.LOG, 'warn')
    def test_restrict(self, mock_warn):
        pxy = proxy.Proxy('10.0.0.1')

        self.assertTrue('207.97.209.147' in pxy)

        pxy.restrict('207.97.209.147')

        self.assertFalse('207.97.209.147' in pxy)

        self.assertFalse(mock_warn.called)

    @mock.patch.object(proxy, '_parse_ip', return_value=None)
    @mock.patch.object(proxy.LOG, 'warn')
    def test_restrict_badaddr(self, mock_warn, mock_parse_ip):
        pxy = proxy.Proxy('10.0.0.1')
        pxy.excluded = mock.Mock()

        pxy.restrict('207.97.209.147')

        self.assertFalse(pxy.excluded.add.called)
        mock_warn.assert_called_once_with(
            "Cannot restrict address '207.97.209.147' from proxy 10.0.0.1: "
            "invalid address")

    @mock.patch.object(proxy.LOG, 'warn')
    def test_accept(self, mock_warn):
        pxy = proxy.Proxy('10.0.0.1', restrictive=True)

        self.assertFalse('207.97.209.147' in pxy)

        pxy.accept('207.97.209.147')

        self.assertTrue('207.97.209.147' in pxy)

        self.assertFalse(mock_warn.called)

    @mock.patch.object(proxy, '_parse_ip', return_value=None)
    @mock.patch.object(proxy.LOG, 'warn')
    def test_accept_badaddr(self, mock_warn, mock_parse_ip):
        pxy = proxy.Proxy('10.0.0.1')
        pxy.accepted = mock.Mock()

        pxy.accept('207.97.209.147')

        self.assertFalse(pxy.accepted.add.called)
        mock_warn.assert_called_once_with(
            "Cannot add address '207.97.209.147' to proxy 10.0.0.1: "
            "invalid address")


class ProxyConfigTest(unittest2.TestCase):
    def test_init_noheader(self):
        self.assertRaises(KeyError, proxy.ProxyConfig, {})

    @mock.patch.object(proxy, 'Proxy', side_effect=lambda x: x)
    def test_init_noproxies(self, mock_Proxy):
        config = dict(header='x-forwarded-for')
        pc = proxy.ProxyConfig(config)

        mock_Proxy.assert_called_once_with('0.0.0.0/0')
        self.assertEqual(pc.header, 'x-forwarded-for')
        self.assertEqual(pc.proxies, None)
        self.assertEqual(pc.pseudo_proxy, '0.0.0.0/0')

    @mock.patch.object(proxy, '_parse_ip',
                       lambda x: None if x == 'none' else x)
    @mock.patch.object(proxy.LOG, 'warn')
    @mock.patch.object(proxy, 'Proxy', side_effect=lambda *args: args)
    def test_init_proxies_basic(self, mock_Proxy, mock_warn):
        config = dict(
            header='x-forwarded-for',
            proxies=('10.0.0.1,none,10.0.0.2, restrict(10.0.0.3) ,'
                     'internal(10.0.0.4)'),
        )
        pc = proxy.ProxyConfig(config)

        mock_Proxy.assert_has_calls([
            mock.call('10.0.0.1', False, True),
            mock.call('10.0.0.2', False, True),
            mock.call('10.0.0.3', True, True),
            mock.call('10.0.0.4', False, False),
        ])
        self.assertEqual(pc.header, 'x-forwarded-for')
        self.assertEqual(pc.proxies, {
            '10.0.0.1': ('10.0.0.1', False, True),
            '10.0.0.2': ('10.0.0.2', False, True),
            '10.0.0.3': ('10.0.0.3', True, True),
            '10.0.0.4': ('10.0.0.4', False, False),
        })
        self.assertEqual(pc.pseudo_proxy, None)
        mock_warn.assert_called_once_with(
            "Cannot understand proxy IP address 'none'")

    @mock.patch.object(proxy, '_parse_ip', lambda x: x)
    @mock.patch.object(proxy, 'Proxy')
    def test_init_proxies_rules(self, mock_Proxy):
        config = {
            'header': 'x-forwarded-for',
            'proxies': '10.0.0.1',
            '10.0.0.1': ('10.0.1.1,10.0.1.2, accept(10.0.1.3), '
                         'restrict(10.0.1.4)'),
        }
        pc = proxy.ProxyConfig(config)

        mock_Proxy.assert_has_calls([
            mock.call('10.0.0.1', False, True),
            mock.call().accept('10.0.1.1'),
            mock.call().accept('10.0.1.2'),
            mock.call().accept('10.0.1.3'),
            mock.call().restrict('10.0.1.4'),
        ])

    def test_validate_noproxy(self):
        pc = proxy.ProxyConfig(dict(header=''))
        pc.pseudo_proxy = None
        pc.proxies = {
            '10.0.0.1': ('10.0.1.1', '10.0.1.2', '10.0.1.3'),
        }

        self.assertEqual(pc.validate('10.0.0.2', '10.0.1.1'), False)

    def test_validate_proxy_noclient(self):
        pc = proxy.ProxyConfig(dict(header=''))
        pc.pseudo_proxy = None
        pc.proxies = {
            '10.0.0.1': ('10.0.1.1', '10.0.1.2', '10.0.1.3'),
        }

        self.assertEqual(pc.validate('10.0.0.1', '10.0.1.4'), False)

    def test_validate_proxy_withclient(self):
        pc = proxy.ProxyConfig(dict(header=''))
        pc.pseudo_proxy = None
        pc.proxies = {
            '10.0.0.1': ('10.0.1.1', '10.0.1.2', '10.0.1.3'),
        }

        self.assertEqual(pc.validate('10.0.0.1', '10.0.1.3'), True)

    def test_validate_pseudo_proxy_noclient(self):
        pc = proxy.ProxyConfig(dict(header=''))
        pc.pseudo_proxy = ('10.0.1.1', '10.0.1.2', '10.0.1.3')
        pc.proxies = None

        self.assertEqual(pc.validate('10.0.0.1', '10.0.1.4'), False)

    def test_validate_pseudo_proxy_withclient(self):
        pc = proxy.ProxyConfig(dict(header=''))
        pc.pseudo_proxy = ('10.0.1.1', '10.0.1.2', '10.0.1.3')
        pc.proxies = None

        self.assertEqual(pc.validate('10.0.0.1', '10.0.1.3'), True)

    @mock.patch.object(proxy, '_parse_ip')
    def test_call_noheader(self, mock_parse_ip):
        pc = proxy.ProxyConfig(dict(header='header'))
        request = mock.Mock(headers={}, environ=dict(REMOTE_ADDR='10.0.0.1'))

        result = pc(request)

        self.assertEqual(result, False)
        self.assertFalse(mock_parse_ip.called)
        self.assertEqual(request.headers, {})
        self.assertEqual(request.environ, dict(REMOTE_ADDR='10.0.0.1'))

    @mock.patch.object(proxy, '_parse_ip')
    def test_call_noremote(self, mock_parse_ip):
        pc = proxy.ProxyConfig(dict(header='header'))
        request = mock.Mock(headers=dict(header='10.0.1.1'), environ={})

        result = pc(request)

        self.assertEqual(result, False)
        self.assertFalse(mock_parse_ip.called)
        self.assertEqual(request.headers, dict(header='10.0.1.1'))
        self.assertEqual(request.environ, {})

    @mock.patch.object(proxy, '_parse_ip', return_value=None)
    def test_call_badremote(self, mock_parse_ip):
        pc = proxy.ProxyConfig(dict(header='header'))
        request = mock.Mock(
            headers=dict(header='10.0.1.1'),
            environ=dict(REMOTE_ADDR='10.0.0.1'),
        )

        result = pc(request)

        self.assertEqual(result, False)
        mock_parse_ip.assert_called_once_with('10.0.0.1')
        self.assertEqual(request.headers, dict(header='10.0.1.1'))
        self.assertEqual(request.environ, dict(REMOTE_ADDR='10.0.0.1'))

    @mock.patch.object(proxy, '_parse_ip', side_effect=lambda x: x)
    def test_call_noagents(self, mock_parse_ip):
        pc = proxy.ProxyConfig(dict(header='header'))
        request = mock.Mock(
            headers=dict(header=',,'),
            environ=dict(REMOTE_ADDR='10.0.0.1'),
        )

        result = pc(request)

        self.assertEqual(result, False)
        mock_parse_ip.assert_called_once_with('10.0.0.1')
        self.assertEqual(request.headers, dict(header=',,'))
        self.assertEqual(request.environ, dict(REMOTE_ADDR='10.0.0.1'))

    @mock.patch.object(proxy.ProxyConfig, 'validate', return_value=True)
    @mock.patch.object(proxy, '_parse_ip',
                       side_effect=lambda x: None if x == 'none' else x)
    def test_call_bad_agent(self, mock_parse_ip, mock_validate):
        pc = proxy.ProxyConfig(dict(header='header'))
        request = mock.Mock(
            headers=dict(header='10.0.1.1 , 10.0.1.2,none,10.0.1.3,10.0.1.4,'),
            environ=dict(REMOTE_ADDR='10.0.0.1'),
        )

        result = pc(request)

        self.assertEqual(result, True)
        self.assertEqual(mock_parse_ip.call_count, 4)
        mock_parse_ip.assert_has_calls([
            mock.call('10.0.0.1'),
            mock.call('10.0.1.4'),
            mock.call('10.0.1.3'),
            mock.call('none'),
        ])
        self.assertEqual(mock_validate.call_count, 2)
        mock_validate.assert_has_calls([
            mock.call('10.0.0.1', '10.0.1.4'),
            mock.call('10.0.1.4', '10.0.1.3'),
        ])
        self.assertEqual(request.headers,
                         dict(header='10.0.1.1,10.0.1.2,none'))
        self.assertEqual(request.environ, {
            'REMOTE_ADDR': '10.0.0.1',
            'bark.useragent_ip': '10.0.1.3',
            'bark.notes': {
                'remoteip-proxy-ip-list': '10.0.1.4,10.0.0.1',
            },
        })

    @mock.patch.object(proxy.ProxyConfig, 'validate',
                       side_effect=lambda x, y: (False if y == 'invalid'
                                                 else True))
    @mock.patch.object(proxy, '_parse_ip', side_effect=lambda x: x)
    def test_call_invalid_agent(self, mock_parse_ip, mock_validate):
        pc = proxy.ProxyConfig(dict(header='header'))
        request = mock.Mock(
            headers=dict(header=('10.0.1.1 , 10.0.1.2,invalid,'
                                 '10.0.1.3,10.0.1.4,')),
            environ=dict(REMOTE_ADDR='10.0.0.1'),
        )

        result = pc(request)

        self.assertEqual(result, True)
        self.assertEqual(mock_parse_ip.call_count, 4)
        mock_parse_ip.assert_has_calls([
            mock.call('10.0.0.1'),
            mock.call('10.0.1.4'),
            mock.call('10.0.1.3'),
            mock.call('invalid'),
        ])
        self.assertEqual(mock_validate.call_count, 3)
        mock_validate.assert_has_calls([
            mock.call('10.0.0.1', '10.0.1.4'),
            mock.call('10.0.1.4', '10.0.1.3'),
            mock.call('10.0.1.3', 'invalid'),
        ])
        self.assertEqual(request.headers,
                         dict(header='10.0.1.1,10.0.1.2,invalid'))
        self.assertEqual(request.environ, {
            'REMOTE_ADDR': '10.0.0.1',
            'bark.useragent_ip': '10.0.1.3',
            'bark.notes': {
                'remoteip-proxy-ip-list': '10.0.1.4,10.0.0.1',
            },
        })

    @mock.patch.object(proxy.ProxyConfig, 'validate', return_value=True)
    @mock.patch.object(proxy, '_parse_ip', side_effect=lambda x: x)
    def test_call_valid(self, mock_parse_ip, mock_validate):
        pc = proxy.ProxyConfig(dict(header='header'))
        request = mock.Mock(
            headers=dict(header=('10.0.1.1 , 10.0.1.2, 10.0.1.3,10.0.1.4,')),
            environ=dict(REMOTE_ADDR='10.0.0.1'),
        )

        result = pc(request)

        self.assertEqual(result, True)
        self.assertEqual(mock_parse_ip.call_count, 5)
        mock_parse_ip.assert_has_calls([
            mock.call('10.0.0.1'),
            mock.call('10.0.1.4'),
            mock.call('10.0.1.3'),
            mock.call('10.0.1.2'),
            mock.call('10.0.1.1'),
        ])
        self.assertEqual(mock_validate.call_count, 4)
        mock_validate.assert_has_calls([
            mock.call('10.0.0.1', '10.0.1.4'),
            mock.call('10.0.1.4', '10.0.1.3'),
            mock.call('10.0.1.3', '10.0.1.2'),
            mock.call('10.0.1.2', '10.0.1.1'),
        ])
        self.assertEqual(request.headers, {})
        self.assertEqual(request.environ, {
            'REMOTE_ADDR': '10.0.0.1',
            'bark.useragent_ip': '10.0.1.1',
            'bark.notes': {
                'remoteip-proxy-ip-list': ('10.0.1.2,10.0.1.3,'
                                           '10.0.1.4,10.0.0.1'),
            },
        })
