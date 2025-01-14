##############################################################################
#
# Copyright (c) 2001-2009 Zope Foundation and Contributors.
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
"""Interfaces for the publisher.
"""
# BBB
from zope.browser.interfaces import IView  # noqa: F401 import unused
from zope.interface import Attribute
from zope.interface import Interface
from zope.interface import implementer
from zope.interface.common.interfaces import IException
from zope.interface.common.interfaces import ILookupError
from zope.interface.common.mapping import IEnumerableMapping
from zope.interface.interfaces import IInterface
# BBB:
from zope.security.interfaces import IParticipation
from zope.security.interfaces import Unauthorized  # noqa: F401 import unused


class IPublishingException(IException):
    """
    An exception that occurs during publication.
    """


@implementer(IPublishingException)
class PublishingException(Exception):
    """
    Default implementation of `IPublishingException`.
    """


class ITraversalException(IPublishingException):
    """
    An exception that occurs during publication traversal.
    """


@implementer(ITraversalException)
class TraversalException(PublishingException):
    """
    Default implementation of `ITraversalException`.
    """


class INotFound(ILookupError, ITraversalException):
    """
    The object we want to traverse to cannot be found.
    """

    def getObject():
        'Returns the object that was being traversed.'

    def getName():
        'Returns the name that was being traversed.'


@implementer(INotFound)
class NotFound(LookupError, TraversalException):
    """
    Default implementation of `INotFound`.
    """

    def __init__(self, ob, name, request=None):
        self.ob = ob
        self.name = name

    def getObject(self):
        return self.ob

    def getName(self):
        return self.name

    def __str__(self):
        try:
            ob = repr(self.ob)
        except:   # noqa: E722 do not use bare 'except'
            ob = 'unprintable object'
        return 'Object: %s, name: %s' % (ob, repr(self.name))


class IDebugError(ITraversalException):
    """
    A debug error.
    """
    def getObject():
        'Returns the object being traversed.'

    def getMessage():
        'Returns the debug message.'


@implementer(IDebugError)
class DebugError(TraversalException):
    """
    Default implementation of `IDebugError`.
    """

    message = None  # override this not to cause warnings in python 2.6

    def __init__(self, ob, message):
        self.ob = ob
        self.message = message

    def getObject(self):
        return self.ob

    def getMessage(self):
        return self.message

    def __str__(self):
        return self.message


class IBadRequest(IPublishingException):
    """
    The request is bad.
    """

    def __str__():
        'Returns the error message.'


@implementer(IBadRequest)
class BadRequest(PublishingException):
    """
    Default implementation of `IBadRequest`.
    """

    message = None  # override this not to cause warnings in python 2.6

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class IRedirect(IPublishingException):
    """
    An exception that redirects the client.
    """

    def getLocation():
        'Returns the location.'

    def getTrusted():
        'Returns the trusted value.'


@implementer(IRedirect)
class Redirect(PublishingException):
    """
    Default implementation of `IRedirect`.
    """

    def __init__(self, location, trusted=False):
        self.location = location
        self.trusted = trusted

    def getLocation(self):
        return self.location

    def getTrusted(self):
        return self.trusted

    def __str__(self):
        return 'Location: %s' % self.location


class IRetry(IPublishingException):
    """
    An exception that indicates a request should be retried.
    """
    def getOriginalException():
        'Returns the original exception object.'


@implementer(IRetry)
class Retry(PublishingException):
    """
    Default implementation of `IRetry`.
    """

    def __init__(self, orig_exc=None):
        """orig_exc must be a 3-tuple as returned from sys.exc_info() ...

        or None.
        """
        self.orig_exc = orig_exc

    def getOriginalException(self):
        return self.orig_exc

    def __str__(self):
        if self.orig_exc is None:
            return 'None'
        return str(self.orig_exc[1])


class IExceptionSideEffects(Interface):
    """An exception caught by the publisher is adapted to this so that
    it can have persistent side-effects."""

    def __call__(obj, request, exc_info):
        """Effect persistent side-effects.

        Arguments are:
          obj                 context-wrapped object that was published
          request             the request
          exc_info            the exception info being handled

        """


