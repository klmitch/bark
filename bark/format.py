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

import pkg_resources

from bark import conversions


class ParseState(object):
    def __init__(self, fmt, format):
        """
        Initialize a parser state.

        :param fmt: An initial Format instance to parse into.
        :param format: The full format string.
        """

        self.fmt = fmt
        self.format = format

        self.state = ['string']
        self.str_begin = 0
        self.param_begin = None
        self.conv_begin = None
        self.modifier = None
        self.codes = []
        self.reject = False
        self.ignore = 0
        self.code_last = False

    def __eq__(self, other):
        """
        Compare the parser state to a desired state.

        :param other: The other state.
        """

        return self.state[-1] == other

    def pop_state(self, idx=None):
        """
        Pops off the most recent state.

        :param idx: If provided, specifies the index at which the next
                    string begins.
        """

        self.state.pop()

        if idx is not None:
            self.str_begin = idx

    def check_ignore(self):
        """
        Returns True if the character should be ignored.
        """

        if self.ignore:
            self.ignore -= 1
            return True
        return False

    def set_ignore(self, count):
        """
        Sets the number of characters to ignore.
        """

        self.ignore += count

    def add_text(self, end, next=None):
        """
        Adds the text from string beginning to the specified ending
        index to the format.

        :param end: The ending index of the string.
        :param next: The next string begin index.  If None, the string
                     index will not be updated.
        """

        if self.str_begin != end:
            self.fmt.append_text(self.format[self.str_begin:end])

        if next is not None:
            self.str_begin = next

    def add_escape(self, idx, char):
        """
        Translates and adds the escape sequence.

        :param idx: Provides the ending index of the escape sequence.
        :param char: The actual character that was escaped.
        """

        self.fmt.append_text(self.fmt._unescape.get(
            self.format[self.str_begin:idx], char))

    def set_param(self, idx):
        """
        Adds the parameter to the conversion modifier.

        :param idx: Provides the ending index of the parameter string.
        """

        self.modifier.set_param(self.format[self.param_begin:idx])

    def set_conversion(self, idx):
        """
        Adds the conversion to the format.

        :param idx: The ending index of the conversion name.
        """

        # First, determine the name
        if self.conv_begin:
            name = self.format[self.conv_begin:idx]
        else:
            name = self.format[idx]

        # Next, add the status code modifiers, as needed
        if self.codes:
            self.modifier.set_codes(self.codes, self.reject)

        # Append the conversion to the format
        self.fmt.append_conv(self.fmt._get_conversion(name, self.modifier))

        # Clear the conversion data
        self.param_begin = None
        self.conv_begin = None
        self.modifier = None
        self.codes = []
        self.reject = False
        self.code_last = False

    def set_reject(self):
        """
        Sets the reject flag for the conversion being considered.
        """

        self.reject = True

    def set_code(self, idx):
        """
        Sets a code to be filtered on for the conversion.  Note that
        this also sets the 'code_last' attribute and configures to
        ignore the remaining characters of the code.

        :param idx: The index at which the code _begins_.

        :returns: True if the code is valid, False otherwise.
        """

        code = self.format[idx:idx + 3]

        if len(code) < 3 or not code.isdigit():
            return False

        self.codes.append(int(code))
        self.ignore = 2
        self.code_last = True
        return True

    def end_state(self):
        """
        Wrap things up and add any final string content.
        """

        # Make sure we append any trailing text
        if self.str_begin != len(self.format):
            if len(self.state) > 1 or self.state[-1] != 'string':
                self.fmt.append_text(
                    "(Bad format string; ended in state %r)" % self.state[-1])
            else:
                self.fmt.append_text(self.format[self.str_begin:])

        # Convenience return
        return self.fmt

    def conversion(self, idx):
        """
        Switches into the 'conversion' state, used to parse a %
        conversion.

        :param idx: The format string index at which the conversion
                    begins.
        """

        self.state.append('conversion')
        self.str_begin = idx
        self.param_begin = None
        self.conv_begin = None
        self.modifier = conversions.Modifier()
        self.codes = []
        self.reject = False
        self.code_last = False

    def escape(self, idx):
        """
        Switches into the 'escape' state, used to parse \ escapes.

        :param idx: The format string index at which the escape
                    begins.
        """

        self.state.append('escape')
        self.str_begin = idx

    def param(self, idx):
        """
        Switches into the 'param' state, used to parse parameters
        enclosed by curly braces ('{}') within conversions.

        :param idx: The format string index at which the parameter
                    name begins.
        """

        self.state.append('param')
        self.param_begin = idx

    def conv(self, idx):
        """
        Switches into the 'conv' state, used to parse conversion
        specifier names enclosed by parentheses ('()') within
        conversions.

        :param idx: The format string index at which the conversion
                    name begins.
        """

        self.state.append('conv')
        self.conv_begin = idx


