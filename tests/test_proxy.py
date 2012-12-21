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
