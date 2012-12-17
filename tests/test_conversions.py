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
