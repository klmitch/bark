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

import ConfigParser
import logging

import webob.dec

import bark.format
import bark.handlers
import bark.proxy


LOG = logging.getLogger('bark')


def bark_filter(global_conf, **local_conf):
    """
    Factory function for Bark.  Returns a function which, when passed
    the application, returns an instance of BarkMiddleware.

    :param global_conf: The global configuration, from the [DEFAULT]
                        section of the PasteDeploy configuration file.
    :param local_conf: The local configuration, from the filter
                       section of the PasteDeploy configuration file.
    """

    # First, parse the configuration
    conf_file = None
    sections = {}
    for key, value in local_conf.items():
        # 'config' key causes a load of a configuration file; settings
        # in the local_conf will override settings in the
        # configuration file, however
        if key == 'config':
            conf_file = value
        elif '.' in key:
            sect, _sep, opt = key.partition('.')
            sect_dict = sections.setdefault(sect, {})
            sect_dict[opt] = value  # note: a string

    # Now that we've loaded local_conf, process conf_file (if any)
    if conf_file:
        cp = ConfigParser.SafeConfigParser()
        cp.read([conf_file])
        for sect in cp.sections():
            for opt, value in cp.options(sect):
                sect_dict = sections.setdefault(sect, {})
                # By using setdefault(), we allow local_conf to
                # override the configuration file
                sect_dict.setdefault(opt, value)

    # OK, the configuration is all read; next step is to turn the
    # configuration into logging handlers
    handlers = {}
    proxies = None
    for sect, sect_dict in sections.items():
        if sect == 'proxies':
            # Reserved for proxy configuration
            try:
                proxies = bark.proxy.ProxyConfig(sect_dict)
            except KeyError as exc:
                LOG.warn("Cannot configure proxy handling: option %s is "
                         "missing from the proxy configuration" % exc)
            continue  # Pragma: nocover

        # First, determine the logging format
        try:
            format = bark.format.Format.parse(sect_dict.pop('format'))
        except KeyError:
            LOG.warn("No format specified for log %r; skipping." % sect)
            continue

        # Next, determine the handler type
        handle_type = sect_dict.pop('type', 'file')

        # Now, let's construct a handler; this will be a callable
        # taking the formatted message to log
        try:
            handler = bark.handlers.get_handler(handle_type, sect, sect_dict)
        except Exception as exc:
            LOG.warn("Cannot load handler of type %r for log %r: %s" %
                     (handle_type, sect, exc))
            continue

        # We now have a handler and a format; bundle them up
        handlers[sect] = (format, handler)

    # Construct the wrapper which is going to instantiate the
    # middleware
    def wrapper(app):
        return BarkMiddleware(app, handlers, proxies)

    return wrapper


class BarkMiddleware(object):
    def __init__(self, app, handlers, proxies):
        """
        Initialize the Bark middleware.

        :param app: The WSGI application.
        :param handlers: A dictionary of logging handlers, used to
                         emit the formatted log messages.
        :param proxies: A ProxyConfig object, containing proxy IP
                        information.  This is used to determine the
                        useragent IP address in the face of proxy
                        forwarding.  If None, proxy handling is
                        disabled.
        """

        self.app = app
        self.handlers = handlers
        self.proxies = proxies

    @webob.dec.wsgify
    def __call__(self, request):
        """
        Process a WSGI request, emitting log output as appropriate.

        :param request: The Request object provided by WebOb.
        """

        data = {}

        # Determine the useragent IP
        if self.proxies:
            self.proxies(request)

        # Start by preparing all the formatters
        for log, (format, handler) in self.handlers.items():
            data[log] = format.prepare(request)

        # Now, let's call the application
        response = request.get_response(self.app)

        # Now, format and log the messages
        for log, (format, handler) in self.handlers.items():
            result = format.convert(request, response, data[log])

            # Emit with the handler
            handler(result)

        return response
