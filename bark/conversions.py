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

import abc
from curses import ascii
import os
import thread
import time
import urlparse


class Modifier(object):
    def __init__(self):
        """
        Initialize a Modifier object.
        """

        # These two work together; if 'reject' is True, only codes
        # that are NOT in 'codes' will format, otherwise, only codes
        # that ARE in 'codes' will format.
        self.codes = set()
        self.reject = True

        # Parameter for the conversion; used with e.g., %i to specify
        # desired header
        self.param = None

    def __str__(self):
        """
        Construct a string representation of this conversion modifier.
        """

        # Start off with the empty string
        result = ''

        # Add the code restrictions
        if self.codes:
            if self.reject:
                result += '!'
            result += ','.join(str(c) for c in sorted(self.codes))

        # Now, add the parameter
        if self.param:
            result += '{%s}' % self.param

        return result

    def set_codes(self, codes, reject=False):
        """
        Set the accepted or rejected codes codes list.

        :param codes: A list of the response codes.
        :param reject: If True, the listed codes will be rejected, and
                       the conversion will format as "-"; if False,
                       only the listed codes will be accepted, and the
                       conversion will format as "-" for all the
                       others.
        """

        self.codes = set(codes)
        self.reject = reject

    def set_param(self, param):
        """
        Set the parameter for the conversion.

        :param param: The string value of the parameter.
        """

        self.param = param

    def accept(self, code):
        """
        Determine whether to accept the given code.

        :param code: The response code.

        :returns: True if the code should be accepted, False
                  otherwise.
        """

        if code in self.codes:
            return not self.reject
        return self.reject


class EscapeDict(dict):
    def __missing__(self, key):
        return '\\x%02x' % ord(key)


class Conversion(object):
    __metaclass__ = abc.ABCMeta

    _escapes = EscapeDict({
        "\b": '\\b',
        "\n": '\\n',
        "\r": '\\r',
        "\t": '\\t',
        "\v": '\\v',
        "\\": '\\\\',
        '"': '\\"',
    })

    @staticmethod
    def _needescape(c):
        """
        Return True if character needs escaping, else False.
        """

        return not ascii.isprint(c) or c == '"' or c == '\\' or ascii.isctrl(c)

    @classmethod
    def escape(cls, string):
        """
        Utility method to produce an escaped version of a given
        string.

        :param string: The string to escape.

        :returns: The escaped version of the string.
        """

        return ''.join([cls._escapes[c] if cls._needescape(c) else c
                        for c in string.encode('utf8')])

    def __init__(self, conv_chr, modifier):
        """
        Initialize a Conversion object.

        :param conv_chr: The conversion character.
        :param modifier: The format modifier applied to this
                         conversion.
        """

        self.conv_chr = conv_chr
        self.modifier = modifier

    def __str__(self):
        """
        Construct a string representation of this conversion.
        """

        if len(self.conv_chr) == 1:
            return "%%%s%s" % (self.modifier, self.conv_chr)
        return "%%%s(%s)" % (self.modifier, self.conv_chr)

    def prepare(self, request):
        """
        Performs any preparation necessary for the Conversion.

        :param request: The webob Request object describing the
                        request.

        :returns: A (possibly empty) dictionary of values needed by
                  the convert() method.
        """

        return {}

    @abc.abstractmethod
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        pass  # Pragma: nocover


