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

import netaddr


LOG = logging.getLogger('bark')


_martian = netaddr.IPSet([
    netaddr.ip.IPV4_LOOPBACK,
    netaddr.ip.IPV4_MULTICAST,
    netaddr.ip.IPV4_6TO4,
    netaddr.ip.IPV6_LOOPBACK,
    netaddr.ip.IPV6_MULTICAST,
])
_internal = netaddr.IPSet(netaddr.ip.IPV4_PRIVATE +
                          netaddr.ip.IPV6_PRIVATE)


def _parse_ip(addr):
    """
    Helper function to convert an address into an IPAddress object.
    Canonicalizes IPv6-mapped (or compatible) IPv4 addresses into IPv4
    addresses.  Returns None if the address cannot be parsed.
    """

    # Parse the IP address
    try:
        address = netaddr.IPAddress(addr)
    except (ValueError, netaddr.AddrFormatError):
        return None

    # Canonicalize it, if possible
    if address.version == 6:
        try:
            return address.ipv4()
        except netaddr.AddrConversionError:
            pass

    return address


class Proxy(object):
    def __init__(self, address, restrictive=False, prohibit_internal=True):
        """
        Initialize a Proxy object.  Sets the IP address of the proxy
        and initializes the list of IP addresses from which proxy
        attempts are permitted, under control of the 'restrictive' and
        'prohibit_internal' options.  Note that some IP addresses are
        always initialized as prohibited, e.g., 127.0.0.0/8; this can
        be changed by adding them back with the accept() method.

        :param address: The IP address of the proxy.
        :param restrictive: If True, this proxy may only introduce
                            clients from ranges explicitly declared
                            through the accept() method.  Defaults to
                            False.
        :param prohibit_internal: If restrictive is True, this
                                  argument is ignored.  Otherwise, if
                                  True, reserved internal IP ranges
                                  (e.g., 10.0.0.0/8) are prohibited.
                                  Defaults to True.
        """

        self.address = netaddr.IPAddress(address)

        # Set up the valid remote IPs
        if restrictive:
            # Use an empty IPSet
            self.remotes = netaddr.IPSet()
        else:
            self.remotes = netaddr.IPSet(['0.0.0.0/0', '::/0']) - _martian

            # Drop the internal addresses
            if prohibit_internal:
                self.remotes -= _internal

    def restrict(self, addr):
        """
        Drop an address from the set of addresses this proxy is
        permitted to introduce.

        :param addr: The address to remove.
        """

        # Remove the address from the set
        ip_addr = _parse_ip(addr)
        if ip_addr is None:
            LOG.warn("Cannot restrict address %r from proxy %s: "
                     "invalid address" % (addr, self.address))
        else:
            self.remotes.remove(addr)

    def accept(self, addr):
        """
        Add an address to the set of addresses this proxy is permitted
        to introduce.

        :param addr: The address to add.
        """

        # Add the address to the set
        ip_addr = _parse_ip(addr)
        if ip_addr is None:
            LOG.warn("Cannot add address %r to proxy %s: "
                     "invalid address" % (addr, self.address))
        else:
            self.remotes.add(addr)

    def permitted(self, addr):
        """
        Tests whether an address is permitted for this proxy.

        :param addr: The address to test.  Must be an IPAddress
                     object.

        :returns: True if the address is permitted for this proxy.
        """

        # Test if address is permitted
        return addr in self.remotes


class ProxyConfig(object):
    def __init__(self, config):
        """
        Initialize a ProxyConfig.

        :param config: A dictionary containing the proxy
                       configuration.
        """

        # First, determine the header to use; this will raise a
        # KeyError if not configured, which will trigger
        # bark_factory() to log an appropriate warning
        self.header = config['header']

        # Next, determine what the acceptable proxies are
        if 'proxies' not in config:
            self.proxies = None
            self.pseudo_proxy = Proxy('0.0.0.0/0')
            return

        # We have a list of proxies, so process it
        self.proxies = {}
        self.pseudo_proxy = None

        for pxy_addr in (pxy.strip() for pxy in config['proxies'].split(',')):
            # Determine what kind of proxy is desired
            if pxy_addr.startswith('restrict(') and pxy_addr[-1] == ')':
                restrictive = True
                prohibit_internal = True
                pxy_addr = pxy_addr[9:-1]
            elif pxy_addr.startswith('internal(') and pxy_addr[-1] == ')':
                restrictive = False
                prohibit_internal = False
                pxy_addr = pxy_addr[9:-1]
            else:
                restrictive = False
                prohibit_internal = True

            # Now create the proxy
            addr = _parse_ip(pxy_addr)
            if addr is None:
                LOG.warn("Cannot understand proxy IP address %r" % pxy_addr)
                continue

            proxy = Proxy(addr, restrictive, prohibit_internal)
            self.proxies[addr] = proxy

            # Check if there are any IP rules for the proxy
            if pxy_addr in config:
                for rule in (r.strip() for r in config[pxy_addr].split(',')):
                    # Determine what kind of rule is desired
                    update = proxy.accept
                    if rule.startswith('restrict(') and rule[-1] == ')':
                        update = proxy.restrict
                        rule = rule[9:-1]
                    elif rule.startswith('accept(') and rule[-1] == ')':
                        rule = rule[7:-1]

                    # Add the rule to the proxy
                    update(rule)

    def __call__(self, request):
        """
        Handle proxy information in the request.

        :param request: A Request object.
        """

        pass  # XXX