class Format(object):
    _conversion_cache = {}
    _unescape = {
        '\\n': '\n',
        '\\t': '\t',
        '\\\\': '\\',
    }

    @classmethod
    def _get_conversion(cls, conv_chr, modifier):
        """
        Return a conversion given its character.

        :param conv_chr: The letter of the conversion, e.g., "a" for
                         AddressConversion, etc.
        :param modifier: The format modifier applied to this
                         conversion.

        :returns: An instance of bark.conversions.Conversion.
        """

        # Do we need to look up the conversion?
        if conv_chr not in cls._conversion_cache:
            for ep in pkg_resources.iter_entry_points('bark.conversion',
                                                      conv_chr):
                try:
                    # Load the conversion class
                    cls._conversion_cache[conv_chr] = ep.load()
                    break
                except (ImportError, pkg_resources.UnknownExtra):
                    # Couldn't load it; odd...
                    continue
            else:
                # Cache the negative result
                cls._conversion_cache[conv_chr] = None

        # Handle negative caching
        if cls._conversion_cache[conv_chr] is None:
            return conversions.StringConversion("(Unknown conversion '%%%s')" %
                                                conv_chr)

        # Instantiate the conversion
        return cls._conversion_cache[conv_chr](conv_chr, modifier)

    @classmethod
    def parse(cls, format):
        """
        Parse a format string.  Factory function for the Format class.

        :param format: The format string to parse.

        :returns: An instance of class Format.
        """

        fmt = cls()

        # Return an empty Format if format is empty
        if not format:
            return fmt

        # Initialize the state for parsing
        state = ParseState(fmt, format)

        # Loop through the format string with a state-based parser
        for idx, char in enumerate(format):
            # Some characters get ignored
            if state.check_ignore():
                continue

            if state == 'string':
                if char == '%':
                    # Handle '%%'
                    if format[idx:idx + 2] == '%%':
                        # Add one % to the string context
                        state.add_text(idx + 1, idx + 2)
                        state.set_ignore(1)
                    else:
                        state.add_text(idx)
                        state.conversion(idx)
                elif char == '\\':
                    state.add_text(idx)
                    state.escape(idx)
            elif state == 'escape':
                state.add_escape(idx + 1, char)
                state.pop_state(idx + 1)
            elif state == 'param':
                if char == '}':
                    state.set_param(idx)
                    state.pop_state()
            elif state == 'conv':
                if char == ')':
                    state.set_conversion(idx)
                    state.pop_state()  # now in 'conversion'
                    state.pop_state(idx + 1)  # now in 'string'
            else:  # state == 'conversion'
                if char in '<>':
                    # Allowed for Apache compatibility, but ignored
                    continue
                elif char == '!':
                    state.set_reject()
                    continue
                elif char == ',' and state.code_last:
                    # Syntactically allowed ','
                    continue
                elif char.isdigit():
                    # True if the code is valid
                    if state.set_code(idx):
                        continue
                elif char == '{' and state.param_begin is None:
                    state.param(idx + 1)
                    continue
                elif char == '(' and state.conv_begin is None:
                    state.conv(idx + 1)
                    continue

                # OK, we have a complete conversion
                state.set_conversion(idx)
                state.pop_state(idx + 1)

        # Finish the parse and return the completed format
        return state.end_state()

    def __init__(self):
        """
        Initialize a Format.
        """

        self.conversions = []

    def __str__(self):
        """
        Return a string representation of this format.
        """

        return ''.join(str(c) for c in self.conversions)

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
