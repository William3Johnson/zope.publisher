##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
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
"""FTP Publisher Tests
"""
import sys
from io import BytesIO
from unittest import TestCase
from unittest import TestSuite
from unittest import makeSuite

import zope.publisher.ftp


class Test(TestCase):

    def setUp(self):
        self.__input = BytesIO(b'')
        env = {'credentials': ('bob', '123'),
               'path': '/a/b/c',
               'command': 'foo',
               }
        self.__request = zope.publisher.ftp.FTPRequest(self.__input, env)

    def test_response(self):
        response = self.__request.response
        response.setResult(123.456)
        self.assertEqual(response.getResult(), 123.456)

        try:
            raise ValueError('spam')
        except:  # noqa: E722 do not use bare 'except'
            info = sys.exc_info()
            response.handleException(info)

        try:
            response.getResult()
        except:  # noqa: E722 do not use bare 'except'
            self.assertEqual(sys.exc_info()[:2], info[:2])

    def test_request(self):
        self.assertEqual(self.__request.getTraversalStack(),
                         ['c', 'b', 'a'])
        self.assertEqual(self.__request._authUserPW(),
                         ('bob', '123'))


def test_suite():
    return TestSuite((
        makeSuite(Test),
    ))