class IPublishTraverse(Interface):
    """
    Traversal for the specific purpose of publishing.
    """

    def publishTraverse(request, name):
        """Lookup a name

        The 'request' argument is the publisher request object.  The
        'name' argument is the name that is to be looked up; it must
        be an ASCII string or Unicode object.

        If a lookup is not possible, raise a NotFound error.

        This method should return an object having the specified name and
        `self` as parent. The method can use the request to determine the
        correct object.
        """


class IPublisher(Interface):
    """
    An object that can publish.
    """

    def publish(request):
        """Publish a request

        The request must be an `IPublisherRequest`.
        """


class IResponse(Interface):
    """Interface used by the publsher"""

    def setResult(result):
        """Sets the response result value.
        """

    def handleException(exc_info):
        """Handles an exception.

        This method is intended only as a convenience for the publication
        object.  The publication object can choose to handle exceptions by
        calling this method.  The publication object can also choose not
        to call this method at all.

        Implementations set the reponse body.
        """

    def internalError():
        """Called when the exception handler bombs.

        Should report back to the client that an internal error occurred.
        """

    def reset():
        """Reset the output result.

        Reset the response by nullifying already set variables.
        """

    def retry():
        """Returns a retry response

        Returns a response suitable for repeating the publication attempt.
        """


class IPublication(Interface):
    """Object publication framework.

    The responsibility of publication objects is to provide
    application hooks for the publishing process. This allows
    application-specific tasks, such as connecting to databases,
    managing transactions, and setting security contexts to be invoked
    during the publishing process.
    """
    # The order of the hooks mostly corresponds with the order in which
    # they are invoked.

    def beforeTraversal(request):
        """Pre-traversal hook.

        This is called *once* before any traversal has been done.
        """

    def getApplication(request):
        """Returns the object where traversal should commence.
        """

    def callTraversalHooks(request, ob):
        """Invokes any traversal hooks associated with the object.

        This is called before traversing each object.  The ob argument
        is the object that is about to be traversed.
        """

    def traverseName(request, ob, name):
        """Traverses to the next object.

        Name must be an ASCII string or Unicode object."""

    def afterTraversal(request, ob):
        """Post-traversal hook.

        This is called after all traversal.
        """

    def callObject(request, ob):
        """Call the object, returning the result.

        For GET/POST this means calling it, but for other methods
        (including those of WebDAV and FTP) this might mean invoking
        a method of an adapter.
        """

    def afterCall(request, ob):
        """Post-callObject hook (if it was successful).
        """

    def handleException(object, request, exc_info, retry_allowed=1):
        """Handle an exception

        Either:
        - sets the body of the response, request.response, or
        - raises a Retry exception, or
        - throws another exception, which is a Bad Thing.
        """

    def endRequest(request, ob):
        """Do any end-of-request cleanup
        """


class IPublicationRequest(IParticipation):
    """Interface provided by requests to `IPublication` objects
    """

    response = Attribute("""The request's response object

        Return an IPublisherResponse for the request.
        """)

    def close():
        """Release resources held by the request.
        """

    def hold(held):
        """Hold a reference to an object until the request is closed.

        The object should be an IHeld.  If it is an IHeld, its
        release method will be called when it is released.
        """

    def getTraversalStack():
        """Return the request traversal stack

        This is a sequence of steps to traverse in reverse order. They
        will be traversed from last to first.
        """

    def setTraversalStack(stack):
        """Change the traversal stack.

        See getTraversalStack.
        """

    def getPositionalArguments():
        """Return the positional arguments given to the request.
        """

    def setPrincipal(principal):
        """Set the principal attribute.

        It should be IPrincipal wrapped in its AuthenticationService's context.
        """


class IHeld(Interface):
    """Object to be held and explicitly released by a request
    """

    def release():
        """Release the held object

        This is called by a request that holds the IHeld when the
        request is closed

        """


class IPublisherRequest(IPublicationRequest):
    """Request interface use by the publisher

    The responsibility of requests is to encapsulate protocol
    specific details, especially wrt request inputs.

    Request objects also serve as "context" objects, providing
    construction of and access to responses and storage of publication
    objects.
    """

    def supportsRetry():
        """Check whether the request supports retry

        Return a boolean value indicating whether the request can be retried.
        """

    def retry():
        """Return a retry request

        Return a request suitable for repeating the publication attempt.
        """

    publication = Attribute("""The request's publication object

        The publication object, an IRequestPublication provides
        application-specific functionality hooks.
        """)

    def setPublication(publication):
        """Set the request's publication object
        """

    def traverse(obj):
        """Traverse from the given object to the published object

        The published object is returned.

        The following hook methods on the publication will be called:

          - callTraversalHooks is called before each step and after
            the last step.

          - traverseName to actually do a single traversal

        """

    def processInputs():
        """Do any input processing that needs to be done before traversing

        This is done after construction to allow the publisher to
        handle errors that arise.
        """


