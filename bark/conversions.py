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

        pass


class Format(object):
    def __init__(self):
        """
        Initialize a Format.
        """

        self.conversions = []

    def append_text(self, text):
        """
        Append static text to the Format.

        :param text: The text to append.
        """

        if (self.conversions and
            isinstance(self.conversions[-1], StringConversion)):
            self.conversions[-1].append(text)
        else:
            self.conversions.append(StringConversion(text))

    def append_conv(self, conv):
        """
        Append a conversion to the Format.

        :param conv: The conversion to append.
        """

        self.conversions.append(conv)

    def prepare(self, request):
        """
        Performs any preparations necessary for the Format.

        :param request: The webob Request object describing the
                        request.

        :returns: A list of dictionary values needed by the convert()
                  method.
        """

        data = []
        for conv in self.conversions:
            data.append(conv.prepare(request))

        return data

    def convert(self, request, response, data):
        """
        Performs the desired formatting.

        :param request: The webob Request object describing the
                        request.
        :param response: The webob Response object describing the
                         response.
        :param data: The data dictionary list returned by the
                     prepare() method.

        :returns: A string, the results of which are the desired
                  conversion.
        """

        result = []
        for idx, conv in enumerate(self.conversions):
            result.append(conv.convert(request, response, data[idx]))

        return ''.join(result)


class StringConversion(Conversion):
    def __init__(self, string):
        """
        Initialize a string conversion.

        :param string: The string to insert.
        """

        super(StringConversion, self).__init__(None, Modifier())
        self.string = string

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
