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

from bark import conversions


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
                isinstance(self.conversions[-1],
                           conversions.StringConversion)):
            self.conversions[-1].append(text)
        else:
            self.conversions.append(conversions.StringConversion(text))

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
        for conv, datum in zip(self.conversions, data):
            # Only include conversion if it's allowed
            if conv.modifier.accept(response.status_code):
                result.append(conv.convert(request, response, datum))
            else:
                result.append('-')

        return ''.join(result)