class IDebugFlags(Interface):
    """Features that support debugging."""

    sourceAnnotations = Attribute("""Enable ZPT source annotations""")
    showTAL = Attribute("""Leave TAL markup in rendered page templates""")


class IApplicationRequest(IEnumerableMapping):
    """Features that support application logic
    """

    principal = Attribute("""Principal object associated with the request
                             This is a read-only attribute.
                          """)

    bodyStream = Attribute(
        """The stream that provides the data of the request.

        The data returned by the stream will not include any possible header
        information, which should have been stripped by the server (or
        previous layer) before.

        Also, the body stream might already be read and not return any
        data. This is commonly done when retrieving the data for the ``body``
        attribute.

        If you access this stream directly to retrieve data, it will not be
        possible by other parts of the framework to access the data of the
        request via the ``body`` attribute.""")

    debug = Attribute("""Debug flags (see IDebugFlags).""")

    def __getitem__(key):
        """Return request data

        The only request data are environment variables.
        """

    environment = Attribute(
        """Request environment data

        This is a read-only mapping from variable name to value.
        """)

    annotations = Attribute(
        """Stores arbitrary application data under package-unique keys.

        By "package-unique keys", we mean keys that are are unique by
        virtue of including the dotted name of a package as a prefex.  A
        package name is used to limit the authority for picking names for
        a package to the people using that package.

        For example, when implementing annotations for hypothetical
        request-persistent adapters in a hypothetical zope.persistentadapter
        package, the key would be (or at least begin with) the following::

          "zope.persistentadapter"
        """)


class IRequest(IPublisherRequest, IPublicationRequest, IApplicationRequest):
    """The basic request contract
    """


class IRequestEvent(Interface):
    """An event which is about or for a request."""

    request = Attribute("The request this event is about.")


class IEndRequestEvent(IRequestEvent):
    """An event which gets sent when the publication is ended."""


class IStartRequestEvent(IRequestEvent):
    """An event which gets sent before publication of a request."""


class RequestEvent(object):
    """Events for requests.

    :param request: The request the event is for.
    """

    def __init__(self, request):
        self.request = request


@implementer(IEndRequestEvent)
class EndRequestEvent(RequestEvent):
    """An event which gets sent when the publication is ended"""

    def __init__(self, ob, request):
        super(EndRequestEvent, self).__init__(request)
        self.object = ob


@implementer(IStartRequestEvent)
class StartRequestEvent(RequestEvent):
    """An event send when before publication of a request."""


class ISkinType(IInterface):
    """Base interface for skin types."""


class ISkinnable(Interface):
    """A skinnable (request) can provide a skin.

    The implementation in BrowserRequest will apply a default skin/layer called
    ``IDefaultBrowserLayer`` if not default skin get registered.
    """


class IDefaultSkin(Interface):
    """Any component providing this interface must be a skin.

    This is a marker interface, so that we can register the default skin as an
    adapter from the presentation type to `IDefaultSkin`.
    """


class ISkinChangedEvent(IRequestEvent):
    """Event that gets triggered when the skin of a request is changed."""


class IDefaultViewName(Interface):
    """A string that contains the default view name

    A default view name is used to select a view when a user hasn't
    specified one.
    """


class IReRaiseException(Interface):
    """An exception that should be reraised, when handled in publisher.

    Under some circumstances (for instance if acting in a WSGI
    pipeline with debugger middleware) certain exceptions occuring
    while publishing should be handled by the Zope machinery and never
    reach the 'outside world'.

    Adapters providing this interface for a certain exception type
    which also return ``False`` when being called, indicate by this
    that the exception should not be reraised during publishing.

    This makes it possible, for instance, to authenticate with
    basic-auth when a debugger middleware is used and `IUnauthorized`
    is raised.
    """

    def __call__():
        """Return True if an exception should be re-raised"""
