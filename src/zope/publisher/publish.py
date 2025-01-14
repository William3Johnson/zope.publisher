##############################################################################
#
# Copyright (c) 2001, 2002, 2003 Zope Foundation and Contributors.
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
"""Python Object Publisher -- Publish Python objects on web servers

Provide an apply-like facility that works with any mapping object
"""
import sys

import six

from zope.interface import implementer
from zope.proxy import removeAllProxies

from zope import component
from zope.publisher.interfaces import IReRaiseException
from zope.publisher.interfaces import Retry


_marker = object()  # Create a new marker object.


def unwrapMethod(obj):
    """obj -> (unwrapped, wrapperCount)

    Unwrap 'obj' until we get to a real function, counting the number of
    unwrappings.

    Bail if we find a class or something we can't identify as callable.
    """
    wrapperCount = 0
    unwrapped = obj

    for i in range(10):
        bases = getattr(unwrapped, '__bases__', None)
        if bases is not None:
            raise TypeError("mapply() can not call class constructors")

        im_func = getattr(unwrapped, '__func__', None)
        if im_func is None:
            # Backwards compatibility with objects aimed at Python 2
            im_func = getattr(unwrapped, 'im_func', None)
        if im_func is not None:
            unwrapped = im_func
            wrapperCount += 1
        elif getattr(unwrapped, '__code__', None) is not None:
            break
        elif getattr(unwrapped, 'func_code', None) is not None:
            break
        else:
            unwrapped = getattr(unwrapped, '__call__', None)
            if unwrapped is None:
                raise TypeError("mapply() can not call %s" % repr(obj))
    else:
        raise TypeError("couldn't find callable metadata, mapply() error on %s"
                        % repr(obj))

    return unwrapped, wrapperCount


def mapply(obj, positional=(), request={}):
    __traceback_info__ = obj

    # we need deep access for introspection. Waaa.
    unwrapped = removeAllProxies(obj)

    unwrapped, wrapperCount = unwrapMethod(unwrapped)

    code = getattr(unwrapped, '__code__', None)
    if code is None:
        code = unwrapped.func_code
    defaults = getattr(unwrapped, '__defaults__', None)
    if defaults is None:
        defaults = getattr(unwrapped, 'func_defaults', None)
    names = code.co_varnames[wrapperCount:code.co_argcount]

    nargs = len(names)
    if not positional:
        args = []
    else:
        args = list(positional)
        if len(args) > nargs:
            given = len(args)
            if wrapperCount:
                given += wrapperCount
            raise TypeError('%s() takes at most %d argument%s(%d given)' % (
                getattr(unwrapped, '__name__', repr(obj)),
                code.co_argcount,
                (code.co_argcount > 1 and 's ' or ' '),
                given))

    get = request.get
    nrequired = len(names)
    if defaults:
        nrequired -= len(defaults)

    for index in range(len(args), nargs):
        name = names[index]
        v = get(name, _marker)
        if v is _marker:
            if name == 'REQUEST':
                v = request
            elif index < nrequired:
                raise TypeError('Missing argument to %s(): %s' % (
                    getattr(unwrapped, '__name__', repr(obj)), name))
            else:
                v = defaults[index - nrequired]
        args.append(v)

    args = tuple(args)

    if __debug__:
        return debug_call(obj, args)

    return obj(*args)


def debug_call(obj, args):
    # The presence of this function allows us to set a pdb breakpoint
    return obj(*args)


def publish(request, handle_errors=True):
    try:  # finally to clean up to_raise and close request
        to_raise = None
        while True:
            publication = request.publication
            try:
                try:
                    obj = None
                    try:
                        try:
                            request.processInputs()
                            publication.beforeTraversal(request)

                            obj = publication.getApplication(request)
                            obj = request.traverse(obj)
                            publication.afterTraversal(request, obj)

                            result = publication.callObject(request, obj)
                            response = request.response
                            if result is not response:
                                response.setResult(result)

                            publication.afterCall(request, obj)

                        except:  # noqa: E722 do not use bare 'except'
                            exc_info = sys.exc_info()
                            publication.handleException(
                                obj, request, exc_info, True)

                            if not handle_errors:
                                # Reraise only if there is no adapter
                                # indicating that we shouldn't
                                reraise = component.queryAdapter(
                                    exc_info[1], IReRaiseException,
                                    default=None)
                                if reraise is None or reraise():
                                    raise
                    finally:
                        exc_info = None  # Avoid circular reference.
                        publication.endRequest(request, obj)

                    break  # Successful.

                except Retry as retryException:
                    if request.supportsRetry():
                        # Create a copy of the request and use it.
                        newrequest = request.retry()
                        request.close()
                        request = newrequest
                    elif handle_errors:
                        # Output the original exception.
                        publication = request.publication
                        publication.handleException(
                            obj, request,
                            retryException.getOriginalException(), False)
                        break
                    else:
                        to_raise = retryException.getOriginalException()
                        if to_raise is None:
                            # There is no original exception inside
                            # the Retry, so just reraise it.
                            raise
                        break

            except:  # noqa: E722 do not use bare 'except'
                # Bad exception handler or retry method.
                # Re-raise after outputting the response.
                if handle_errors:
                    request.response.internalError()
                    to_raise = sys.exc_info()
                    break
                else:
                    raise

        response = request.response
        if to_raise is not None:
            six.reraise(to_raise[0], to_raise[1], to_raise[2])

    finally:
        to_raise = None  # Avoid circ. ref.
        request.close()  # Close database connections, etc.

    # Return the request, since it might be a different object than the one
    # that was passed in.
    return request


@implementer(IReRaiseException)
class DoNotReRaiseException(object):
    """Marker adapter for exceptions that should not be re-raised"""

    def __init__(self, exc):
        pass

    def __call__(self):
        return False