class StringConversion(Conversion):
    def __init__(self, string):
        """
        Initialize a string conversion.

        :param string: The string to insert.
        """

        super(StringConversion, self).__init__(None, Modifier())
        self.string = string

    def __str__(self):
        """
        Return a string representation of this StringConversion.
        """

        return self.string

    def append(self, text):
        """
        Append a string to the string in this StringConversion.

        :param text: The string to be appended.
        """

        self.string += text

    def convert(self, request, response, data):
        """
        Perform the string conversion by returning the string.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        return self.string


class AddressConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        client_addr = request.environ.get('REMOTE_ADDR', '-')
        if (self.modifier.param != 'c' and
                'bark.useragent_ip' in request.environ):
            client_addr = request.environ['bark.useragent_ip']

        return client_addr


class CookieConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        return self.escape(request.cookies.get(self.modifier.param, '-'))


class EnvironmentConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        return self.escape(os.environ.get(self.modifier.param, '-'))


class FilenameConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        return self.escape(request.path)


class FirstLineConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        # Chop up the URL
        uri = urlparse.urlparse(request.url)

        # If there's a password, recompute the URI without it
        if uri.password:
            netloc = "%s:%s@" % (uri.username or "", "XXXXXXXX")
            if uri.hostname:
                netloc += uri.hostname
            if uri.port is not None:
                netloc += ":%d" % uri.port

            uri = urlparse.ParseResult(uri[0], netloc, uri[2], uri[3],
                                       uri[4], uri[5])

        return self.escape("%s %s %s" % (request.method, uri.geturl(),
                                         request.environ['SERVER_PROTOCOL']))


class HostnameConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        return self.escape(request.remote_addr or "")


class KeepAliveConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        return "0"


class LocalAddressConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        # For eventlet WSGI server, this will be the server IP address
        return request.environ['SERVER_NAME']


class NoteConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        # Notes are in bark.notes dictionary
        return self.escape(request.environ.get('bark.notes', {}).get(
            self.modifier.param, '-'))


class ProcessIDConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        if self.modifier.param is None or self.modifier.param == 'pid':
            return str(os.getpid())
        elif self.modifier.param == 'tid':
            return str(thread.get_ident())
        elif self.modifier.param == 'hextid':
            return hex(thread.get_ident())
        return self.modifier.param


class ProtocolConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        return self.escape(request.environ['SERVER_PROTOCOL'])


class QueryStringConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        qstr = request.query_string

        return self.escape('?%s' % qstr) if qstr else ''


class RemoteUserConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        # None specified
        if request.remote_user is None:
            return "-"
        elif not request.remote_user:
            # Empty string...
            return '""'
        return self.escape(request.remote_user)


class RequestHeaderConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        return self.escape(request.headers.get(self.modifier.param, ''))


class RequestMethodConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        return self.escape(request.method)


class ResponseHeaderConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        return self.escape(response.headers.get(self.modifier.param, ''))


class ResponseSizeConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        size = response.content_length
        if not size:
            size = "-" if self.conv_chr == 'b' else 0

        return str(size)


class ServerNameConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        return self.escape(request.environ['HTTP_HOST'])


class PortConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        if self.modifier.param in (None, 'canonical', 'local'):
            return str(request.environ['SERVER_PORT'])
        elif self.modifier.param == 'remote':
            return str(request.environ.get('REMOTE_PORT', '-'))

        return "-"


class ServeTimeConversion(Conversion):
    def prepare(self, request):
        """
        Performs any preparation necessary for the Conversion.

        :param request: The webob Request object describing the
                        request.

        :returns: A (possibly empty) dictionary of values needed by
                  the convert() method.
        """

        return {'start': time.time()}

    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        delta = time.time() - data['start']

        if self.conv_chr == 'D':
            delta *= 1000000

        return str(int(delta))


class StatusConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        return str(response.status_code)


class TimeConversion(Conversion):
    def prepare(self, request):
        """
        Performs any preparation necessary for the Conversion.

        :param request: The webob Request object describing the
                        request.

        :returns: A (possibly empty) dictionary of values needed by
                  the convert() method.
        """

        return {'start': time.time()}

    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        # Determine which time to use
        fmtstr = self.modifier.param
        if fmtstr is None:
            log_time = data['start']
        elif fmtstr == 'begin' or fmtstr.startswith('begin:'):
            log_time = data['start']
            if fmtstr == 'begin':
                fmtstr = None
            else:
                fmtstr = fmtstr[len('begin:'):]
        elif fmtstr == 'end' or fmtstr.startswith('end:'):
            log_time = time.time()
            if fmtstr == 'end':
                fmtstr = None
            else:
                fmtstr = fmtstr[len('end:'):]
        else:
            log_time = data['start']

        # Next, determine the format to use
        if fmtstr is None:
            fmtstr = "[%d/%b/%Y:%H:%M:%S %z]"
        elif fmtstr in ('sec', 'msec', 'usec', 'msec_frac', 'usec_frac'):
            mult = 1
            fld_len = 0

            # Handle microseconds and milliseconds
            if fmtstr.startswith('usec'):
                mult = 1000000
                fld_len = 6
            elif fmtstr.startswith('msec'):
                mult = 1000
                fld_len = 3

            # Adjust for request for fractions
            if fmtstr.endswith('_frac'):
                log_time = int((log_time * mult) - (int(log_time) * mult))
            else:
                log_time = int(log_time * mult)
                fld_len = 0

            # Return the formatted result
            return "%0*d" % (fld_len, log_time)

        return time.strftime(fmtstr, time.gmtime(log_time))


class UnavailableConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        return "-"


class URLConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        return self.escape(request.path)


class WSGIEnvironmentConversion(Conversion):
    def convert(self, request, response, data):
        """
        Performs the desired Conversion.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary returned by the prepare()
                     method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        return self.escape(str(request.environ.get(self.modifier.param, '-')))
