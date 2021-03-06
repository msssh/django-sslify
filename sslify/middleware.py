"""Django middlewares."""


try:
    # Python 2.x
    from urlparse import urlsplit, urlunsplit
except ImportError:
    # Python 3.x
    from urllib.parse import urlsplit
    from urllib.parse import urlunsplit

from django.conf import settings
from django.http import HttpResponsePermanentRedirect

try:
    # Django 1.10
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    # Django <1.10
    class MiddlewareMixin(object):
        def __init__(self, get_response=None):
            self.get_response = get_response
            super(MiddlewareMixin, self).__init__()

        def __call__(self, request):
            response = None
            if hasattr(self, 'process_request'):
                response = self.process_request(request)
            if not response:
                response = self.get_response(request)
            if hasattr(self, 'process_response'):
                response = self.process_response(request, response)
            return response


class SSLifyMiddleware(MiddlewareMixin):
    """Force all requests to use HTTPs. If we get an HTTP request, we'll just
    force a redirect to HTTPs.

    .. note::
        You can also disable this middleware when testing by setting
        ``settings.SSLIFY_DISABLE`` to True.
    """
    @staticmethod
    def process_request(request):
        # If the user has explicitly disabled SSLify, do nothing.
        if getattr(settings, 'SSLIFY_DISABLE', False):
            return None

        # Evaluate callables that can disable SSL for the current request
        per_request_disables = getattr(settings, 'SSLIFY_DISABLE_FOR_REQUEST', [])
        for should_disable in per_request_disables:
            if should_disable(request):
                return None

        # If we get here, proceed as normal.
        if not request.is_secure():
            url = request.build_absolute_uri(request.get_full_path())
            url_split = urlsplit(url)
            scheme = 'https' if url_split.scheme == 'http' else url_split.scheme
            ssl_port = getattr(settings, 'SSLIFY_PORT', 443)
            url_secure_split = (scheme, "%s:%d" % (url_split.hostname or '', ssl_port)) + url_split[2:]
            secure_url = urlunsplit(url_secure_split)

            return HttpResponsePermanentRedirect(secure_url)
