##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Request Data-Property Tests
"""
from unittest import TestCase
from unittest import makeSuite

from zope.interface.common.tests.basemapping import testIEnumerableMapping
from zope.interface.common.tests.basemapping import testIReadMapping

from zope.publisher.base import RequestDataGetter
from zope.publisher.base import RequestDataMapper
from zope.publisher.base import RequestDataProperty


class TestDataGettr(RequestDataGetter):
    _gettrname = 'getSomething'


class TestDataMapper(RequestDataMapper):
    _mapname = '_data'


_marker = object()


class Data(object):

    def getSomething(self, name, default=_marker):
        if name.startswith('Z'):
            return "something %s" % name

        if default is not _marker:
            return default

        raise KeyError(name)

    something = RequestDataProperty(TestDataGettr)
    somedata = RequestDataProperty(TestDataMapper)


class Test(TestCase):

    def testRequestDataGettr(self):
        testIReadMapping(self, Data().something,
                         {"Zope": "something Zope"}, ["spam"])

    def testRequestDataMapper(self):
        data = Data()
        sample = {'foo': 'Foo', 'bar': 'Bar'}
        data._data = sample
        inst = data.somedata
        testIReadMapping(self, inst, sample, ["spam"])
        testIEnumerableMapping(self, inst, sample)

    def testNoAssign(self):
        data = Data()
        try:
            data.something = {}
        except AttributeError:
            pass
        else:
            raise AssertionError("Shouldn't be able to assign")

        try:
            data.somedata = {}
        except AttributeError:
            pass
        else:
            raise AssertionError("Shouldn't be able to assign")


def test_suite():
    return makeSuite(Test)
