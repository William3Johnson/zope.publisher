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
"""Tests for BaseResponse
"""

from unittest import TestCase
from unittest import TestSuite
from unittest import makeSuite

from zope.interface.verify import verifyObject

from zope.publisher.base import BaseResponse
from zope.publisher.interfaces import IResponse


class TestBaseResponse(TestCase):

    def test_interface(self):
        verifyObject(IResponse, BaseResponse())


def test_suite():
    return TestSuite((
        makeSuite(TestBaseResponse),
    ))
